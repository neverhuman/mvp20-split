#!/usr/bin/env bash
# 05_build.sh — pdflatex ×2 (for cross-refs / last-page counter)
set -euo pipefail
cd /home/ubuntu/amphora/reports/portfolio-status-2026-08-03
echo "[$(date -Iseconds)] pdflatex pass 1 …"
pdflatex -halt-on-error -interaction=nonstopmode main.tex >/tmp/build_pass1.log 2>&1 || {
    echo "== pdflatex pass 1 FAILED — tail of log =="
    tail -60 /tmp/build_pass1.log
    exit 1
}
echo "[$(date -Iseconds)] pdflatex pass 2 …"
pdflatex -halt-on-error -interaction=nonstopmode main.tex >/tmp/build_pass2.log 2>&1 || {
    echo "== pdflatex pass 2 FAILED — tail of log =="
    tail -60 /tmp/build_pass2.log
    exit 1
}
mv -f main.pdf portfolio-status-2026-08-03.pdf
echo "[$(date -Iseconds)] built portfolio-status-2026-08-03.pdf ($(stat -c %s portfolio-status-2026-08-03.pdf) B)"
pdfinfo portfolio-status-2026-08-03.pdf | head -20
