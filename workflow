# Create the workflow
mkdir -p .github/workflows
cat > .github/workflows/guard-yayia.yml <<'YML'
name: Guard YAY IA references
on:
  pull_request:
    branches: [ "**" ]
  push:
    branches: [ main, master, develop ]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Fail if .env is tracked
        run: |
          if git ls-files --error-unmatch .env >/dev/null 2>&1; then
            echo "::error file=.env::.env is tracked in git"; exit 1; fi
      - name: Scan for forbidden patterns
        run: |
          set -e
          PATTERN='yay[ _-]?ia|yayia|yay_ia|yayia_voice|elevenlabs|spotipy|pydub|librosa|sounddevice|yayia_popups\.py|data_out/yayia_voice|recordings/yay_ia_samples'
          if grep -RniE "$PATTERN" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ --exclude-dir=.github .; then
            echo "::error::Forbidden pattern found (see above)"; exit 1
          else
            echo "No forbidden patterns found."
          fi
YML

# Commit & push a PR branch
git checkout -b chore/guard-yayia-removal
git add .github/workflows/guard-yayia.yml
git commit -m "Add CI guard after YAY IA removal"
git push -u origin chore/guard-yayia-removal