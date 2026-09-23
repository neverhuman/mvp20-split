#!/usr/bin/env python3
"""Deterministic .docx -> Markdown renderer for the founder directive.

No network, no new dependency: a .docx is a zip of XML. We walk word/document.xml
in document order, emitting paragraphs and table rows. Deterministic by
construction (no dict iteration over unordered data, no timestamps), so the
rendered .md has a stable sha256 that receipts can cite.
"""
import re, sys, zipfile

SRC, DST = sys.argv[1], sys.argv[2]

xml = zipfile.ZipFile(SRC).read("word/document.xml").decode("utf-8", "replace")

# Heading level comes from the paragraph style (Heading1/2/3 or Title).
def para_text(block):
    b = re.sub(r"<w:tab[^>]*/>", "\t", block)
    b = re.sub(r"<w:br[^>]*/>", "\n", b)
    t = re.sub(r"<[^>]+>", "", b)
    for a, b2 in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                  ("&quot;", '"'), ("&#39;", "'"), ("&apos;", "'")):
        t = t.replace(a, b2)
    return t.strip()

def style_of(block):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', block)
    return m.group(1) if m else ""

out, seen_title = [], False
# Walk tables and paragraphs in document order.
for m in re.finditer(r"<w:tbl[ >].*?</w:tbl>|<w:p[ >].*?</w:p>|<w:p/>", xml, re.S):
    chunk = m.group(0)
    if chunk.startswith("<w:tbl"):
        rows = []
        for r in re.finditer(r"<w:tr[ >].*?</w:tr>", chunk, re.S):
            # A cell holds its own <w:p> runs; join them with a space so adjacent
            # sentences don't fuse into one unreadable word ("documentSection A").
            cells = []
            for c in re.findall(r"<w:tc[ >].*?</w:tc>", r.group(0), re.S):
                paras = [para_text(p) for p in re.findall(r"<w:p[ >].*?</w:p>|<w:p/>", c, re.S)]
                cells.append(" ".join(p for p in paras if p) or para_text(c))
            cells = [c.replace("\n", " ").replace("|", "\\|") for c in cells]
            if any(cells):
                rows.append("| " + " | ".join(cells) + " |")
        if rows:
            out.append("")
            out.append(rows[0])
            ncol = rows[0].count("|") - 1
            out.append("|" + "---|" * max(1, ncol))
            out.extend(rows[1:])
            out.append("")
        continue
    txt = para_text(chunk)
    if not txt:
        if out and out[-1] != "":
            out.append("")
        continue
    st = style_of(chunk)
    if st.startswith("Title") or (not seen_title and txt.isupper() and len(txt) < 80):
        out.append(f"# {txt}"); seen_title = True
    elif st.startswith("Heading1"):
        out.append(f"## {txt}")
    elif st.startswith("Heading2"):
        out.append(f"### {txt}")
    elif st.startswith("Heading3"):
        out.append(f"#### {txt}")
    elif st.startswith("ListParagraph"):
        out.append(f"- {txt}")
    else:
        out.append(txt)

# collapse runs of blank lines
body, prev_blank = [], False
for line in out:
    blank = (line == "")
    if blank and prev_blank:
        continue
    body.append(line); prev_blank = blank

text = "\n".join(body).strip() + "\n"
open(DST, "w").write(text)
print(f"wrote {DST}: {len(text)} chars, {text.count(chr(10))} lines")
