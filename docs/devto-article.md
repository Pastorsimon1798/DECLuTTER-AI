# Building an ADHD-First App with Flutter: How I Turned Clutter into Code

> This is the story of how I built DECLuTTER AI — an open-source decluttering assistant designed specifically for neurodivergent brains.

---

## The Problem

I have ADHD. My desk looks like a tornado hit a thrift store. Cables everywhere. Papers I meant to file three months ago. Three half-empty coffee cups.

Every "productivity" app I tried made me feel worse.

They would identify the mess. Count the items. Even suggest "systems." But none of them helped me **decide what to do** with any of it. They just showed me the problem in higher resolution.

The real blocker wasn't seeing the clutter. It was the **decision paralysis**.

*Is this cable worth keeping? Should I donate this book? What if I need that charger someday?*

By the time I finished debating one item, I was exhausted and the rest of the desk was still there, judging me.

## The Insight

What I needed wasn't a scanner. I needed a **decision engine** wrapped in a **time box**.

ADHD brains work best with:
- **One clear action at a time**
- **Visible progress** (not hidden in menus)
- **An escape route** (so it doesn't feel like a trap)
- **No shame** (seriously, never call it "junk")

So I built exactly that.

---

## Meet DECLuTTER AI

[⭐ Star on GitHub](https://github.com/Pastorsimon1798/DECLuTTER-AI)

DECLuTTER AI is a Flutter app + FastAPI backend that turns a photo of clutter into simple, time-boxed decisions.

### How it works

1. **Snap a photo** of any cluttered zone (desk, closet, dresser)
2. **AI groups items** by category — cables, books, clothing, electronics
3. **Tap a decision** for each group: Keep · Donate · Trash · Relocate · Maybe
4. **10-minute sprint timer** keeps you focused without overwhelm
5. **Session summary** shows what you decided + estimated resale value + CSV export

All object detection happens **on-device** via ONNX Runtime. Your photos never leave your phone unless you explicitly opt in.

---

## Why Flutter?

I chose Flutter because:
- **One codebase** → iOS + Android from a single Dart project
- **Camera plugin** is mature and well-documented
- **TensorFlow Lite + ONNX Runtime** both have Flutter packages
- **Fast iteration** — hot reload means I can test UI changes in seconds

The backend is FastAPI (Python) because Python's ML ecosystem is unbeatable. The Flutter app never calls AI providers directly — all vision analysis goes through the backend adapter.

---

## ADHD-First Design Principles

Every screen follows these rules:

### 1. One Primary Action
No decision paralysis. When you open the app, the biggest button says **"Take Photo."** That's it.

### 2. Large Touch Targets
Minimum 48dp for every button. Fat-finger friendly.

### 3. Visible Progress
"3/5 groups decided" is always on screen. You always know how far you've come.

### 4. Undo Everything
Every decision can be reversed. No commitment anxiety.

### 5. Shame-Free Language
We never say "mess," "junk," "lazy," or "failed." The app says "zone," "items," and "not worth your energy today."

### 6. Energy Modes
- **2 minutes** → one easiest clear action only
- **5 minutes** → top 1 sellable item
- **10 minutes** → top 3 sellable items
- **Can list today** → full listing sprint

---

## The Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Mobile App | Flutter / Dart | Cross-platform, fast iteration |
| On-Device ML | ONNX Runtime | Privacy-first, works offline |
| ML Fallback | TensorFlow Lite | Broader model compatibility |
| Backend | FastAPI / Python | Async, typed, great ML ecosystem |
| State Management | ChangeNotifier → Riverpod | Testable, feature-isolated |
| Local Storage | SharedPreferences → SQLite | Offline session history |
| API Client | Dio + Firebase Auth | Secure token handling |

---

## Privacy by Design

Most AI apps upload your photos to the cloud by default. We do the opposite:

- **Object detection runs on-device** via ONNX Runtime
- **EXIF metadata is stripped** before any upload
- **Cloud features require explicit per-group opt-in**
- **Session summaries stay local** unless you choose to sync

The backend only sees photos if you toggle "Explain" on a specific group — and even then, it receives a cropped group image, not the full photo.

---

## Open Source

DECLuTTER AI is MIT licensed.

I believe ADHD tools should be accessible, not locked behind paywalls. The full source is on GitHub:

👉 [github.com/Pastorsimon1798/DECLuTTER-AI](https://github.com/Pastorsimon1798/DECLuTTER-AI)

**Contributors welcome.** Whether you code, design, write docs, or just have ADHD and want to share feedback — you're wanted here.

---

## What's Next

- [x] Photo capture + on-device detection
- [x] Decision cards + 10-min sprint timer
- [x] Valuation + CSV export
- [ ] SQLite persistence for session history
- [ ] eBay marketplace integration (list items directly)
- [ ] AI-powered item analysis (backend vision model)
- [ ] iOS/Android app store release

---

## Try It

```bash
git clone https://github.com/Pastorsimon1798/DECLuTTER-AI.git
cd DECLuTTER-AI/app
flutter pub get
flutter run
```

Or just [star the repo](https://github.com/Pastorsimon1798/DECLuTTER-AI) to follow along.

---

*If you have ADHD and struggle with clutter: you're not lazy, and you're not broken. Your brain just needs a different interface. I built this for both of us.*
