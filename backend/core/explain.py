import html


def build_explanation(rule_hits, model_conf=None, duplicate_score=None):
    bullets = []
    if rule_hits:
        bullets.append(f"{len(rule_hits)} suspicious pattern(s) detected in this posting.")
        for hit in rule_hits:
            bullets.append(f"- {hit.name}: {hit.explanation}")
    else:
        bullets.append("No known scam red-flag patterns matched this posting.")
    if model_conf is not None:
        bullets.append(
            f"The ML model rates this posting as {model_conf * 100:.0f}% likely to be a scam."
        )
    if duplicate_score is not None:
        bullets.append(
            f"This posting is {duplicate_score * 100:.0f}% similar to a known scam template."
        )
    return {"summary": bullets[0] if bullets else "", "bullet_points": bullets}


def highlight_flags(text, rule_hits, marker="<mark style='background:#ffe3e3;color:#b00020'>{}</mark>"):
    pieces = []
    for hit in rule_hits:
        pieces.extend(hit.evidence)
    pieces = sorted(set(pieces), key=len, reverse=True)
    escaped = html.escape(text)
    for piece in pieces:
        if not piece:
            continue
        escaped = escaped.replace(html.escape(piece), marker.format(html.escape(piece)))
    return escaped
