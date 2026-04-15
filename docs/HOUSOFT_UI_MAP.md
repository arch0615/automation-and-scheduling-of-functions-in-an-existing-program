# Housoft Face UI Map (Discovered from Client Videos)

**Source**: 5 screen recordings from Valesca, April 2026
**Resolution**: 1024 x 768 (confirmed)

---

## Main Window Layout (Pixel Coordinates)

```
y=0-20    : Housoft title bar "Housoft Face (Versao registrada para Valesca...)"
y=20-30   : Bandicam watermark overlay (not part of Housoft UI)
y=30-78   : Menu Row 1 (text on top, circular icon below)
y=78-115  : Menu Row 2 (text on top, circular icon below)
y=115+    : Navegador / Resultados / Fale conosco sub-tabs + main content
```

## Menu Row 1 (Primary Modules)

| Module | Portuguese Name | X Range |
|---|---|---|
| Post in Groups | Postar em grupos | 5-100 |
| Post on Wall | Postar no mural | 100-195 |
| Send Message | Enviar mensagem | 195-280 |
| Add Friends | Adicionar amigo | 280-375 |
| Pages & Events | Paginas e eventos | 375-465 |
| Login Loop | Login loop | 465-550 |

## Menu Row 2 (Secondary Modules)

| Module | Portuguese Name | X Range |
|---|---|---|
| Post on Marketplace | Postar no marketplace | 5-110 |
| Join Groups | Entrar em grupos | 110-200 |
| Reply Messages | Responder mensagem | 200-300 |
| Like | Curtir | 300-380 |
| Share | Compartilhar | 380-470 |
| Create List | Criar lista | 470-555 |

## Configuration Button

| Button | Location |
|---|---|
| Configurar (Settings) | x=558-650, y=30-95 |

## Dialog Structure (Common to All Modules)

When a module is clicked, a dialog opens with these tabs:
- **Criterio** — WHO to target
- **Conteudo** — WHAT to send (text, images, macros)
- **Opcoes** — HOW to behave (timing, limits, rest, login switching)
- **Filtros** — WHO to exclude

Some modules (Enviar Mensagem, Responder Mensagem) use "Principal/Filtro" instead of the full 4-tab layout.

## Dialog Action Buttons (Bottom)

| Button | Portuguese | Purpose |
|---|---|---|
| Ok | Ok | Start the task |
| Ajuda | Ajuda | Help |
| Cancelar | Cancelar | Close dialog |

## Task Control (Top Bar When Running)

When a task is active, red **Parar** (Stop) and yellow **Pausa** (Pause) buttons appear at the top of the window — confirmed in videos showing Paginas e Eventos and Responder Mensagem.

## Videos Inventory

| File | Duration | Module Shown |
|---|---|---|
| bandicam_2026-04-09_17-44-06-253.mp4 | 10:00 | Main view + Postar em Grupos + Postar no Mural + Enviar Mensagem |
| bandicam_2026-04-09_17-59-19-289.mp4 | 3:14 | Enviar Mensagem (Opcoes tab) |
| bandicam_2026-04-09_18-07-59-249.mp4 | 3:10 | Paginas e Eventos (Promover pagina) |
| bandicam_2026-04-09_18-12-25-520.mp4 | 3:16 | Postar no Marketplace |
| bandicam_2026-04-09_18-15-47-751.mp4 | 6:31 | Responder Mensagem |

## Click Sequence to Start a Task

1. Click module button in Menu Row 1 or Row 2 (e.g., "Postar em grupos")
2. Dialog opens — navigate to Criterio / Conteudo / Opcoes / Filtros tabs as needed
3. Configure content, options
4. Click "Ok" to start
5. Dialog closes, **Parar** / **Pausa** buttons appear at top
6. Results log appears in the Resultados tab

## Click Sequence to Stop a Task

1. Click **Parar** button at top of window
2. Task stops, Parar/Pausa buttons disappear

## Click Sequence to Switch Tasks

1. Click **Parar** to stop current task
2. Wait for task to fully stop (~2-4 seconds)
3. Click the new module button
4. Reconfigure if needed (or use saved config)
5. Click **Ok** to start new task

## Content Tabs (Multi-Content Feature)

Every module that posts content supports multiple content variations:
- Tabs labeled "1", "2", "3", ... with "+" to add more
- Each tab has its own text, images, and attachments
- Housoft rotates between them automatically to avoid repetition
- Used for content randomization (anti-bot detection)

## Macros Available

Used in message/post content to personalize:
- `[NOME_GRUPO]` — group name
- `[NOME DO DESTINATARIO]` — recipient name
- `[AGRADECIMENTO]` — thank-you phrase
- `[EMOJIS]` — emoji set
- `[LINK DO WHATS]` — WhatsApp link
- `[SAUDACAO]` — greeting
- `[FRASE MOTIVACIONAL]` — motivational phrase
- `<nome>` — short form for recipient name

## Templates Extracted

All templates saved to `templates/` folder for OpenCV matching:
- 12 `module_*.png` (full button with text + icon)
- 12 `text_*.png` (text-only, more compact)
- `titlebar_face.png` (window detection)
- `module_configurar.png` (settings button)

---

## Still Needed (Cannot Be Extracted From Videos)

1. **Parar / Pausa button templates** — need a live frame showing them enabled
2. **Ok / Ajuda / Cancelar button templates** — exact pixel positions depend on dialog position on screen
3. **Tab button templates** (Criterio, Conteudo, Opcoes, Filtros) — positions vary per module
4. **Popup / error dialog templates** — not captured in any video
5. **Housoft Insta UI** — no video sent for Insta yet

These will need to be captured from the live Housoft system via AnyDesk access.
