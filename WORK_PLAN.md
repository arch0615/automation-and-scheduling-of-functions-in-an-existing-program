# Housoft Meta — 2-Day Completion Plan

**Scope:** Every deliverable from the original 3-day plan preserved — nothing dropped. Achieved by running Day 1 as an extended remote session and running the Day 2 sustained validation **in parallel** with hardening and documentation tasks.

**Total budget:** ~16 hours of active work across 2 calendar days.

**Prerequisite (must be done BEFORE Day 1):** All client-side preparation complete — see [Pre-Day-1 Checklist](#pre-day-1-checklist) below.

---

## Pre-Day-1 Checklist

Nothing below is optional. Missing items pushes the plan.

- [ ] Client laptop accessible via AnyDesk, uninterrupted for Day 1
- [ ] Python 3.8+ installed on client machine
- [ ] `housoft-meta/` repo pulled to client machine, `pip install -r requirements.txt` completed
- [ ] Housoft Face installed and logged in
- [ ] Housoft Instagram installed and logged in (if Insta used)
- [ ] Screen resolution **fixed** at production value
- [ ] Display scaling set to **100%**
- [ ] Antivirus whitelist entries added for `python.exe` and the project folder
- [ ] Power settings: no sleep, no hibernate, lid stays open
- [ ] Client-provided: dashboard credentials, ngrok token, operating hours, content library, targeting lists, enabled task list
- [ ] Admin rights confirmed on client laptop

---

## DAY 1 — Templates + Full Live Integration (8-10h remote session)

**Objective:** Finish Days 1 and 2 of the original plan in a single extended remote session. Exit with all templates captured, matching validated, and every live-integration test passed.

### Morning Block (4-5h)

#### 1.1 — Environment verification (20 min)
- [ ] Confirm resolution and scaling on client machine
- [ ] Activate venv, run `pip list` to confirm dependencies
- [ ] Open Housoft Face, bring to foreground
- [ ] Run `python main.py --help` or equivalent sanity check

#### 1.2 — Capture the 13 missing templates (2 h)
```bash
python capture_templates.py
```
- [ ] `titlebar_insta` (needs Housoft Insta open)
- [ ] `btn_ok`, `btn_ajuda`, `btn_cancelar` (open any module dialog)
- [ ] `tab_criterio`, `tab_conteudo`, `tab_opcoes`, `tab_filtros` (module dialog)
- [ ] `btn_parar`, `btn_pausa` (start a module, then capture from top toolbar)
- [ ] `module_enviar_direct` (switch to Housoft Insta)
- [ ] `popup_blocked`, `popup_error` — if not visible now, run a high-volume module briefly to trigger one; otherwise mark to capture opportunistically during Block 1.4

#### 1.3 — Template matching validation (30 min)
```bash
python tests/test_template_matching.py
```
- [ ] All tests pass
- [ ] For any failure: inspect `_preview_<name>.png`, re-capture with tighter crop
- [ ] Re-run until green

#### 1.4 — E2E test suite with mock GUI (15 min)
```bash
python tests/test_orchestrator_e2e.py
```
- [ ] All 4 tests pass (Basic Flow, Category Ordering, Intensity, Pause/Resume)

#### 1.5 — Live single-task smoke test (1 h)
- [ ] Disable all tasks in `schedule.json` except one short one (3-5 min, e.g., `entrar_em_grupos`)
- [ ] Set peak hours to cover current time
- [ ] `python main.py` → dashboard → **Start**
- [ ] Verify on screen: window focus → module click → OK click → duration elapses → "Parar" click → history updated

### Afternoon Block (4-5h)

#### 1.6 — Multi-task rotation test (1.5 h)
- [ ] Enable 3-4 short tasks in `schedule.json` (5 min each)
- [ ] Run full cycle
- [ ] Verify category order: maintenance → growth → posting → messaging → engagement
- [ ] Verify random inter-task delays
- [ ] Verify all tasks complete without intervention

#### 1.7 — Pause/Resume/Stop validation (30 min)
- [ ] Pause mid-task → current task finishes → no new task starts → confirm via log
- [ ] Resume → next task starts → confirm via log
- [ ] Stop → current task halts (Parar clicked) → orchestrator thread exits
- [ ] Clean Start again → verify fresh run

#### 1.8 — Popup handling test (30 min)
- [ ] If a popup appeared during earlier blocks, re-verify auto-dismissal
- [ ] If no popup yet, manually trigger one (dismiss it → orchestrator must handle without crashing)
- [ ] Capture any new popup variants discovered

#### 1.9 — Intensity transition test (45 min)
- [ ] Adjust `schedule.json` so current time is near a peak/moderate or moderate/off boundary
- [ ] Watch transition in log
- [ ] Verify: off-hours → no new tasks started; moderate → duration multiplied by 0.6

#### 1.10 — ngrok + mobile dashboard (30 min)
- [ ] Set `NGROK_AUTH_TOKEN` in `.env`
- [ ] Restart `main.py`
- [ ] Copy ngrok URL, open on phone
- [ ] Log in, verify status updates, verify controls work

#### 1.11 — End-of-Day-1 commit & handoff note (15 min)
- [ ] Commit captured templates: `git add templates/ && git commit -m "Capture production UI templates"`
- [ ] Leave system running overnight? — decide with client
- [ ] Note any issues/quirks for Day 2

### Day 1 Deliverables
- All 10+3 templates captured and matching
- E2E tests green
- Every live test from original Day 2 plan passed
- Mobile dashboard access confirmed

---

## DAY 2 — Hardening, Autostart, and 2h Sustained Run (6-8h, ~2h parallel observation)

**Objective:** Complete all Day 3 hardening AND the 2-hour sustained validation. Key trick: **start the sustained run first, then do hardening tasks in parallel while observing it.**

### Morning Block (3-4h)

#### 2.1 — Production credentials (30 min)
Edit `.env` on client machine:
- [ ] `DASHBOARD_USERNAME` — client's preferred value
- [ ] `DASHBOARD_PASSWORD` — strong password (12+ chars)
- [ ] `FLASK_SECRET_KEY` — generate random:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] `NGROK_AUTH_TOKEN` — confirm set to real token
- [ ] Confirm `.env` is NOT committed (check `.gitignore`)

#### 2.2 — Tune production schedule (30 min)
- [ ] Set final peak/moderate/off hours per client preference
- [ ] Enable client's chosen tasks, disable others
- [ ] Set production `duration_min` per task
- [ ] Confirm randomization params (delays, variation)
- [ ] Reload/restart to pick up changes

#### 2.3 — **Start the 2-hour sustained run** (0 min active — runs in background)
- [ ] Launch system under watchdog: `python watchdog.py`
- [ ] Note start time — this is your T+0 for the 2h run
- [ ] Dashboard accessible, initial state logged
- [ ] **All remaining Day 2 tasks run while this is live**

#### 2.4 — Watchdog recovery test (45 min) — *parallel to sustained run*
- [ ] Identify `main.py` process in Task Manager
- [ ] Kill it
- [ ] Watch `logs/watchdog.log` — restart should occur within ~10 seconds
- [ ] Verify dashboard becomes reachable again
- [ ] Do this twice to confirm repeatability
- [ ] Note: this test counts as a disruption inside the 2h window — that's OK, the 2h run continues after restart

#### 2.5 — Autostart install (45 min) — *parallel*
- [ ] Stop the system cleanly
- [ ] `python install_autostart.py`
- [ ] Confirm registry / startup entry created
- [ ] Reboot the client laptop
- [ ] After login, confirm watchdog + main.py running automatically
- [ ] Dashboard reachable
- [ ] **Resume the sustained run timer** — add 15 min to originally-noted start time to compensate, or simply extend to a full 2h after reboot

#### 2.6 — Mid-run observation (ongoing — check every 20 min)
- [ ] Dashboard: current task, intensity mode, history accumulating
- [ ] Log file: no unhandled errors
- [ ] Task Manager: memory stable, CPU reasonable
- [ ] Any popups handled automatically

### Afternoon Block (3-4h)

#### 2.7 — Continue 2h sustained run (passive)
- [ ] Aim for a full 2-hour clean window after the autostart reboot
- [ ] If watchdog or autostart test caused a restart mid-run, the 2h clock resets from the last clean start
- [ ] Observations logged every 20 min continue

#### 2.8 — Cross-time-period validation (30 min) — *during run*
- [ ] If possible, arrange the 2h window to span a peak→moderate or moderate→off transition
- [ ] Verify the transition in the log and dashboard (intensity_mode changes)

#### 2.9 — Final deployment checklist (30 min)
Work through each:
- [ ] All UI templates captured
- [ ] Template matching tests pass
- [ ] E2E tests pass
- [ ] Live single-task tested
- [ ] Live multi-task tested
- [ ] Pause/Resume/Stop verified
- [ ] Popup auto-dismissal verified
- [ ] Intensity transitions verified
- [ ] Mobile dashboard via ngrok verified
- [ ] Watchdog recovery verified
- [ ] Autostart verified
- [ ] Secure credentials in `.env`
- [ ] Production `schedule.json` saved
- [ ] 2h sustained run complete with no unhandled errors
- [ ] Memory/CPU baseline recorded

#### 2.10 — Deployment notes (30 min)
Create `DEPLOYMENT_NOTES.md` on the client machine and in the repo:
- [ ] Confirmed screen resolution and scaling
- [ ] Confirmed Housoft window titles
- [ ] Template matching confidence values used
- [ ] Antivirus whitelist entries
- [ ] Any OS-specific quirks encountered
- [ ] Recovery procedure: how to restart manually, where logs are, how to check watchdog
- [ ] Client-specific operating hours and enabled task list

#### 2.11 — Client handoff walkthrough (45 min)
Live with client:
- [ ] Show how to log into dashboard (local + mobile)
- [ ] Demo Start / Pause / Resume / Stop
- [ ] Show how to toggle individual tasks on/off
- [ ] Show where logs live and how to read them
- [ ] Explain recovery: what happens if system crashes, how watchdog restarts it
- [ ] Explain what *not* to do (minimize Housoft, change resolution, close lid)
- [ ] Confirm they can access dashboard from their phone

#### 2.12 — Final commit & close (15 min)
- [ ] Commit any final config/doc changes
- [ ] Leave system running under watchdog + autostart
- [ ] Confirm with client, disconnect

### Day 2 Deliverables
- Secure production credentials
- Watchdog + autostart both verified
- 2h clean sustained run complete
- Full deployment checklist ticked
- Handoff documentation written
- Client trained on dashboard

---

## Parallelization Logic (Why 2 Days Fits Everything)

The 3-day plan was serial. The 2-day plan overlaps:

```
Day 2 Morning:
  [Credentials 30m] → [Schedule tune 30m] → [START 2h RUN] ──────────────┐
                                                                         │
  While 2h run is live (passive observation every 20 min):               │
    [Watchdog recovery 45m]   ┐                                          │
    [Autostart + reboot 45m]  ├─ done in parallel with run observation   │
    [Checklist 30m]           │                                          │
    [Notes + handoff 1h]      ┘                                          │
                                                                         │
  2h run ends ─────────────────────────────────────────────────────────┘
  Final commit.
```

The sustained run doesn't require active attention — only periodic checks. All Day 3 hardening happens during that window.

---

## Risk & Contingency

| Risk | 2-day impact | Mitigation |
|------|--------------|------------|
| Template re-capture needed after initial session | Eats into Day 1 afternoon | Budget shows slack — if overrun, compress 1.6/1.7 by reducing test task count |
| Watchdog/autostart problem on Day 2 | Delays 2h run start | Troubleshoot first (30m max), then run watchdog manually for the 2h window — install autostart second |
| Popup never appears naturally | Popup templates uncaptured | Trigger manually by running a known-risky module; if still impossible, capture opportunistically during ongoing operation after Day 2 |
| Client laptop reboot loop or autostart fails | Day 2 afternoon at risk | Have fallback: schedule watchdog as a Windows Task instead of registry entry — already supported by `install_autostart.py` |
| Day 1 runs over | Less sleep before Day 2 | Day 1 has no hard stop — extend to evening. Day 2 morning start can slide 1-2h without breaking plan |
| ngrok free tier URL rotation surprises client | Client can't reach dashboard next day | Document URL retrieval method; recommend paid ngrok plan or reserve a static URL |

**If Day 1 overruns past 10h:** push blocks 1.9-1.10 (intensity + ngrok) to the start of Day 2. Everything still fits.

---

## Success Criteria (same as 3-day plan — nothing relaxed)

By end of Day 2, all of the following must be true:

1. System runs continuously under watchdog
2. All enabled tasks execute successfully in live Housoft
3. Dashboard accessible locally and remotely from phone
4. Popups detected and dismissed automatically
5. System recovers from process crashes within 10 seconds
6. Auto-starts on machine reboot
7. Credentials and secrets are production-grade
8. Logs show no unhandled errors during 2-hour sustained run
9. Client trained on dashboard operation
10. Handoff documentation complete

---

## Quick Command Reference

```bash
# Install / update
pip install -r requirements.txt

# Capture templates interactively
python capture_templates.py

# Run tests
python tests/test_template_matching.py
python tests/test_orchestrator_e2e.py

# Run under watchdog (production)
python watchdog.py

# Run directly (development)
python main.py

# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Install Windows autostart
python install_autostart.py

# Check watchdog log
type logs\watchdog.log

# Check main log
type logs\housoft_meta.log
```
