#!/usr/bin/env python3
"""render_prompt.py TEMPLATE : print the prompt with {{NAME}} placeholders replaced literally from environment variables.
Exits 2 (printing nothing) if the file is unreadable, a placeholder in the template has no non-empty value, or the result is empty."""
import os, re, sys
try:
    text = open(sys.argv[1], encoding="utf-8").read()
except OSError as e:
    sys.exit(f"cannot read prompt template: {e}")
missing = sorted({n for n in re.findall(r"\{\{([A-Z_]+)\}\}", text) if not os.environ.get(n, "").strip()})
leftover = re.sub(r"\{\{[A-Z_]+\}\}", "", text)
if "{{" in leftover or "}}" in leftover or "{{{" in text or "}}}" in text:
    sys.exit("malformed placeholder in the template (expected {{UPPER_CASE_NAME}})")
if missing:
    sys.exit("set these environment variables to your project documents (see prompts/README.md): " + ", ".join(missing))
out = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: os.environ[m.group(1)], text).strip()
if not out:
    sys.exit("prompt is empty")
print(out)
