LATEX ?= pdflatex
BIBTEX ?= bibtex
TEXFLAGS = -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape

.PHONY: all check clean
all: paper.pdf

paper.pdf: paper.tex references.bib tables.tex figures/prefix_timing.pdf figures/contrasts.pdf figures/release_examples.pdf
	$(LATEX) $(TEXFLAGS) paper.tex
	$(BIBTEX) paper
	$(LATEX) $(TEXFLAGS) paper.tex
	$(LATEX) $(TEXFLAGS) paper.tex

check: paper.pdf
	python3 scripts/validate_manuscript.py --root .

clean:
	rm -f paper.aux paper.bbl paper.blg paper.log paper.out paper.toc paper.fls paper.fdb_latexmk
