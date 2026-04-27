"""
Proof-of-concept: Claude Vision as the primary GUI element resolver for Housoft.

Goal: Prove that Claude can accurately identify pixel coordinates of Housoft UI
elements across DIFFERENT screen resolutions, eliminating the need for
resolution-specific template images.

Run:
    set ANTHROPIC_API_KEY=sk-ant-...
    python poc_vision_resolver.py

Outputs annotated images to 0424/_poc_annotated/ — open them to verify Claude
clicked the right pixels.
"""
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import anthropic
import cv2
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load ANTHROPIC_API_KEY from housoft-meta/.env
load_dotenv(Path(__file__).parent / ".env")

ROOT = Path(__file__).parent.parent
SOURCES_DIR = ROOT / "0424"
OUTPUT_DIR = SOURCES_DIR / "_poc_annotated"
OUTPUT_DIR.mkdir(exist_ok=True)


class Element(BaseModel):
    name: str = Field(description="The element label, e.g. 'btn_parar'")
    x: int = Field(description="Center X pixel coordinate")
    y: int = Field(description="Center Y pixel coordinate")
    confidence: float = Field(ge=0, le=1)
    found: bool = Field(description="False if the element is not present in the image")


class VisionResult(BaseModel):
    image_resolution: str
    elements: list[Element]


VISION_SYSTEM_PROMPT = """You are a pixel-perfect GUI automation engine.

Given a screenshot of a Housoft application, identify the EXACT center pixel
coordinates of UI elements requested. You must respond with valid JSON only.

Rules:
1. Use the actual pixel dimensions of the image — count from (0,0) at top-left.
2. Return the CENTER of each clickable element, not the corner.
3. If an element is not visible, set found=false and use 0 for coordinates.
4. Be precise — these coordinates drive automated mouse clicks. A 5px error
   could miss the button entirely.
5. confidence: 1.0 = certain, 0.5 = visible but ambiguous, < 0.3 = guess.

Housoft button conventions you must know:
- "Parar" = red diamond icon with text below
- "Pausa" = blue || (pause) icon with text below
- "Cont." (Continuar) = blue arrow icon with text below — replaces Pausa when paused
- "Ok" = green checkmark/diamond icon with "Ok" text
- "Ajuda" = blue help-bubble icon with "Ajuda" text
- "Cancelar" = red diamond icon with "Cancelar" text
- Tabs: text labels at top of dialog (Conteudos, Opcoes, Filtros, etc.)
- Module buttons: small icons with descriptive text in the top toolbar"""


class VisionResolver:
    def __init__(self, model: str = "claude-opus-4-7"):
        self.client = anthropic.Anthropic()
        self.model = model

    def resolve(self, image_path: Path, elements_to_find: list[str]) -> VisionResult:
        image_bytes = image_path.read_bytes()
        media_type = "image/jpeg" if image_path.suffix.lower() in (".jpg", ".jpeg") else "image/png"
        img_b64 = base64.standard_b64encode(image_bytes).decode()

        # Read actual image dimensions to give Claude the ground truth
        img = cv2.imread(str(image_path))
        h, w = img.shape[:2]

        user_prompt = (
            f"This screenshot is exactly {w}x{h} pixels. "
            f"Find the center pixel coordinates of the following elements:\n\n"
            + "\n".join(f"- {e}" for e in elements_to_find)
            + "\n\nReturn JSON matching this schema:\n"
            + json.dumps(VisionResult.model_json_schema(), indent=2)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": VISION_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )

        # Extract JSON from response
        text = next(b.text for b in response.content if b.type == "text")
        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        return VisionResult.model_validate_json(text)


def annotate(image_path: Path, result: VisionResult, ground_truth: Optional[dict] = None) -> Path:
    """Draw markers on the image at predicted coordinates. Optionally compare to ground truth."""
    img = cv2.imread(str(image_path))
    for el in result.elements:
        if not el.found:
            continue
        color = (0, 255, 0) if el.confidence >= 0.8 else (0, 165, 255)
        cv2.circle(img, (el.x, el.y), 12, color, 2)
        cv2.putText(
            img, f"{el.name} ({el.confidence:.2f})",
            (el.x + 15, el.y - 5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1
        )
        # If ground truth provided, draw expected position in red
        if ground_truth and el.name in ground_truth:
            gx, gy = ground_truth[el.name]
            cv2.circle(img, (gx, gy), 8, (0, 0, 255), 2)
            cv2.line(img, (el.x, el.y), (gx, gy), (255, 0, 255), 1)

    out_path = OUTPUT_DIR / f"poc_{image_path.stem}.png"
    cv2.imwrite(str(out_path), img)
    return out_path


def run_test(resolver: VisionResolver, image_rel: str, elements: list[str], ground_truth: Optional[dict] = None):
    image_path = SOURCES_DIR / image_rel
    if not image_path.exists():
        print(f"SKIP: {image_path}")
        return

    print(f"\n{'='*70}")
    print(f"TEST: {image_rel}")
    print(f"  Looking for: {', '.join(elements)}")

    try:
        result = resolver.resolve(image_path, elements)
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    print(f"  Image: {result.image_resolution}")
    print(f"  Found:")
    for el in result.elements:
        gt_str = ""
        if ground_truth and el.name in ground_truth and el.found:
            gx, gy = ground_truth[el.name]
            err = ((el.x - gx) ** 2 + (el.y - gy) ** 2) ** 0.5
            gt_str = f"  (expected ({gx},{gy}), error={err:.0f}px)"
        status = "[OK]" if el.found else "[MISS]"
        print(f"    {status} {el.name:<20} ({el.x:4d},{el.y:4d}) conf={el.confidence:.2f}{gt_str}")

    out = annotate(image_path, result, ground_truth)
    print(f"  Annotated: {out}")


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print("  Run: python set_api_key.py")
        print("  (or set ANTHROPIC_API_KEY environment variable manually)")
        sys.exit(1)

    resolver = VisionResolver()

    # Test 1: 1024x768 main window — find module buttons
    run_test(
        resolver,
        "photo_2026-04-24_13-19-13.jpg",
        ["Postar em grupos button", "Postar no mural button",
         "Enviar mensagem button", "Login loop button",
         "Configurar button", "Housoft logo"],
    )

    # Test 2: 610x696 dialog — find Ok/Ajuda/Cancelar + tabs
    # Ground truth from earlier extraction (center pixels)
    gt_dialog = {
        "Ok button": (52, 662),
        "Ajuda button": (154, 662),
        "Cancelar button": (247, 662),
        "Conteudos tab": (44, 36),
        "Opcoes tab": (115, 36),
        "Filtros tab": (163, 36),
    }
    run_test(
        resolver,
        "photo_2026-04-24_13-19-18.jpg",
        list(gt_dialog.keys()),
        gt_dialog,
    )

    # Test 3: 1280x720 running task — find Parar/Pausa
    gt_running = {
        "Parar button": (910, 50),
        "Pausa button": (970, 50),
    }
    run_test(
        resolver,
        "frames/frame_062_t0060.4s.png",
        list(gt_running.keys()),
        gt_running,
    )

    # Test 4: 1280x720 paused state — find Parar/Cont.
    gt_paused = {
        "Parar button": (910, 50),
        "Continuar button (labeled Cont.)": (970, 50),
    }
    run_test(
        resolver,
        "frames/frame_185_t0180.3s.png",
        list(gt_paused.keys()),
        gt_paused,
    )

    print(f"\n{'='*70}")
    print(f"Done. Inspect annotated images in: {OUTPUT_DIR}")
    print("Green circle = high-confidence prediction")
    print("Orange circle = low-confidence prediction")
    print("Red circle = ground truth (expected position)")
    print("Magenta line = error vector")


if __name__ == "__main__":
    main()
