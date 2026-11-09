"""Parse Shweta's email replies. The scheduled Claude run reads the Gmail thread
and passes the reply body here, so the decision logic is deterministic and tested."""
from __future__ import annotations

import re

_QUOTE_START = re.compile(r"^(on .+wrote:|-----original message|from: |>)", re.I)


def strip_quoted(body: str) -> str:
    """Keep only what Shweta typed above the quoted original email."""
    lines = []
    for line in body.replace("\r\n", "\n").split("\n"):
        if _QUOTE_START.match(line.strip()):
            break
        lines.append(line)
    return "\n".join(lines).strip()


def parse_reply(body: str) -> dict:
    """Returns {"decision": approve|skip|edit|unclear, "text": edited text or None, "note": str}.

    Accepted forms (case-insensitive, first word decides):
      APPROVE / APPROVED / YES / OK / GO                -> approve
      SKIP / NO / REJECT                                -> skip
      EDIT <newline> full replacement post text         -> edit (needs re-check, then approval)
      APPROVE WITH EDIT <newline> full replacement text -> approve the edited text as-is
    Anything else is 'unclear' and triggers a clarification email; never a publish.
    """
    text = strip_quoted(body)
    if not text:
        return {"decision": "unclear", "text": None, "note": "empty reply"}
    first, _, rest = text.partition("\n")
    head = first.strip().lower().rstrip(".!:")
    rest = rest.strip()

    if re.fullmatch(r"approve(d)?\s+with\s+edits?", head):
        if len(rest.split()) < 20:
            return {"decision": "unclear", "text": None, "note": "approve-with-edit but no post text below"}
        return {"decision": "approve", "text": rest, "note": "approved with Shweta's own edit"}
    if re.fullmatch(r"edits?", head):
        if len(rest.split()) < 20:
            return {"decision": "unclear", "text": None, "note": "EDIT without replacement text; treat as change request"}
        return {"decision": "edit", "text": rest, "note": "replacement text supplied"}
    if re.fullmatch(r"(approve(d)?|yes|ok(ay)?|go|publish)(\s+it)?", head):
        return {"decision": "approve", "text": None, "note": rest or None}
    if re.fullmatch(r"(skip|no|reject(ed)?|don'?t post)", head):
        return {"decision": "skip", "text": None, "note": rest or None}
    return {"decision": "unclear", "text": None, "note": first[:200]}
