# iPhone Playtest Guide — 三国文字Roguelike (PWA v1)

**Version**: v1 (2026-06-23)
**Target**: iPhone Safari (iOS 16+) → install as PWA on home screen
**Production**: `source-v3.7-pb` (FROZEN)
**Goal**: play a full death/reincarnation loop on your iPhone and report any issues.

---

## 0. What's new (compared to web-only)

The game is now a **Progressive Web App (PWA)** that you can install on your iPhone home screen. Once installed, it runs in standalone mode (no Safari chrome), supports offline app shell, and behaves like a native app for save/load and restart.

---

## 1. How to open the game

### Option A — Public URL (recommended, easiest)

1. Open Safari on your iPhone
2. Go to: **`<your Railway or VPS URL>`** (ask the developer for the URL)
3. You should see the start screen with ⚔️ 三国文字Roguelike ⚔️

> **NOTE**: iOS Safari shows the URL bar at the top. To get the fullscreen PWA experience, install to home screen (next section).

### Option B — LAN (laptop + iPhone on same WiFi)

Use this when developing locally:

1. **On your laptop**, start the Flask server:
   ```bash
   cd /root/sanguo_roguelike
   python3 api.py
   ```
   You should see: `Running on http://0.0.0.0:5000`

2. **Find your laptop's LAN IP**:
   - **macOS**: `ipconfig getifaddr en0` (or check System Settings → Wi-Fi → Details)
   - **Linux**: `hostname -I | awk '{print $1}'`
   - **Windows**: `ipconfig` (look for IPv4 Address)

   Example: `192.168.1.42`

3. **Allow inbound on port 5000** (if you have a firewall):
   - **macOS**: System Settings → Network → Firewall → allow Python
   - **Linux**: `sudo ufw allow 5000/tcp`
   - **Windows**: Windows Defender Firewall → Advanced → Inbound Rules → New Rule → Port 5000

4. **On iPhone Safari**, go to: `http://192.168.1.42:5000/`

> If you get "cannot connect":
> - Make sure iPhone is on the **same WiFi** (not cellular, not guest network)
> - Some routers block device-to-device traffic (AP isolation) — try a different WiFi network
> - Try `http://<laptop-ip>:5000/api/state` directly in Safari — should return JSON `{"game_status": "no_game", "ui_state": "start"}`

---

## 2. How to add to home screen (install as PWA)

This is the **most important step** for the best experience and for save persistence.

1. **Open the game in Safari** (Option A or B above)
2. Tap the **Share button** (the square with an arrow pointing up, at the bottom of Safari on iPhone)
3. Scroll down and tap **"Add to Home Screen"** (添加至主屏幕)
4. (Optional) Edit the name — default is "三国Roguelike"
5. Tap **"Add"** in the top right
6. Go to your home screen — you'll see the ⚔️ icon
7. **Tap the icon** to launch

### What changes after install

- **No Safari chrome** (no URL bar, no toolbar)
- **Game takes the full screen** (draws under notch and home indicator via safe-area CSS)
- **App icon on home screen** (the ⚔️ icon we generated)
- **Saves are persistent** — localStorage survives app restarts, OS updates, and reboots
- **Offline app shell** — static assets (HTML, CSS, JS, icons) are cached; only the API requires the server

> **Why this matters for saves**: iOS Safari may clear localStorage for sites you haven't visited in 7+ days. Once installed as a PWA, the storage is treated as persistent.

---

## 3. How to start a new game

1. Launch the app (from home screen icon or Safari)
2. You should see the **Start Screen** with:
   - ⚔️ 三国文字Roguelike ⚔️
   - "黄巾乱世，英雄四起"
   - "开始新游戏" button (gold)
3. Tap **"开始新游戏"**
4. You should see the **Main Game Screen**:
   - Top bar: `184年1月 | 颍川` ... `散兵 | 英雄`
   - Stats bar: HP ❤️ / 士气 💪 / 体力 ⚡ / 金 💰 / 粮 🍖 / 经验 📈
   - Attributes bar: 武 ⚔️ / 智 🧠 / 名 📜 / 魅 💫 / 运 🍀
   - Narrative area (mostly empty at start)
   - Bottom nav: 📍地图 / ⏭️下月 / 📊状态 / 🏆成就 / 📜战报

If the game shows "网络错误" (network error) or a blank screen:
- Check your internet connection
- Make sure the server is running (if LAN)
- Pull down to refresh (existing pull-to-refresh)
- Force-quit and relaunch the PWA

---

## 4. How to continue a saved game

The game **auto-saves** to your iPhone after every action (the existing `localStorage` save system). To continue:

1. Launch the app
2. If you have a saved game, it should **automatically resume** at the correct year/month/location/stats
3. If it shows the Start Screen instead, your save was lost (rare; usually means localStorage was cleared)

> **Save persistence rules**:
> - ✅ Survives: app close, app restart, OS reboot, OS update
> - ✅ Survives: PWA reinstall, network outage
> - ❌ Lost: Safari browser data cleared (Settings → Safari → Clear History and Website Data)
> - ❌ Lost: iPhone erased / restored from backup
> - ❌ Lost: PWA deleted from home screen (warning: this clears localStorage on iOS)

---

## 5. How to play (quick reference)

| Action | How to do it |
|---|---|
| **Advance one month** | Tap "⏭️下月" at the bottom OR **pull down** on the narrative area |
| **Move to another city** | Tap "📍地图" → tap a connected city name |
| **Fight a battle** | When in combat, tap one of the 4 action buttons (进攻/坚守/撤退/用计). Optional: tap a skill above the actions |
| **Recruit an NPC** | When you meet an NPC (encounter or tavern), tap one of the 7 options (诚心相邀 / 以利诱之 / 晓以大义 / etc.) |
| **Buy / sell food** | When in market, tap "buy" or "sell" |
| **See the map** | Tap "📍地图" |
| **See your status** | Tap "📊状态" |
| **See achievements** | Tap "🏆成就" (swipe up the bottom sheet to see more) |
| **See run history** | Tap "📜战报" (only shows current run) |
| **Buy a skill (after death)** | On the Death Shop screen, tap a skill to buy it with fragments |
| **Reincarnate** | On the Death Shop screen, tap "转世" (resets your character; keeps karma) |
| **Get intel (NPC locations)** | When in a city, go to market → intel button (costs 20 金) |

### Touch gestures

- **Pull down on the narrative area** → advance one month (existing pull-to-refresh)
- **Swipe up on a bottom sheet** (achievements / history) → close it
- **Tap a button** → activate
- **No pinch-to-zoom** by design (set `user-scalable=no` for game UI; use the back button to dismiss modals)

---

## 6. What to look for during playtest (60-second check)

After tapping "开始新游戏", the first 60 seconds should feel like this:

1. **0-5s**: Main Game Screen appears with stats and bottom nav
2. **5-10s**: You see your starting stats (武 40, 智 30, 名 10, 魅 20, 运 30, 30 random offset)
3. **10-15s**: You tap "⏭️下月" → time advances to "184年2月", narrative updates
4. **15-30s**: You tap "📍地图" → see a list of cities, tap an adjacent one to move
5. **30-60s**: A random event, NPC encounter, or combat may trigger — read the narrative, tap an action

**If anything takes more than 60 seconds to understand, the UI needs work** — please report it.

---

## 7. What to playtest (one full death/reincarnation loop)

1. **Start a new game** at S1
2. **Tap "⏭️下月"** 5-10 times to advance
3. **Trigger an encounter** (combat or NPC) — this should appear in the narrative area
4. **Resolve the encounter** (combat: choose an action; NPC: choose an option)
5. **Move cities** at least once
6. **Buy or sell** at a market
7. **Let your character die** (HP reaches 0) OR **let the year reach 220** (game over)
8. **Death Shop** appears — buy a skill with fragments (optional)
9. **Tap "转世"** — new game starts with reincarnation karma applied
10. **Save/load test**: close the PWA (swipe up), reopen — game should resume

> **Goal**: complete steps 1-10 without crashes, save loss, or UI confusion. Target: 30-60 minutes total playtime.

---

## 8. How to report a bug

Use this template (copy-paste into Feishu DM or issue tracker):

```
## Bug report

**What I did**: [e.g. "tapped 📍地图, then tapped 洛阳"]
**What I expected**: [e.g. "moved to 洛阳, narrative updated"]
**What happened**: [e.g. "screen froze, no response"]
**iOS version**: [Settings → General → About → iOS Version, e.g. "17.4.1"]
**iPhone model**: [e.g. "iPhone 13 Pro"]
**Game state**: [year/month/location/Hold the values if visible]
**Network**: [Wi-Fi or cellular, router brand if relevant]
**Saved the bug?**: [yes/no — did the save work after the bug?]

**Screenshot**: [attach if possible]
```

### Common things to check first

| Symptom | Likely cause | Try |
|---|---|---|
| "网络错误" toast | Server offline / wrong URL | Check server is running; visit `<url>/api/state` in Safari |
| White screen | Service worker stuck | Settings → Safari → Advanced → Website Data → find the site → Delete. Then reopen |
| Buttons not responding | Tap highlight / z-index | Force-quit (swipe up) and relaunch |
| Save lost | localStorage cleared | Always install to home screen; don't clear Safari data |
| Status bar overlaps content | Not installed to PWA | Add to home screen (see Section 2) |
| Bottom home indicator overlaps nav | safe-area CSS not applied | Update to latest PWA build; force-quit and relaunch |
| Game stuck on a modal | Modal can't be dismissed | Tap outside the modal; or force-quit |

---

## 9. Quick troubleshooting (90% of issues are these)

### "I can't reach the server from my iPhone"

1. Confirm the server is running: `curl http://<server>/api/state` from a desktop browser — should return JSON
2. Confirm the iPhone is on the same network (Wi-Fi, not cellular)
3. If using a public URL (Railway / VPS), confirm HTTPS is enabled (required for service workers on iOS in production)
4. Try `<url>/api/state` directly in iPhone Safari — should return JSON

### "The app shows a white screen"

1. Force-quit the PWA (swipe up from home indicator)
2. Reopen
3. If still white: Settings → Safari → Advanced → Website Data → find the URL → Delete → reopen
4. If still white: try the URL in regular Safari (not home screen) — if it works there, the PWA install is corrupted; remove from home screen and re-add

### "The bottom of the screen is cut off / under the home indicator"

This means the PWA was installed BEFORE the safe-area CSS was added. Remove and re-add:
1. Long-press the icon → Remove App → Delete
2. Open the URL in Safari again
3. Re-add to home screen

### "The save disappeared"

This means localStorage was cleared. Causes:
- You cleared Safari history & website data
- You removed the PWA from home screen
- The PWA was inactive for >7 days without being installed to home screen

To prevent: always install to home screen (one-time action).

---

## 10. iPhone-specific features

| Feature | Status | Note |
|---|---|---|
| Home screen install | ✅ | Add to Home Screen via Share button |
| Fullscreen standalone | ✅ | display: standalone in manifest |
| Status bar overlay | ✅ | black-translucent; safe-top padding |
| Notch / Dynamic Island safe area | ✅ | viewport-fit=cover + env(safe-area-inset-*) |
| Home indicator safe area | ✅ | env(safe-area-inset-bottom) on bottom-nav |
| Offline app shell | ✅ | Service Worker caches static assets |
| Offline game | ❌ | Game still requires server (deferred to v2) |
| Push notifications | ❌ | iOS Safari limitation (deferred) |
| Haptic feedback | ❌ | iOS Safari doesn't support Web Vibration API |
| Background sync | ❌ | iOS Safari limitation (deferred) |

---

## 11. What's NOT in this MVP (deferred to v2)

- ❌ Native iOS app (App Store)
- ❌ Push notifications
- ❌ Offline game mode (server required)
- ❌ Haptic feedback
- ❌ Background sync
- ❌ Cloud save sync (local only)
- ❌ Multiple save slots (one save slot only)
- ❌ Replay/share functionality

---

## 12. Contact for issues

Reply in this Feishu DM with the bug report template (Section 8). For the developer:
- Engine / game logic issues → separate from PWA, will not block MVP
- PWA / iOS / save issues → report here, will fix in v1.1

---

**Enjoy the game! ⚔️ 三国文字Roguelike ⚔️**
