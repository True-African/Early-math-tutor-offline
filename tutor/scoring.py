from __future__ import annotations

NUMBER_MAP = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twewenti": 20,
    "un": 1,
    "deux": 2,
    "trois": 3,
    "quatre": 4,
    "cinq": 5,
    "six": 6,
    "sept": 7,
    "huit": 8,
    "neuf": 9,
    "dix": 10,
    "onze": 11,
    "douze": 12,
    "treize": 13,
    "quatorze": 14,
    "quinze": 15,
    "seize": 16,
    "vingt": 20,
    "rimwe": 1,
    "kabiri": 2,
    "gatatu": 3,
    "kane": 4,
    "gatanu": 5,
    "gatandatu": 6,
    "karindwi": 7,
    "umunani": 8,
    "icyenda": 9,
    "icumi": 10,
    "eshatu": 3,
    "esheshatu": 6,
    "ebyiri": 2,
    "ine": 4,
    "eshanu": 5,
    "zirindwi": 7,
}


def normalize_response(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    text = text.replace("-", " ")
    if text in NUMBER_MAP:
        return NUMBER_MAP[text]
    tokens = text.split()
    if len(tokens) == 1:
        return NUMBER_MAP.get(tokens[0])
    return None


def score_response(item: dict, selected_value: str | int | None) -> tuple[bool, int | None]:
    parsed = normalize_response(selected_value)
    correct = parsed == int(item.get("answer_int"))
    return correct, parsed
