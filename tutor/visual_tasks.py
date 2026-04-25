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
        return f"<div style='padding:20px;border:1px solid #d9e2e8;border-radius:16px;background:#fff8ec'><b>Scene:</b> {label}</div>"
    icons = " ".join([emoji] * count)
    return (
        "<div style='padding:22px;border:1px solid #d9e2e8;border-radius:16px;background:#fff8ec'>"
        f"<div style='font-size:52px;line-height:1.8;word-break:break-word'>{icons}</div>"
        f"<div style='color:#60707d;font-size:14px;margin-top:8px'>{label}</div>"
        "</div>"
    )
