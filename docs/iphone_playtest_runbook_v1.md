# iPhone Playtest Runbook v1

**Generated**: 2026-06-23 16:23 GMT+8
**Target**: 杨亚超 + 1-2 iPhone testers
**Session length**: 15-30 minutes per tester
**Production**: `source-v3.7-pb` (FROZEN)
**PWA verdict**: IPHONE_PWA_READY (see `reports/iphone_pwa_mvp_v1.md`)
**Companion docs**: `docs/iphone_playtest_guide.md` (how to install + play), `reports/iphone_pwa_mvp_v1.md` (PWA architecture)
**Author**: OpenClaw agent

---

## 0. Purpose

This runbook is for **hands-on iPhone user playtest** before any UX polish work. It is intentionally:

- **Short** — 15-30 minutes per session (not a full game playthrough)
- **Structured** — every step has a tickbox and a time budget
- **Capture-friendly** — every step has a "what to report" hook
- **Gate-driven** — pass/fail is defined up-front in Section 4

The goal is to surface **iPhone-specific PWA friction** (notch overlap, home indicator, save persistence, modal stacking) and **first-time UX confusion** (first 60 seconds, action clarity). We are NOT looking for game-balance feedback — production is frozen, balance is a separate cycle.

---

## 1. Pre-test setup (3 min, do this once)

### 1.1 Tester profile

Fill this in before starting:

```
Tester name: ____________________
iPhone model: ____________________   (e.g. iPhone 13 Pro)
iOS version:  ____________________   (Settings → General → About → Software Version)
Safari version: __________________   (Settings → Safari → About)
Network:       ☐ Wi-Fi   ☐ Cellular
              SSID: ____________________ (omit if cellular)
              Router: ____________________ (e.g. Asus RT-AX86U, if known)
Server URL:   http://<your-server>:5000/   (or LAN IP)
PWA install:   ☐ Fresh (never installed)
              ☐ Already installed (delete first: long-press → Remove App → Delete)
Date / time:   ____________________ (GMT+8)
```

### 1.2 Fresh-install prep (recommended)

1. If you've played before, **delete the existing PWA**:
   - Long-press the ⚔️ icon on home screen
   - Tap "Remove App" → "Delete App"
2. Clear Safari data for the test URL (optional, for cleanest state):
   - Settings → Safari → Advanced → Website Data → find the URL → swipe left → Delete
3. Charge your iPhone to ≥ 80% (the 30-min session uses ~3-5%)

### 1.3 Have ready

- A timer (phone clock, or `say "set timer 30 minutes"` to Siri)
- A way to take screenshots (Volume Up + Side button)
- A notepad (Notes app, or a paper notebook) for quick text feedback
- A Feishu DM window for sending back the completed runbook

---

## 2. The 15-30 minute playtest checklist

Each step has a time budget. If you blow the budget, that's a finding — note it. If you can't complete a step at all, that's a blocker — Section 5.

### Phase A — Install & first launch (target 3 min)

| # | Step | Pass criterion | Time | ✓/✗ | Notes |
|---:|---|---|---:|:---:|---|
| A1 | Open `<server-url>` in iPhone Safari | Start screen renders with "⚔️ 三国文字Roguelike" | 30s | ☐ | |
| A2 | Tap Share → "Add to Home Screen" → Add | ⚔️ icon appears on home screen | 30s | ☐ | |
| A3 | Tap the ⚔️ icon on home screen | App launches in standalone (no Safari URL bar) | 30s | ☐ | |
| A4 | Verify status bar is transparent / overlaid (notch + island) | No double-header; top bar not hidden | 10s | ☐ | |
| A5 | Verify home indicator does NOT overlap bottom nav | "📍地图" button is fully tappable | 10s | ☐ | |

**Total Phase A target: 3 min**

### Phase B — First 60 seconds (target 1 min)

> The hardest UX test. Fresh user, no instructions, no prior context.

| # | Step | Pass criterion | Time | ✓/✗ | Notes |
|---:|---|---|---:|:---:|---|
| B1 | Land on start screen, locate "开始新游戏" button | Find without help within 10s | 10s | ☐ | |
| B2 | Tap "开始新游戏" | Main game screen renders, time shows "184年1月" | 5s | ☐ | |
| B3 | Read the top stats bar — can you identify HP, gold, food? | Identify all 3 within 15s | 15s | ☐ | |
| B4 | Find the "⏭️下月" button (bottom nav or pull-to-refresh) | Find within 10s | 10s | ☐ | |
| B5 | Tap "⏭️下月" — does time advance? | Time updates to "184年2月" | 5s | ☐ | |
| B6 | Does the narrative area show any text? | Something appears (intro or empty) | 5s | ☐ | |
| B7 | Try pull-to-refresh on the narrative area | Time advances again (proves pull-to-refresh works) | 10s | ☐ | |

**Total Phase B target: 60s**

### Phase C — Core loop (target 10 min)

> Drive the game forward. Tap "下月" ~30 times, take the first encounter you get.

| # | Step | Pass criterion | Time | ✓/✗ | Notes |
|---:|---|---|---:|:---:|---|
| C1 | Tap "⏭️下月" 10 times in a row | Time advances each time, no crash | 60s | ☐ | |
| C2 | Open "📍地图" — does a list of cities appear? | List shows, current city highlighted | 15s | ☐ | |
| C3 | Tap an adjacent city (e.g. 洛阳 if at 颍川) | Game moves, location updates | 10s | ☐ | |
| C4 | Continue tapping "下月" until an encounter fires | Combat OR NPC OR market triggers | 2-4 min | ☐ | |
| C5 | If combat fires: read enemy stats, tap any action button | Combat resolves, narrative updates | 30s | ☐ | |
| C6 | If NPC fires: read options, tap "交谈" (option 5, safe) | NPC responds, encounter ends | 20s | ☐ | |
| C7 | If market fires: tap "buy" or "leave" | Market accepts input | 20s | ☐ | |
| C8 | Open "📊状态" — does a status panel show? | Status panel shows current stats | 15s | ☐ | |
| C9 | Open "🏆成就" — does a bottom sheet slide up? | Sheet appears, achievements list visible | 15s | ☐ | |
| C10 | Close the achievements sheet (swipe down or close button) | Sheet dismisses | 10s | ☐ | |
| C11 | Open "📜战报" — does a history sheet show? | Sheet appears, history list visible | 15s | ☐ | |

**Total Phase C target: 8-10 min**

### Phase D — Death → Death Shop → Reincarnation (target 5 min)

> The hardest mechanic. Needs to be crystal-clear.

| # | Step | Pass criterion | Time | ✓/✗ | Notes |
|---:|---|---|---:|:---:|---|
| D1 | Force your character to die (lose combat OR let HP drop) | HP reaches 0 OR time reaches 220年 | 1-3 min | ☐ | |
| D2 | Verify death screen appears (narrative ends with "陨落" or "三国鼎立") | Death message visible | 10s | ☐ | |
| D3 | Verify Death Shop appears with skill list + fragments balance | Shop renders, fragments > 0 | 10s | ☐ | |
| D4 | Read a skill description — do you understand what it does? | Can describe the skill's effect in 1 sentence | 30s | ☐ | |
| D5 | Try to buy a skill (if fragments sufficient) | Skill purchased, fragments deducted | 20s | ☐ | |
| D6 | Find the "转世" / reincarnate button | Find within 15s | 15s | ☐ | |
| D7 | Tap "转世" — does a new game start? | New game screen, time "184年1月" again | 10s | ☐ | |
| D8 | Check if reincarnation karma is applied (stats higher than initial) | At least one stat is higher than 40/30/10/20/30 baseline | 15s | ☐ | |

**Total Phase D target: 4-5 min**

### Phase E — Save/load (target 2 min)

> The most critical PWA feature.

| # | Step | Pass criterion | Time | ✓/✗ | Notes |
|---:|---|---|---:|:---:|---|
| E1 | Note current year/month/location (e.g. "185年3月 / 洛阳") | ___year___月 / ___city___ | 5s | ☐ | |
| E2 | Force-quit the PWA: swipe up from home indicator → swipe app up | App closes | 5s | ☐ | |
| E3 | Re-launch the PWA from home screen icon | App opens, Main Game screen renders | 10s | ☐ | |
| E4 | Verify the game resumed at the same year/month/location | Year/month/location match E1 | 10s | ☐ | |
| E5 | Verify stats (HP, gold, food) match what you had | Stats match what you had | 10s | ☐ | |
| E6 | Tap "⏭️下月" once — does the game continue normally? | Time advances, no crash | 5s | ☐ | |

**Total Phase E target: 2 min**

### Phase F — Final feedback (target 2 min)

| # | Step | Pass criterion | Time | ✓/✗ | Notes |
|---:|---|---|---:|:---:|---|
| F1 | Spend 60 seconds just LOOKING at the screen. Anything weird? | Take note of any visual oddities | 60s | ☐ | |
| F2 | Type one sentence: "If I could change ONE thing, it would be..." | Sentence recorded | 30s | ☐ | |
| F3 | Send the completed runbook back via Feishu DM | Sent | 30s | ☐ | |

**Total Phase F target: 2 min**

### Total session target: 18-23 min (A: 3 + B: 1 + C: 10 + D: 5 + E: 2 + F: 2)

---

## 3. Bug report template

Use this for any unexpected behavior, crash, save loss, or visual bug. **One bug per template** — easier to triage.

```
─────────────────────────────────────────────
BUG REPORT — iPhone PWA MVP v1
─────────────────────────────────────────────
Tester name:        ____________________
Date / time:        ____________________ (GMT+8)
iPhone model:       ____________________
iOS version:        ____________________
Network:            ☐ Wi-Fi  ☐ Cellular
PWA install state:  ☐ Home screen  ☐ Safari only
Server URL:         ____________________
Game state at time of bug:
  Year/Month:       ______年____月
  Location:         ____________________
  HP / Gold / Food: ____ / ____ / ____
  Recent action:    ____________________

─────────────────────────────────────────────
WHAT I DID:
  1. _______________
  2. _______________
  3. _______________

WHAT I EXPECTED:
  _______________

WHAT HAPPENED:
  _______________

REPRODUCIBLE?
  ☐ Yes (happens every time)
  ☐ Sometimes (about __% of attempts)
  ☐ Once (couldn't reproduce)

SCREENSHOT:   ☐ Attached   ☐ Could not capture

WORKAROUND:   _______________ (if any)

SEVERITY:     ☐ Blocker (can't play)  ☐ Major (lost save / crash)
              ☐ Minor (UI weird)        ☐ Cosmetic (visual nit)
─────────────────────────────────────────────
```

### Common things to check FIRST (before filing a bug)

| Symptom | Check this first | Still broken? |
|---|---|---|
| "网络错误" toast | Is the server running? Try `<url>/api/state` in iPhone Safari | File bug with network section |
| White screen | Force-quit, reopen. If still white: Settings → Safari → Website Data → delete the URL | File bug with iOS version |
| Save lost | Did you delete the PWA? Or clear Safari data? Or have it on home screen? | File bug only if you did none of these |
| Buttons not responding | Force-quit, reopen. Try double-tap (iOS may slow-click first time) | File bug with iPhone model |
| Stuck on a modal | Tap outside the modal. If stuck: force-quit | File bug with modal name |
| Status bar overlap | Are you on the home-screen PWA, or in Safari? (Safari has a separate URL bar) | Remove and re-add to home screen |

---

## 4. UX feedback template

After completing the playtest, fill this in. This is **subjective** — your honest impressions matter more than your expertise.

### 4.1 First 60 seconds

| Question | Your answer |
|---|---|
| Q1.1: How long did it take to understand what to do first? | _____ seconds |
| Q1.2: What did you do FIRST without reading any text? | _________________________________________ |
| Q1.3: Did you ever feel lost or confused in the first 60 seconds? | ☐ No  ☐ Yes — what confused you? _________________________________ |
| Q1.4: Rate the first-60-seconds experience | ☐ 1 (terrible)  ☐ 2  ☐ 3  ☐ 4  ☐ 5 (great) |

### 4.2 Action clarity

| Question | Your answer |
|---|---|
| Q2.1: When combat fired, did you know what each button (进攻/坚守/撤退/用计) does? | ☐ Yes  ☐ No — which one was unclear? _________________________________ |
| Q2.2: When an NPC encounter fired, did you know what "诚心相邀" vs "晓以大义" means? | ☐ Yes  ☐ No |
| Q2.3: When the market opened, did you know what to do? | ☐ Yes  ☐ No |
| Q2.4: Did you ever tap a button and NOT know what would happen? | ☐ No  ☐ Yes — which one? _________________________________ |
| Q2.5: Rate action clarity overall | ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5 |

### 4.3 Button size & touch targets

| Question | Your answer |
|---|---|
| Q3.1: Did you ever mis-tap a button (tapped one, got another)? | ☐ No  ☐ Yes — which buttons? _________________________________ |
| Q3.2: Were any buttons too SMALL to comfortably tap? | ☐ No  ☐ Yes — which ones? _________________________________ |
| Q3.3: Were any buttons too BIG (wasting screen space)? | ☐ No  ☐ Yes — which ones? _________________________________ |
| Q3.4: Was the bottom-nav (📍⏭️📊🏆📜) easy to reach with your thumb? | ☐ Yes, comfortable  ☐ Slight stretch  ☐ Hard to reach |
| Q3.5: Rate button/touch ergonomics | ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5 |

### 4.4 Log / narrative readability

| Question | Your answer |
|---|---|
| Q4.1: Can you read the narrative text comfortably (font size, color)? | ☐ Yes  ☐ Too small  ☐ Too dim  ☐ Hard to find |
| Q4.2: Did you ever have to SCROLL to find what just happened? | ☐ No  ☐ Yes — annoying?  ☐ Yes — fine |
| Q4.3: When combat ended, was the result clear in the narrative? | ☐ Yes  ☐ Unclear — what was unclear? _________________________________ |
| Q4.4: Were the stat numbers (HP 100, 金 50) easy to read at a glance? | ☐ Yes  ☐ No — which ones? _________________________________ |
| Q4.5: Rate the log/narrative readability | ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5 |

### 4.5 Death & reincarnation clarity

| Question | Your answer |
|---|---|
| Q5.1: When your character died, did you understand what just happened? | ☐ Yes  ☐ No — what was unclear? _________________________________ |
| Q5.2: On the Death Shop screen, did you understand what "碎片" (fragments) is? | ☐ Yes  ☐ No — what was unclear? _________________________________ |
| Q5.3: Could you tell what each skill in the shop would do for you? | ☐ Yes  ☐ No — what was unclear? _________________________________ |
| Q5.4: When you tapped "转世", did you know your old character was gone forever? | ☐ Yes  ☐ No — it was unclear what would happen |
| Q5.5: After reincarnation, did you notice any stat change from "前世修为"? | ☐ Yes  ☐ No — was it announced clearly?  ☐ What did you see? _________________________________ |
| Q5.6: Rate the death/reincarnation experience | ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5 |

### 4.6 Save/load confidence

| Question | Your answer |
|---|---|
| Q6.1: Before force-killing the app, did you trust the save would persist? | ☐ Yes, fully  ☐ Slightly worried  ☐ Not at all |
| Q6.2: After re-launching, did the game resume at the right place? | ☐ Yes, exactly  ☐ Close but not exact (drift of: ___)  ☐ No, lost save |
| Q6.3: Was there any visual indicator that the game was saving? | ☐ Yes  ☐ No — would have liked one |
| Q6.4: After resuming, did you lose any progress (items, NPCs, etc.)? | ☐ No  ☐ Yes — what was lost? _________________________________ |
| Q6.5: Rate save/load confidence | ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5 |

### 4.7 Overall impression

| Question | Your answer |
|---|---|
| Q7.1: If a friend asked "is this fun?", what would you say? | _________________________________________ |
| Q7.2: If you could change ONE thing about the iPhone experience, it would be: | _________________________________________ |
| Q7.3: Would you keep this app on your home screen? | ☐ Yes  ☐ Maybe  ☐ No — why? _________________________________ |
| Q7.4: Overall iPhone PWA experience | ☐ 1  ☐ 2  ☐ 3  ☐ 4  ☐ 5 |

---

## 5. iPhone Playability Gate v1 — pass/fail definition

This gate is run by the developer after collecting ≥ 1 playtest session. Each criterion is **binary** (PASS / FAIL). Borderline is FAIL → fix → re-run.

### Gate criteria (12 total)

| # | Criterion | PASS definition | Source of truth |
|---:|---|---|---|
| **G1** | **Installable PWA** | A2 in checklist passes (icon appears on home screen) | Tester ✓/✗ |
| **G2** | **Standalone launch** | A3 in checklist passes (no Safari chrome) | Tester ✓/✗ |
| **G3** | **First-60s onboarding** | All B1-B7 pass; tester rates Q1.4 ≥ 3 | Checklist + UX template |
| **G4** | **Map works** | C2-C3 pass; tester can move cities | Tester ✓/✗ |
| **G5** | **Encounters fire and resolve** | C4-C7 all pass; combat OR NPC OR market all resolve without crash | Tester ✓/✗ |
| **G6** | **Bottom sheets work** | C8-C11 pass; status / achievements / history all open and close | Tester ✓/✗ |
| **G7** | **Death triggers and is clear** | D1-D3 pass; death message visible | Tester ✓/✗ |
| **G8** | **Death Shop works** | D3-D5 pass; can buy a skill | Tester ✓/✗ |
| **G9** | **Reincarnation works** | D6-D8 pass; karma applied | Tester ✓/✗ |
| **G10** | **Save/load round-trip** | E1-E6 all pass; game resumes at same year/month/location/stats | Tester ✓/✗ |
| **G11** | **No crash in 15 minutes** | The 15-30 min session completes without the app crashing or showing error | Tester ✓/✗ |
| **G12** | **PWA install doesn't visibly break** | After install, A4 + A5 pass (status bar, home indicator don't overlap) | Tester ✓/✗ |

### Gate decision

| Outcome | Condition | Action |
|---|---|---|
| 🟢 **GREEN** | G1-G12 all PASS, AND Q7.4 (overall) ≥ 4 | **READY_FOR_UX_POLISH** cycle. No further PWA work needed. |
| 🟡 **YELLOW** | G1-G11 all PASS, but one of: G12 fails (cosmetic) OR Q7.4 = 3 | **NEEDS_MINOR_PWA_FIX** — tweak safe-area CSS, re-test on 1 device |
| 🟡 **YELLOW** | G3 OR G8 OR G9 fails (UX confusion, not blocker) | **NEEDS_UX_COPY_FIX** — clarify text, re-test on 1 device |
| 🔴 **RED** | Any G1, G2, G5, G7, G10, G11 fails | **BLOCKED** — fix blocker before re-running. Common causes: PWA scope, save/load round-trip, modal stacking |

### Gate summary (filled by developer after playtest)

```
iPhone Playability Gate v1
═══════════════════════════════════════════
Date:             ____________________
Tester:           ____________________
Server URL:       ____________________
iOS version:      ____________________

G1  Installable PWA:        ☐ PASS  ☐ FAIL
G2  Standalone launch:      ☐ PASS  ☐ FAIL
G3  First-60s onboarding:   ☐ PASS  ☐ FAIL
G4  Map works:              ☐ PASS  ☐ FAIL
G5  Encounters resolve:     ☐ PASS  ☐ FAIL
G6  Bottom sheets work:     ☐ PASS  ☐ FAIL
G7  Death triggers clear:   ☐ PASS  ☐ FAIL
G8  Death Shop works:       ☐ PASS  ☐ FAIL
G9  Reincarnation works:    ☐ PASS  ☐ FAIL
G10 Save/load round-trip:   ☐ PASS  ☐ FAIL
G11 No crash in 15 min:     ☐ PASS  ☐ FAIL
G12 PWA install clean:      ☐ PASS  ☐ FAIL

UX scores (out of 5):
  First 60s (Q1.4):         ____
  Action clarity (Q2.5):    ____
  Button ergonomics (Q3.5): ____
  Log readability (Q4.5):   ____
  Death/reincarnation (Q5.6): ____
  Save/load confidence (Q6.5): ____
  Overall (Q7.4):           ____

Verdict:  ☐ GREEN (12/12 PASS, overall ≥ 4)
          ☐ YELLOW (any minor fail or overall = 3)
          ☐ RED (any blocker fail)

Bugs filed: _____ (list IDs below)
  B1: ____________________
  B2: ____________________
  B3: ____________________

Top 3 UX improvements (from Q7.2):
  1. _____________________________________
  2. _____________________________________
  3. _____________________________________
═══════════════════════════════════════════
```

---

## 6. After the playtest

### What happens next (developer)

1. **Collect** the completed runbook + bug reports + UX template from the tester
2. **Triage** bugs:
   - P0 (blocker): fix immediately, re-run full gate
   - P1 (major): schedule in next iteration
   - P2 (minor / cosmetic): backlog
3. **Score** the UX template:
   - Any score 1-2 → must address in next iteration
   - Any score 3 → consider addressing
   - Score 4-5 → no action
4. **Decide** gate verdict (Section 5)
5. **Update** `MEMORY.md` with playtest results + verdict
6. **Plan** next cycle (likely UX polish, not more PWA work)

### What the playtest is NOT

- ❌ A game-balance playtest (production is FROZEN; balance is v3.10 cycle)
- ❌ A long-run test (we don't need a 200-seed playtest like the v1.5 engine validation)
- ❌ A multi-device matrix (one iPhone model is enough for v1; we'll expand to Android + older iOS in v2)
- ❌ A network stress test (Flask on localhost / Railway is already validated)

### What the playtest IS

- ✅ A "does the PWA actually work on a real iPhone" check
- ✅ A "does a fresh user understand the game in 60 seconds" check
- ✅ A "does save/load survive a real app kill" check
- ✅ A "is the death/reincarnation loop clear" check
- ✅ A bug surface for the UX polish cycle

---

## 7. Verdict

# 🟢 **READY_FOR_USER_IPHONE_PLAYTEST**

**Why**:
1. PWA build is verified (IPHONE_PWA_READY in `reports/iphone_pwa_mvp_v1.md`)
2. Production engine is FROZEN at source-v3.7-pb (no risk to validated gameplay)
3. This runbook provides structured capture (checklist + bug template + UX template + gate)
4. Companion guide (`docs/iphone_playtest_guide.md`) covers install + play
5. Gate has 12 measurable criteria with clear GREEN/YELLOW/RED decision

**No guide fixes needed.** The user (杨亚超) can now run this runbook on their iPhone and send back the completed checklist + bug reports + UX template via Feishu DM.

**Next step (waiting on user)**: run a 15-30 min iPhone playtest using this runbook, send the completed runbook back.
