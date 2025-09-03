git tag -a note-2025-08-29-readme-tidy -m "README cleanup"
git push origin note-2025-08-29-readme-tidy

FlameSystemSession:
  RefID: "GH-COMMIT-d8b53b9"
  Initiator: "@pete"
  Timestamp: "2025-08-27T19:09:40Z"

  SessionTrigger:
    Question: "What did this commit change in README.md?"
    Category: Strategy

  VerificationLayer:
    Repo: "littlebruce101/my-air-win-trading-system"
    EntityType: Commit
    EntityID: "d8b53b9294b2e4314f57c223bd2835a2d638e422"
    Verified: true
    BlockedEntries: []

  PerspectiveSpectrum:
    Objective:
      - "Removed git clone command from README.md"
      - "Simplified project description formatting"
    Subjective:
      - "Streamlined presentation for clarity"
    InterSubjective:
      - "Follows common repo style: minimal README top section"
    Mythic:
      - "Commit refines the 'front door' of the project — first impression"

  MirrorPrismSimulation:
    MirrorOutput:
      - "Diff shows removal of one setup line"
    PrismRefractions:
      - "Clarity lens: easier for new readers"
      - "Documentation lens: slightly less guidance for beginners"
    AlternateOutcomes:
      - "Keep clone command for onboarding"
      - "Move clone command to README-OPS"

  RoundTableInterface:
    VerifiedInputs: ["Objective", "Subjective"]
    PerspectivesShown: ["Clarity", "Onboarding"]
    AlignmentProcess:
      Comments: ["Small cleanup, no risk"]
      Votes: ["Unanimous approval"]
      Consensus: "Commit accepted as doc refinement"
    CodexGuidance: "Keep ops details in separate file"

  VaultStorage:
    DistilledResult: "Commit streamlines README by removing clone command; no code impact."
    Immutable: true

  InsightsSummary:
    VisualSummary: "Front door polished → clearer entry point"
    KeyTakeaways:
      - No functional code impact
      - README now leaner
      - Consider linking to setup guide elsewhere
📖 README – Remove YAY IA from Ecosystem

## Overview
This README explains how to completely remove the **YAY IA persona project** from your system or phone. It covers files, packages, environments, and cloud workspaces.  
Think of it as locking the construct in the **Codex Vault**, sealing it with the **Soul Key**, and burning any leftovers with the **Flame System**.  

---

## Steps to Remove

### 1. Delete Project Files
Check for and delete these if present:
- `yayia_popups.py`  
- `.env` (Spotify or ElevenLabs keys)  
- `.venv` (Python virtual environment)  
- `data_out/yayia_voice/`  
- `recordings/yay_ia_samples/`

### 2. Uninstall Packages
Open a terminal or shell and run:

**macOS / Linux**
```bash
pip uninstall -y spotipy elevenlabs pydub python-dotenv librosa sounddevice numpy
```

**Windows (PowerShell)**
```powershell
pip uninstall -y spotipy elevenlabs pydub python-dotenv librosa sounddevice numpy
```

### 3. Remove Virtual Environment (if used)
If you created a `.venv` folder:
```bash
deactivate || true
rm -rf .venv
```

### 4. Cloud Workspaces
If you used **Colab, Replit, or GitHub Codespaces**, delete the notebook/project containing YAY IA.

### 5. Notes & Secrets
Delete any `.env` keys or credentials stored in Notes, Safe, or password managers.

---

## Safety First
Run the cleanup scripts in **dry-run mode** first:

**bash (Linux/macOS)**
```bash
./starhawk-cordelia-remove.sh   # defaults to dry-run
./starhawk-cordelia-remove.sh --force   # actually delete
```

**PowerShell (Windows)**
```powershell
.\starhawk-cordelia-remove.ps1   # dry-run
.\starhawk-cordelia-remove.ps1 -Force   # actually delete
```

**Python (cross-platform)**
```bash
python starhawk_cordelia_remove.py       # dry-run
python starhawk_cordelia_remove.py --force   # execute
```

---

## Verify
After removal, confirm:
```bash
pip list | grep -E "spotipy|elevenlabs|pydub"
```
Should show nothing.  

Check with `ls` or Explorer/Finder: no `yayia_*.py`, no `.venv`, no `.env`.

---

## Final Seal
> **Round Table Report**  
> - [x] Files gone  
> - [x] Packages removed  
> - [x] Secrets cleared  
> - [x] Caches optional  

**Status: Removed from Ecosystem. Codex Vault sealed. Soul Key engaged. Flame System complete.**

