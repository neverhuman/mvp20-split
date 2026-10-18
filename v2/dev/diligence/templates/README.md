# Amphora publication templates

`amphora_brand.tex` and `amphora_note.tex` define a small shared Letter/11pt publication starting point. They are templates, not completed investor artifacts. No compilation pass is asserted by their presence. No shell escape is required.

Future assembly reads `brand_tokens.json` and approved `claims.json`, validates source selectors/qualifiers, escapes TeX special characters and emits `generated_body.tex`. The final generator must derive colors/metadata from tokens rather than maintaining two manual copies. The scaffold comments identify the present mirrored values; automatic token-to-TeX synchronization remains a DD-050 qualification item.

The two-page brief must use explicit page budgets and at least 11pt body. The systems note targets six pages. All pages must be rendered/reviewed, citations and links checked, embedded fonts verified and final digests recorded. Never copy the existing PLGA paper into this template or change its scientific formatting/results as an incidental build.
