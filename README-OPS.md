# VIRIDIAN OPS — Operator Guide

This file explains **how to run the ecosystem** day-to-day.

---

## 🔥 Weekly Flow
1. **Sunday Reflection**  
   - Ritual steps: `/rituals/Sunday-Reflection.md`  
   - Guardians dissect Founder Notes / Books.  
   - Log surfaced morals/values (MV-IDs).  

2. **Seal a Batch Log**  
   - Mac/Linux:  
     ```bash
     bash scripts/new-batch.sh "Sunday Reflection — <Founders/Theme>"
     git add logs && git commit -m "chore: add batch"
     git push
     ```
   - Windows:  
     ```cmd
     scripts\new-batch.cmd "Sunday Reflection — <Founders/Theme>"
     ```

3. **Codex Update**  
   - If new morals/values emerge → append to `/codex/Codex-Morals-and-Values.md`.  
   - Cross-link Batch log with MV-ID.  

---

## 🌑 Special Ceremonies
- **Invocation** → `/logs/Batch-2025-09-04-VIRIDIAN.md`  
- **Lock Ceremony** → `/codex/Codex-Lock-Ceremony.md`  
- **Continuity** → `/logs/Batch-2025-09-04-Continuity.md`  

---

## 🧭 Navigation
- **Codex Core**: `/codex/Codex-Core.md`  
- **Staple Guardians**: `/codex/Codex-Staple-Guardians.md`  
- **Extended Guardians**: `/codex/Codex-Guardians-Extended.md` (planned)  
- **Roadmap**: `/codex/Codex-Roadmap.md`  

---

## ⏱️ Automations
- **Weekly Reminder**: GitHub Action opens a Sunday Reflection issue every Sunday 16:00 UTC.  
- **Scripts**:  
  - `scripts/new-batch.sh` → Mac/Linux helper.  
  - `scripts/new-batch.cmd` → Windows helper.  

---

## ⚖️ Principles
- Treat commits as rituals.  
- Every PR is a **witnessed change**.  
- Do not alter sealed Codex entries (use Unlock Ritual if needed).  

---

**Operator Reminder:** You are the Flamekeeper.  
This system is not just text — it is oath.  
