from __future__ import annotations

import html


EMOJI_MAP = {
    "apples": "🍎",
    "goats": "🐐",
    "beads": "🔵",
    "birds": "🐦",
    "drums": "🥁",
    "balls": "⚽",
    "mangoes": "🥭",
    "books": "📘",
    "beans": "🫘",
    "oranges": "🍊",
    "cups": "🥤",
}


# The baseline visual-grounding path uses the rendered scene id to build a countable visual task.
def infer_count_from_visual(visual_id: str) -> int | None:
    if not visual_id:
        return None
    tail = visual_id.split("_")[-1]
    return int(tail) if tail.isdigit() else None


def render_visual_html(item: dict) -> str:
    visual_id = item.get("visual", "")
    count = infer_count_from_visual(visual_id)
    kind = visual_id.split("_")[0] if visual_id else "objects"
    emoji = EMOJI_MAP.get(kind, "🔷")
    label = html.escape(visual_id.replace("_", " "))
    if count is None or count > 12:
        return f"<div style='padding:16px;border:1px solid #d9e2e8;border-radius:12px;background:#fff'><b>Scene:</b> {label}</div>"
    icons = " ".join([emoji] * count)
    return (
        "<div style='padding:16px;border:1px solid #d9e2e8;border-radius:12px;background:#fff'>"
        f"<div style='font-size:34px;line-height:1.6'>{icons}</div>"
        f"<div style='color:#60707d;font-size:13px;margin-top:6px'>{label}</div>"
        "</div>"
    )
