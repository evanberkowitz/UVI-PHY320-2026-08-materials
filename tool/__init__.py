"""Tooling for preparing and publishing course materials.

Mostly private.  Three files are distributed, because students receive a
repository that audits itself: `tool/__init__.py`, `tool/markers.py` (so the
marker grammar travels with the materials it scrubbed) and `tool/audit.py`
(so the public repository's GitHub Action can re-run the leak check on every
push).  They are copied verbatim, never scrubbed.

Everything else -- `publish.py`, `scrub.py`, `notebook.py`, `meta.py` -- is
absent from the publish allowlist and never reaches the public materials
repository.
"""
