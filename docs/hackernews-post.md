# Show HN: I built a decluttering app for my ADHD brain

**Link:** https://github.com/Pastorsimon1798/DECLuTTER-AI

I have ADHD. My desk has three half-empty coffee cups, a nest of cables, and papers I meant to file months ago. Every productivity app I tried just showed me the mess in higher resolution. None helped me *decide* what to do with it.

So I built DECLuTTER AI — an open-source Flutter app that turns a clutter photo into simple, time-boxed decisions.

**How it works:**
1. Snap a photo of your desk/closet/dresser
2. On-device AI (ONNX Runtime) groups items by category
3. Tap Keep/Donate/Trash/Relocate/Maybe for each group
4. 10-minute sprint timer keeps you focused
5. Session summary + CSV export + resale valuation

**ADHD-first design:**
- One primary action per screen (no decision paralysis)
- Large buttons, visible progress, undo everything
- Shame-free language (never "mess" or "junk")
- Energy modes: 2 min / 5 min / 10 min / full listing sprint

**Privacy:** All detection is on-device. Photos never leave your phone unless you explicitly opt in per group.

**Stack:** Flutter + Dart + FastAPI + Python + ONNX Runtime

MIT licensed. Contributors welcome — especially if you have ADHD and want to share feedback.

---

**Posting tips:**
- Post on Tuesday or Wednesday, 8–10 AM PT
- Respond to every comment within the first 2 hours
- Be honest about what's rough / MVP / not working yet
- HN loves technical details — mention ONNX, FastAPI, the decision algorithm
