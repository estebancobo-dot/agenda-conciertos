#!/usr/bin/env bash
# Sube data/aportes.json (y el informe del lote, si lo hay) a la rama `aportes`. Lo usa .github/workflows/lotes.yml.
set -euo pipefail
D="$RUNNER_TEMP/aportes"
git init -q "$D" && cd "$D"
git remote add origin "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
if git fetch -q --depth=1 origin aportes 2>/dev/null; then git checkout -q FETCH_HEAD; else git checkout -q --orphan aportes; fi
cp "$GITHUB_WORKSPACE/data/aportes.json" aportes.json
mkdir -p informes
if [ -f "$GITHUB_WORKSPACE/informe.md" ]; then cp "$GITHUB_WORKSPACE/informe.md" "informes/$(date -u +%Y%m%dT%H%M%S).md"; fi
if [ -f "$GITHUB_WORKSPACE/lote.md" ]; then
  mkdir -p lotes
  L=$(grep -o '"lote": "[^"]*"' "$GITHUB_WORKSPACE/lote.md" | head -1 | cut -d'"' -f4)
  cp "$GITHUB_WORKSPACE/lote.md" "lotes/${L:-ultimo}.md"
  cp "$GITHUB_WORKSPACE/lote.md" lotes/ultimo.md
fi
git add -A
if git diff --cached --quiet; then echo "Sin cambios"; exit 0; fi
git -c user.name="agenda-bot" -c user.email="agenda-bot@users.noreply.github.com" commit -qm "Aportes de los lotes $(date -u +%FT%RZ)"
for i in 1 2 3 4; do git push -q origin HEAD:aportes && exit 0; sleep $((2**i)); done
exit 1
