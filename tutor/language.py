from __future__ import annotations

NUMBER_WORDS = {
    "en": {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "bigger", "between", "plus", "minus"},
    "fr": {"zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf", "vingt", "plus", "moins"},
    "kin": {"zeru", "rimwe", "kabiri", "gatatu", "kane", "gatanu", "gatandatu", "karindwi", "umunani", "icyenda", "icumi", "cumi", "rimwe", "ebyiri", "eshatu", "ine", "eshanu", "esheshatu", "zirindwi", "umunani", "icyenda", "wongeyeho", "ukuyeho", "anganahe"},
}


def detect_language(text: str) -> str:
    clean = (text or "").strip().lower()
    if not clean:
        return "unknown"
    scores = {}
    for language, words in NUMBER_WORDS.items():
        scores[language] = sum(1 for token in clean.replace("-", " ").split() if token in words)
    best = max(scores, key=scores.get)
    non_zero = [lang for lang, score in scores.items() if score > 0]
    if len(non_zero) >= 2:
        return "mix"
    if scores[best] == 0:
        return "unknown"
    return best


def choose_reply_language(preferred: str, detected: str) -> str:
    preferred = (preferred or "kin").lower()
    if detected in {"en", "fr", "kin"}:
        return detected
    if detected == "mix":
        return preferred if preferred in {"en", "fr", "kin"} else "kin"
    return preferred if preferred in {"en", "fr", "kin"} else "kin"


def localized_stem(item: dict, language: str) -> str:
    if language == "fr" and item.get("stem_fr"):
        return item["stem_fr"]
    if language == "kin" and item.get("stem_kin"):
        return item["stem_kin"]
    return item.get("stem_en", "")
