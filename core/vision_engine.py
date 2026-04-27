"""
Vision-Driven GUI Automation Engine

Drop-in replacement for GUIEngine. Uses Claude Vision to identify UI elements
on the live screen — works regardless of resolution, theme, or UI variations.

Falls back through a chain when the primary path is unavailable:
    1. Claude Vision API  (primary — semantic recognition)
    2. pywinauto UIA      (if Housoft exposes accessibility tree)
    3. Template matching  (final fallback — uses templates/*.png)

Public interface mirrors GUIEngine exactly so the orchestrator and click
sequences need no changes. To switch over:

    # main.py
    # from core.gui_engine import GUIEngine
    from core.vision_engine import VisionGUIEngine as GUIEngine
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pyautogui
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True


# ─────────────────────────────────────────────────────────────────────────────
# Element descriptions — semantic descriptions Claude uses to find each element.
# Keys match the template names used elsewhere in the project, so existing
# click sequences ("btn_parar", "btn_ok", etc.) work unchanged.
# ─────────────────────────────────────────────────────────────────────────────
ELEMENT_DESCRIPTIONS: dict[str, str] = {
    # Task control buttons (top toolbar of running task)
    "btn_parar":     "The red 'Parar' (Stop) button in the top toolbar — red diamond icon with 'Parar' text below.",
    "btn_pausa":     "The blue 'Pausa' (Pause) button in the top toolbar — blue || (pause) icon with 'Pausa' text below.",
    "btn_continuar": "The blue 'Cont.' (Continue) button in the top toolbar — blue right-arrow icon with 'Cont.' text below. Replaces Pausa when paused.",

    # Module dialog buttons
    "btn_ok":        "The green 'Ok' button at the bottom of a Housoft module dialog — green diamond icon with 'Ok' text.",
    "btn_ajuda":     "The blue 'Ajuda' (Help) button at the bottom of a Housoft module dialog — blue help-bubble icon with 'Ajuda' text.",
    "btn_cancelar":  "The red 'Cancelar' (Cancel) button at the bottom of a Housoft module dialog — red diamond icon with 'Cancelar' text.",

    # Dialog tabs
    "tab_criterio":  "The 'Critério' tab at the top of a module dialog (selects targeting criteria).",
    "tab_conteudo":  "The 'Conteúdo' tab at the top of a module dialog (selects content to post/send).",
    "tab_opcoes":    "The 'Opções' tab at the top of a module dialog (timing and rotation settings).",
    "tab_filtros":   "The 'Filtros' tab at the top of a module dialog (filtering rules).",

    # Title bars (used to verify which app is in focus)
    "titlebar_face":  "The 'Housoft Face' title bar text at the top of the Housoft Face window.",
    "titlebar_insta": "The 'Housoft Insta' title bar text at the top of the Housoft Instagram window.",

    # Facebook module buttons (top toolbar of Housoft Face main window)
    "module_postar_em_grupos":   "The 'Postar em grupos' module button in the Housoft Face top toolbar.",
    "module_postar_no_mural":    "The 'Postar no mural' module button in the Housoft Face top toolbar.",
    "module_enviar_mensagem":    "The 'Enviar mensagem' module button in the Housoft Face top toolbar.",
    "module_adicionar_amigos":   "The 'Adicionar amigos' module button in the Housoft Face top toolbar.",
    "module_paginas_eventos":    "The 'Páginas e eventos' module button in the Housoft Face top toolbar.",
    "module_login_loop":         "The 'Login loop' module button in the Housoft Face top toolbar.",
    "module_postar_marketplace": "The 'Postar no marketplace' module button in the Housoft Face top toolbar.",
    "module_entrar_em_grupos":   "The 'Entrar em grupos' module button in the Housoft Face top toolbar.",
    "module_responder_mensagem": "The 'Responder mensagem' module button in the Housoft Face top toolbar.",
    "module_curtir":             "The 'Curtir' module button in the Housoft Face top toolbar.",
    "module_compartilhar":       "The 'Compartilhar' module button in the Housoft Face top toolbar.",
    "module_criar_lista":        "The 'Criar lista' module button in the Housoft Face top toolbar.",
    "module_configurar":         "The 'Configurar' (Configure) button on the right of the toolbar.",

    # Instagram module buttons
    "module_enviar_direct":      "The 'Enviar direct' module button in the Housoft Insta top toolbar — envelope icon.",

    # Popups (state detection & dismissal)
    "popup_error":      "An error popup dialog (red icon, error message).",
    "popup_blocked":    "An 'account blocked' popup from Facebook/Instagram saying the account was restricted.",
    "popup_alert":      "A generic alert/warning popup dialog.",
    "popup_ok_btn":     "The 'OK', 'Confirmar', or 'Continuar' button on a popup dialog.",
    "popup_close_btn":  "The close (X) button in the title bar of a popup dialog.",

    # State indicators
    "status_running":   "Indicator that a task is currently running (active/green status).",
    "status_stopped":   "Indicator that the task is stopped or idle.",
    "status_error":     "Indicator that the task is in an error state.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models for Claude responses
# ─────────────────────────────────────────────────────────────────────────────
class _ElementHit(BaseModel):
    found: bool
    x: int = 0
    y: int = 0
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reason: str = ""


class _StateCheck(BaseModel):
    matches: bool
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    observed: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Vision Resolver — wraps Claude API with caching
# ─────────────────────────────────────────────────────────────────────────────
_VISION_SYSTEM = (
    "You are a pixel-perfect GUI automation engine driving an automated mouse. "
    "Given a screenshot, identify the EXACT center pixel coordinates of UI elements. "
    "Coordinates are in screen pixels with (0,0) at top-left. "
    "Return the click center, not corners. A 5-pixel error can miss a small button.\n\n"
    "If the element is not visible, set found=false and explain in 'reason'. "
    "confidence: 1.0 = certain, 0.5 = visible but ambiguous, < 0.3 = uncertain guess.\n\n"
    "Always reply with valid JSON only — no markdown fences, no commentary."
)


class VisionResolver:
    """Wraps Claude Vision API. Caches identical-screenshot lookups."""

    def __init__(self, model: str = "claude-opus-4-7"):
        try:
            import anthropic
            self.client = anthropic.Anthropic()
            self.available = True
        except Exception as e:
            logger.warning(f"Anthropic client unavailable: {e}")
            self.client = None
            self.available = False
        self.model = model
        # Cache: (screenshot_hash, element_name) -> (x, y, confidence)
        self._cache: dict[tuple[str, str], tuple[int, int, float]] = {}

    @staticmethod
    def _hash_image(img: np.ndarray) -> str:
        # Downsample to 64x64 for hash stability against tiny pixel noise
        small = cv2.resize(img, (64, 64))
        return hashlib.md5(small.tobytes()).hexdigest()

    @staticmethod
    def _encode_image(img: np.ndarray) -> str:
        ok, buf = cv2.imencode(".png", img)
        if not ok:
            raise RuntimeError("Failed to encode screenshot")
        return base64.standard_b64encode(buf.tobytes()).decode()

    def find(self, screenshot: np.ndarray, element_name: str) -> Optional[tuple[int, int, float]]:
        """Returns (x, y, confidence) or None."""
        if not self.available:
            return None

        description = ELEMENT_DESCRIPTIONS.get(element_name, element_name)
        h, w = screenshot.shape[:2]
        cache_key = (self._hash_image(screenshot), element_name)

        if cache_key in self._cache:
            x, y, conf = self._cache[cache_key]
            logger.debug(f"VisionResolver cache hit: {element_name} -> ({x},{y})")
            return (x, y, conf)

        prompt = (
            f"Screenshot is exactly {w}x{h} pixels.\n"
            f"Find this element and return its CENTER pixel coordinates:\n\n"
            f"  {description}\n\n"
            f"Reply with JSON: "
            f'{{"found": bool, "x": int, "y": int, "confidence": float, "reason": str}}'
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=[{
                    "type": "text",
                    "text": _VISION_SYSTEM,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": self._encode_image(screenshot),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
        except Exception as e:
            logger.error(f"Vision API call failed for '{element_name}': {e}")
            return None

        text = next(b.text for b in response.content if b.type == "text").strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            hit = _ElementHit.model_validate_json(text)
        except Exception as e:
            logger.error(f"Failed to parse Vision response for '{element_name}': {e}\n{text[:200]}")
            return None

        if not hit.found or hit.confidence < 0.3:
            logger.info(f"Vision: '{element_name}' not found (conf={hit.confidence:.2f}, {hit.reason})")
            return None

        result = (hit.x, hit.y, hit.confidence)
        self._cache[cache_key] = result
        logger.info(f"Vision: '{element_name}' at ({hit.x},{hit.y}) conf={hit.confidence:.2f}")
        return result

    def verify_state(self, screenshot: np.ndarray, expected: str) -> bool:
        """Ask Claude whether the screenshot shows the expected state."""
        if not self.available:
            return True  # No verification when Vision unavailable

        prompt = (
            f"Does this screenshot match the following expected UI state?\n\n"
            f"  {expected}\n\n"
            f'Reply JSON: {{"matches": bool, "confidence": float, "observed": str}}'
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                system=[{
                    "type": "text",
                    "text": _VISION_SYSTEM,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": self._encode_image(screenshot),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
        except Exception as e:
            logger.error(f"verify_state failed: {e}")
            return True

        text = next(b.text for b in response.content if b.type == "text").strip()
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        try:
            check = _StateCheck.model_validate_json(text)
            logger.info(f"State check: {expected} -> matches={check.matches} ({check.observed})")
            return check.matches and check.confidence >= 0.5
        except Exception as e:
            logger.error(f"Failed to parse verify_state response: {e}")
            return True


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: classic template matching (uses files in templates/)
# ─────────────────────────────────────────────────────────────────────────────
_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _template_find(screenshot: np.ndarray, name: str, confidence: float) -> Optional[tuple[int, int, float]]:
    path = _TEMPLATES_DIR / f"{name}.png"
    if not path.exists():
        return None
    template = cv2.imread(str(path))
    if template is None:
        return None
    if template.shape[0] > screenshot.shape[0] or template.shape[1] > screenshot.shape[1]:
        return None
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < confidence:
        return None
    h, w = template.shape[:2]
    return (max_loc[0] + w // 2, max_loc[1] + h // 2, max_val)


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: pywinauto by accessibility name
# ─────────────────────────────────────────────────────────────────────────────
_PYWINAUTO_NAME_MAP = {
    "btn_ok": "Ok",
    "btn_ajuda": "Ajuda",
    "btn_cancelar": "Cancelar",
    "btn_parar": "Parar",
    "btn_pausa": "Pausa",
    "btn_continuar": "Cont.",
    "popup_ok_btn": "OK",
    "popup_close_btn": "Close",
}


def _pywinauto_find(window, element_name: str) -> Optional[tuple[int, int, float]]:
    accessible_name = _PYWINAUTO_NAME_MAP.get(element_name)
    if not accessible_name or window is None:
        return None
    try:
        ctrl = window.child_window(title=accessible_name, control_type="Button")
        if not ctrl.exists():
            return None
        rect = ctrl.rectangle()
        return ((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2, 1.0)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Vision-driven GUI engine
# ─────────────────────────────────────────────────────────────────────────────
class VisionGUIEngine:
    """Drop-in replacement for GUIEngine, Vision-first with fallbacks."""

    TEMPLATES_DIR = _TEMPLATES_DIR

    def __init__(self, vision_model: str = "claude-opus-4-7", enable_verification: bool = True):
        self.current_app: Optional[str] = None
        self.current_module: Optional[str] = None
        self.is_task_running: bool = False
        self._window_cache: dict[str, object] = {}
        self.vision = VisionResolver(model=vision_model)
        self.enable_verification = enable_verification
        logger.info(
            f"VisionGUIEngine initialized (vision_available={self.vision.available}, "
            f"verification={enable_verification})"
        )

    # ─── Window Management ───────────────────────────────────

    def find_window(self, app_name: str):
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            search_term = "Housoft Face" if app_name == "face" else "Housoft Insta"
            for win in desktop.windows():
                if search_term.lower() in win.window_text().lower():
                    self._window_cache[app_name] = win
                    return win
            logger.warning(f"Window not found for: {search_term}")
            return None
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            return None

    def bring_to_front(self, app_name: str) -> bool:
        window = self.find_window(app_name)
        if not window:
            return False
        try:
            window.set_focus()
            time.sleep(0.5)
            self.current_app = app_name
            return True
        except Exception as e:
            logger.error(f"Error bringing window to front: {e}")
            return False

    # ─── Screen capture ──────────────────────────────────────

    def take_screenshot(self) -> np.ndarray:
        return cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)

    # ─── Element resolution (the fallback chain) ─────────────

    def find_element(self, template_name: str, confidence: float = 0.7) -> Optional[tuple[int, int]]:
        """Find an element using the fallback chain. Returns (x, y) or None."""
        screenshot = self.take_screenshot()

        # 1. Vision API
        hit = self.vision.find(screenshot, template_name)
        if hit:
            return (hit[0], hit[1])

        # 2. pywinauto by accessibility name
        if self.current_app and self.current_app in self._window_cache:
            hit = _pywinauto_find(self._window_cache[self.current_app], template_name)
            if hit:
                logger.info(f"pywinauto found '{template_name}' at ({hit[0]},{hit[1]})")
                return (hit[0], hit[1])

        # 3. Classic template matching
        hit = _template_find(screenshot, template_name, confidence)
        if hit:
            logger.info(f"Template matched '{template_name}' at ({hit[0]},{hit[1]}) conf={hit[2]:.2f}")
            return (hit[0], hit[1])

        logger.warning(f"All resolvers failed for '{template_name}'")
        return None

    # ─── Click actions ───────────────────────────────────────

    def click_element(self, template_name: str, confidence: float = 0.7, retries: int = 3) -> bool:
        for attempt in range(retries):
            pos = self.find_element(template_name, confidence)
            if pos:
                ox = random.randint(-3, 3)
                oy = random.randint(-3, 3)
                pyautogui.click(pos[0] + ox, pos[1] + oy)
                time.sleep(random.uniform(0.3, 0.8))
                logger.info(f"Clicked '{template_name}' at {pos}")
                return True
            if attempt < retries - 1:
                logger.info(f"Retry {attempt + 1}/{retries} for '{template_name}'")
                time.sleep(1)
        logger.error(f"Failed to click '{template_name}' after {retries} attempts")
        return False

    def click_position(self, x: int, y: int) -> None:
        ox = random.randint(-2, 2)
        oy = random.randint(-2, 2)
        pyautogui.click(x + ox, y + oy)
        time.sleep(random.uniform(0.3, 0.7))

    # ─── Sequence execution ──────────────────────────────────

    def execute_sequence(self, sequence: list, context: dict | None = None) -> bool:
        context = context or {}
        for i, step in enumerate(sequence):
            step_type = step.get("type")
            label = step.get("label", f"Step {i+1}")
            logger.info(f"  [{i+1}/{len(sequence)}] {label}")

            if step_type == "click":
                if not self.click_element(step["template"]):
                    logger.error(f"Step failed: {label}")
                    return False
            elif step_type == "click_xy":
                self.click_position(step["x"], step["y"])
            elif step_type == "wait":
                time.sleep(step.get("seconds", 1.0) * random.uniform(0.9, 1.2))
            elif step_type == "verify":
                if not self.find_element(step["template"]):
                    logger.error(f"Verify failed: {step['template']} not found")
                    return False
            else:
                logger.warning(f"Unknown step type: {step_type}")
        return True

    # ─── Task orchestration ──────────────────────────────────

    def start_task(self, app_name: str, module_name: str) -> bool:
        from core.click_sequences import get_start_sequence

        if not self.bring_to_front(app_name):
            return False
        time.sleep(random.uniform(0.5, 1.0))

        sequence = get_start_sequence(module_name)
        if not sequence or not self.execute_sequence(sequence):
            return False

        self.current_module = module_name
        self.is_task_running = True

        if self.enable_verification:
            time.sleep(1.5)
            ok = self.vision.verify_state(
                self.take_screenshot(),
                f"A Housoft {app_name} task is currently running. The Parar (red) and Pausa (blue) "
                f"buttons should be visible at the top toolbar, indicating the task is active.",
            )
            if not ok:
                logger.warning(f"State verification failed after starting {module_name}")
                # Don't fail hard — the task may have started but visual cue differs
        return True

    def stop_task(self) -> bool:
        from core.click_sequences import get_stop_sequence

        if not self.is_task_running:
            return True

        sequence = get_stop_sequence(self.current_module)
        if not self.execute_sequence(sequence):
            return False

        self.is_task_running = False
        self.current_module = None
        return True

    def switch_task(self, app_name: str, module_name: str) -> bool:
        if self.is_task_running:
            if not self.stop_task():
                return False
            time.sleep(random.uniform(2.0, 4.0))
        return self.start_task(app_name, module_name)

    # ─── Popup handling ──────────────────────────────────────

    def detect_popup(self) -> Optional[str]:
        for popup in ("popup_error", "popup_blocked", "popup_alert"):
            if self.find_element(popup):
                logger.warning(f"Popup detected: {popup}")
                return popup
        return None

    def dismiss_popup(self) -> bool:
        if not self.detect_popup():
            return False
        if self.click_element("popup_ok_btn"):
            return True
        if self.click_element("popup_close_btn"):
            return True
        return False

    def check_task_status(self) -> str:
        if self.find_element("status_running"):
            return "running"
        if self.find_element("status_stopped"):
            return "stopped"
        if self.find_element("status_error"):
            return "error"
        return "unknown"

    # ─── Utility ─────────────────────────────────────────────

    def human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0) -> None:
        time.sleep(random.uniform(min_sec, max_sec))

    def capture_template(self, name: str, region=None):
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        save_path = self.TEMPLATES_DIR / f"{name}.png"
        screenshot.save(str(save_path))
        return save_path
