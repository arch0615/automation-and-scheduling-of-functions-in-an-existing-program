"""
Click Sequence Definitions for Housoft Modules
Each module has a defined click path: template name, wait time, optional params.

These sequences are derived from the client videos showing the Housoft UI
at 1024x768 resolution. Coordinates are relative to the Housoft window.

Sequence step types:
  - click:   click a template by name
  - click_xy: click at absolute (x, y) coords (fallback when no template)
  - wait:    sleep for N seconds
  - type:    type text into a focused field
  - select:  click a dropdown, then select an option
  - check:   set a checkbox (click if not already checked)
  - tab:     switch to a tab in the module dialog
  - verify:  verify a template is present (fail if not)
"""

# ─── Module menu button positions (confirmed via template matching) ─────────
MODULE_POSITIONS = {
    "postar_em_grupos":   (52, 54),
    "postar_no_mural":    (147, 54),
    "enviar_mensagem":    (237, 54),
    "adicionar_amigos":   (327, 54),
    "paginas_eventos":    (420, 54),
    "login_loop":         (507, 54),
    "postar_marketplace": (57, 96),
    "entrar_em_grupos":   (155, 96),
    "responder_mensagem": (250, 96),
    "curtir":             (340, 96),
    "compartilhar":       (425, 96),
    "criar_lista":        (512, 96),
}

# ─── Common sequences ────────────────────────────────────────────────────────

# Start any module: click the module button, wait for dialog, click OK
def start_module_sequence(module_key):
    pos = MODULE_POSITIONS[module_key]
    return [
        {"type": "click_xy", "x": pos[0], "y": pos[1], "label": f"Open {module_key}"},
        {"type": "wait", "seconds": 1.0, "label": "Wait for dialog to open"},
        {"type": "click", "template": "btn_ok", "label": "Click OK to start task"},
        {"type": "wait", "seconds": 2.0, "label": "Wait for task to start"},
    ]


# Start a module whose dialog has an inline 'Pesquisar' button that must be
# clicked to load/validate the saved content (e.g. a page link) before the
# footer Ok will accept the form. The text field is left at whatever Housoft
# remembered from Valesca's last session.
# Reported by Miguel for paginas_eventos / "Promover página" — 2026-05-18.
def start_search_then_ok_sequence(module_key):
    pos = MODULE_POSITIONS[module_key]
    return [
        {"type": "click_xy", "x": pos[0], "y": pos[1], "label": f"Open {module_key}"},
        {"type": "wait", "seconds": 1.5, "label": "Wait for dialog to open"},
        {"type": "click", "template": "btn_pesquisar_inline",
         "label": "Click inline Pesquisar to load the saved page/link"},
        {"type": "wait", "seconds": 4.0, "label": "Wait for page to load in dialog"},
        {"type": "click", "template": "btn_ok",
         "label": "Click footer OK to commit and start task"},
        {"type": "wait", "seconds": 2.0, "label": "Wait for task to start"},
    ]


# Start a module that opens a search dialog (Pesquisar) before the module runs.
# The dialog REQUIRES a search term — clicking Ok with the field empty leaves
# the bot stuck on this screen (reported by Miguel, 2026-05-12).
def start_search_module_sequence(module_key, search_term):
    pos = MODULE_POSITIONS[module_key]
    return [
        {"type": "click_xy", "x": pos[0], "y": pos[1], "label": f"Open {module_key}"},
        {"type": "wait", "seconds": 1.5, "label": "Wait for Pesquisar dialog to open"},
        {"type": "type", "template": "search_input", "text": search_term,
         "press_enter": True, "clear_first": True,
         "label": f"Type search term and submit: {search_term!r}"},
        {"type": "wait", "seconds": 3.5, "label": "Wait for search results to populate"},
        {"type": "click", "template": "btn_ok", "label": "Click OK to commit search & start task"},
        {"type": "wait", "seconds": 2.0, "label": "Wait for task to start"},
    ]


# Stop current task: click Parar button at top
STOP_SEQUENCE = [
    {"type": "click", "template": "btn_parar", "label": "Click Parar to stop task"},
    {"type": "wait", "seconds": 2.0, "label": "Wait for task to stop"},
]


# ─── Module-specific configurations ───────────────────────────────────────────
# Each module has pre-configured settings that Valesca saved.
# The meta-automation system just starts/stops — doesn't reconfigure each time.
# But we record the CATEGORY tab navigation in case we need to set targeting mode.

MODULE_SEQUENCES = {
    # ═══ Facebook Modules ═══════════════════════════════════════════════════

    "postar_em_grupos": {
        "display_name": "Postar em Grupos",
        "description": "Post content in Facebook groups (discussion/sale/marketplace)",
        "tabs": ["Conteudo", "Opcoes", "Filtros"],
        "start_sequence": start_module_sequence("postar_em_grupos"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"location_filter": "nearby"},
            "national": {"location_filter": "all_brazil"},
        },
    },

    "postar_no_mural": {
        "display_name": "Postar no Mural",
        "description": "Post on friends' walls or timeline",
        "tabs": ["Criterio", "Conteudo", "Opcoes", "Filtros"],
        "start_sequence": start_module_sequence("postar_no_mural"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"criterio": "friends_nearby"},
            "national": {"criterio": "all_friends"},
        },
    },

    "enviar_mensagem": {
        "display_name": "Enviar Mensagem",
        "description": "Send direct messages to friends / group members / page likers",
        "tabs": ["Principal", "Opcoes", "Filtro"],
        "start_sequence": start_module_sequence("enviar_mensagem"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"criterio": "pesquisar_meus_amigos"},
            "national": {"criterio": "pesquisar_paginas"},
        },
    },

    "adicionar_amigos": {
        "display_name": "Adicionar Amigos",
        "description": "Add friends from groups / other profiles / page likers",
        "tabs": ["Criterio", "Opcoes"],
        "start_sequence": start_module_sequence("adicionar_amigos"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"criterio": "participantes_grupo_local"},
            "national": {"criterio": "curtidores_pagina"},
        },
    },

    "paginas_eventos": {
        "display_name": "Paginas e Eventos",
        "description": "Like pages, invite friends to events",
        "tabs": ["Criterio", "Convites"],
        # The "Promover página" dialog needs the inline Pesquisar clicked to
        # actually load the saved page link before footer Ok will work.
        "start_sequence": start_search_then_ok_sequence("paginas_eventos"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"invite_scope": "amigos_proximos"},
            "national": {"invite_scope": "todos_amigos"},
        },
    },

    "login_loop": {
        "display_name": "Login Loop",
        "description": "Rotate through multiple accounts (anti-block maintenance)",
        "tabs": ["Contas", "Acoes"],
        "start_sequence": start_module_sequence("login_loop"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            # Login Loop doesn't use targeting - runs across all configured accounts
            "local": {},
            "national": {},
        },
        "do_not_interrupt": True,  # Critical: never stop mid-cycle
    },

    "postar_marketplace": {
        "display_name": "Postar no Marketplace",
        "description": "Post products for sale on Facebook Marketplace",
        "tabs": ["Conteudo", "Opcoes", "Filtros"],
        "start_sequence": start_module_sequence("postar_marketplace"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"grupos_sugeridos": "locais"},
            "national": {"grupos_sugeridos": "todos"},
        },
    },

    "entrar_em_grupos": {
        "display_name": "Entrar em Grupos",
        "description": "Join Facebook groups by keyword search",
        "tabs": ["Criterio", "Opcoes"],
        # Dynamic: the orchestrator passes a `search_term` in the context dict.
        # The lambda is invoked by get_start_sequence() at task-start time so we
        # can rotate through a keyword list across cycles.
        "start_sequence": lambda ctx: start_search_module_sequence(
            "entrar_em_grupos", ctx.get("search_term", "")
        ),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"keywords": ["maes [cidade]", "pais [cidade]", "educacao [cidade]"]},
            "national": {"keywords": ["oferta brasil", "atacado", "revendedores"]},
        },
    },

    "responder_mensagem": {
        "display_name": "Responder Mensagem",
        "description": "Auto-reply to incoming messages by keyword rules",
        "tabs": ["Regras", "Opcoes", "Filtros"],
        "start_sequence": start_module_sequence("responder_mensagem"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {},
            "national": {},
        },
    },

    "curtir": {
        "display_name": "Curtir",
        "description": "Like posts on timeline / friends / specific profiles / pages",
        "tabs": ["Criterio", "Opcoes"],
        "start_sequence": start_module_sequence("curtir"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"criterio": "amigos"},
            "national": {"criterio": "paginas_negocios"},
        },
    },

    "compartilhar": {
        "display_name": "Compartilhar",
        "description": "Share posts from profiles / pages to my profile or groups",
        "tabs": ["Criterio", "Conteudo", "Opcoes"],
        "start_sequence": start_module_sequence("compartilhar"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"destino": "meus_grupos_locais"},
            "national": {"destino": "meu_perfil"},
        },
    },

    "criar_lista": {
        "display_name": "Criar Lista",
        "description": "Build target audience lists (friends/groups/page likers/etc.)",
        "tabs": ["Criterio", "Opcoes"],
        "start_sequence": start_module_sequence("criar_lista"),
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"pais": "Brasil", "cidade": "[cidade_da_escola]"},
            "national": {"pais": "Brasil"},
        },
    },

    # ═══ Instagram Modules (Housoft Insta - separate app) ═══════════════════

    "enviar_direct": {
        "display_name": "Enviar Direct",
        "description": "Send Instagram direct messages",
        "tabs": ["Criterio", "Conteudo", "Opcoes", "Filtros"],
        "start_sequence": [
            # Note: Needs switch to Housoft Insta window first (handled by GUIEngine.bring_to_front)
            {"type": "wait", "seconds": 1.0, "label": "Wait for Instagram window"},
            {"type": "click", "template": "module_enviar_direct",
             "label": "Click Enviar Direct module"},
            {"type": "wait", "seconds": 1.0, "label": "Wait for dialog"},
            {"type": "click", "template": "btn_ok", "label": "Click OK"},
            {"type": "wait", "seconds": 2.0, "label": "Wait for task to start"},
        ],
        "stop_sequence": STOP_SEQUENCE,
        "targeting_options": {
            "local": {"criterio": "seguidores_portal_colegio"},
            "national": {"criterio": "hashtag_search"},
        },
        "app": "insta",
    },
}


def get_sequence(module_key):
    """Get the full sequence config for a module."""
    return MODULE_SEQUENCES.get(module_key)


def get_start_sequence(module_key, context=None):
    """Get the start sequence for a module.

    Some modules (like entrar_em_grupos, which requires a search term) have
    a callable as their `start_sequence` — it's invoked here with the runtime
    context so the orchestrator can inject dynamic values like keywords.
    Static modules return their list verbatim.
    """
    seq = MODULE_SEQUENCES.get(module_key)
    if not seq:
        return None
    start = seq["start_sequence"]
    if callable(start):
        return start(context or {})
    return start


def get_stop_sequence(module_key):
    """Get the stop sequence (same for all modules)."""
    seq = MODULE_SEQUENCES.get(module_key)
    return seq["stop_sequence"] if seq else STOP_SEQUENCE


def get_targeting_config(module_key, targeting_mode):
    """Get targeting configuration for a module (local / national)."""
    seq = MODULE_SEQUENCES.get(module_key)
    if not seq:
        return {}
    return seq.get("targeting_options", {}).get(targeting_mode, {})


def list_modules():
    """Return list of all configured module keys."""
    return list(MODULE_SEQUENCES.keys())


def get_module_app(module_key):
    """Return which Housoft app a module belongs to (face/insta)."""
    seq = MODULE_SEQUENCES.get(module_key)
    return seq.get("app", "face") if seq else "face"
