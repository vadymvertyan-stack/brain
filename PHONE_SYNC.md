# Brain Phone Sync Guide
=====================

## Option 1: Obsidian + Git (Recommended)

### Android
1. Install **Obsidian** from Play Store
2. Install **GitHub Desktop** or **MTgit** (Git client)
3. Clone repo: `https://github.com/vadymvertyan-stack/brain.git`

### iOS
1. Install **Obsidian** from App Store
2. Install **Working Copy** (Git client - paid but excellent)
3. Clone repo in Working Copy
4. Open in Obsidian

### Obsidian Git Plugin Setup
1. Install Obsidian
2. Settings → Community plugins → Disable Safe mode
3. Install **Git** plugin by @denolehov
4. Configure:
   ```
   Repository: vadymvertyan-stack/brain
   Branch: master
   Auto-commit: true
   Auto-push: true (every 5 min)
   ```

---

## Option 2: Syncthing (Simpler)

### Install on both devices:
- Android: Syncthing from F-Droid/Play Store
- PC: https://syncthing.net/

### Setup:
1. Add device ID from Settings → ID
2. Share folder between devices
3. Changes sync automatically

---

## Option 3: iCloud / Google Drive

### Quick setup:
1. Make Brain folder sync to cloud
2. Access from phone's cloud app

**Note:** Not recommended - loses Git versioning

---

## Quick Start (Obsidian Recommended)

### Step 1: Get the app
- **iOS**: https://apps.apple.com/app/obsidian/id1557175442
- **Android**: https://play.google.com/store/apps/details?id=md.obsidian

### Step 2: Clone repo
```bash
# Using Termux (Android)
apt install git
git clone https://github.com/vadymvertyan-stack/brain.git

# Or using Working Copy (iOS)
```

### Step 3: Open in Obsidian
1. Open folder as vault
2. Install Git plugin
3. Enable auto-sync

---

## Status

| Device | Status | Method |
|--------|--------|--------|
| PC | ✅ Ready | `brain_autosync.py` |
| VPS | ✅ Ready | Cron every 5 min |
| Phone | ⏳ Setup required | Obsidian + Git |

---

## Commands

### Manual sync from phone terminal:
```bash
cd ~/brain
git add -A
git commit -m "update"
git push
```
