set -euo pipefail
outfile=yayia_cleanliness_report.md
echo "# YAY IA Removal Report" > "$outfile"
echo "Generated (UTC): $(date -u)" >> "$outfile"
echo -e "\n## Patterns scan" >> "$outfile"
pat='yay[ _-]?ia|yayia|yay_ia|yayia_voice|elevenlabs|spotipy|pydub|librosa|sounddevice|yayia_popups\.py|data_out/yayia_voice|recordings/yay_ia_samples'
grep -RniE "$pat" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ . | tee -a "$outfile" || echo "No matches" | tee -a "$outfile"
echo -e "\n## .env tracking" >> "$outfile"
if git ls-files --error-unmatch .env >/dev/null 2>&1; then echo ".env is tracked! ❌" | tee -a "$outfile"; else echo ".env not tracked. ✅" | tee -a "$outfile"; fi
echo -e "\n## requirements.txt scan" >> "$outfile"
if [ -f requirements.txt ]; then grep -E "elevenlabs|spotipy|pydub|librosa|sounddevice" requirements.txt >> "$outfile" || echo "No banned deps in requirements.txt" >> "$outfile"; else echo "requirements.txt not found" >> "$outfile"; fi
echo -e "\n## Done" >> "$outfile"
cat "$outfile"

# macOS/Linux
unzip yayia_post_removal_kit.zip -d .
git checkout -b chore/guard-yayia-removal
git add -A
git commit -m "Add guard + docs after YAY IA removal"
git push -u origin chore/guard-yayia-removal