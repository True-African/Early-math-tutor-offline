from __future__ import annotations

import json
from pathlib import Path

from tutor import SKILLS
from tutor.language import TERM_OVERRIDES


AGE_BANDS = ["5-6", "6-7", "7-8", "8-9"]

KIN_COUNT_WORDS = {
    "pome": "zingahe",
    "ihene": "zingahe",
    "amasaro": "angahe",
    "inyoni": "zingahe",
    "ingoma": "zingahe",
    "imipira": "ingahe",
    "imyembe": "ingahe",
    "ibitabo": "bingahe",
    "ibishyimbo": "bingahe",
    "amacunga": "angahe",
    "ibikombe": "bingahe",
    "bisikiti": "zingahe",
    "inyanya": "zingahe",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def localized_term(term: str, language: str) -> str:
    return TERM_OVERRIDES.get(language, {}).get(term, term)


def kin_count_word(noun: str) -> str:
    return KIN_COUNT_WORDS.get(noun, "zingahe")


def french_count_phrase(noun: str) -> str:
    return f"d'{noun}" if noun[:1].lower() in {"a", "e", "i", "o", "u", "h"} else f"de {noun}"


def kin_count_prompt(noun: str, *, seen: bool) -> str:
    intro = "Ubona" if seen else "Hari"
    return f"{intro} {noun} {kin_count_word(noun)}?"


def fr_count_prompt(noun: str, *, seen: bool) -> str:
    ending = "vois-tu ?" if seen else "y a-t-il ?"
    return f"Combien {french_count_phrase(noun)} {ending}"


def normalize_item_terms(item: dict) -> dict:
    updated = dict(item)
    for language, field in (("kin", "stem_kin"), ("fr", "stem_fr")):
        text = updated.get(field)
        if not text:
            continue
        for source, target in TERM_OVERRIDES.get(language, {}).items():
            text = text.replace(source, target)
        updated[field] = text
    return updated


def load_seed_curriculum(data_dir: Path) -> list[dict]:
    return [normalize_item_terms(item) for item in load_json(data_dir / "seed" / "curriculum_seed.json")]


def load_curriculum(data_dir: Path) -> list[dict]:
    generated = data_dir / "generated_curriculum.json"
    if generated.exists():
        return [normalize_item_terms(item) for item in load_json(generated)]
    return load_seed_curriculum(data_dir)


def _counting_item(i: int) -> dict:
    objects = ["apples", "goats", "beads", "birds", "drums", "balls"]
    obj = objects[i % len(objects)]
    obj_fr = localized_term(obj, "fr")
    obj_kin = localized_term(obj, "kin")
    answer = (i % 9) + 1
    return {
        "id": f"CX{i:03d}",
        "skill": "counting",
        "difficulty": min(9, 1 + i // 2),
        "age_band": AGE_BANDS[min(len(AGE_BANDS) - 1, i // 3)],
        "stem_en": f"How many {obj} do you see?",
        "stem_fr": fr_count_prompt(obj_fr, seen=True),
        "stem_kin": kin_count_prompt(obj_kin, seen=True),
        "visual": f"{obj}_{answer}",
        "answer_int": answer,
    }


def _number_sense_item(i: int) -> dict:
    left = 2 + i
    right = left + 2 + (i % 3)
    if i % 2 == 0:
        prompt_en = f"Which number is bigger: {left} or {right}?"
        prompt_fr = f"Quel nombre est le plus grand entre {left} et {right} ?"
        prompt_kin = f"Ni iyihe nimero nini hagati ya {left} na {right}?"
        answer = right
        visual = f"compare_{left}_{right}"
    else:
        prompt_en = f"What number comes between {left} and {right}?"
        prompt_fr = f"Quel nombre se trouve entre {left} et {right} ?"
        prompt_kin = f"Ni iyihe nimero iri hagati ya {left} na {right}?"
        answer = left + 1
        visual = f"between_{left}_{right}"
    return {
        "id": f"NX{i:03d}",
        "skill": "number_sense",
        "difficulty": min(9, 2 + i // 2),
        "age_band": AGE_BANDS[min(len(AGE_BANDS) - 1, i // 3)],
        "stem_en": prompt_en,
        "stem_fr": prompt_fr,
        "stem_kin": prompt_kin,
        "visual": visual,
        "answer_int": answer,
    }


def _addition_item(i: int) -> dict:
    a = 1 + (i % 9)
    b = 2 + ((i * 2) % 9)
    return {
        "id": f"AX{i:03d}",
        "skill": "addition",
        "difficulty": min(9, 2 + i // 2),
        "age_band": AGE_BANDS[min(len(AGE_BANDS) - 1, i // 3)],
        "stem_en": f"{a} plus {b} equals?",
        "stem_fr": f"Combien font {a} plus {b} ?",
        "stem_kin": f"{a} wongeyeho {b} bingana iki?",
        "visual": f"beads_{a}_plus_{b}",
        "answer_int": a + b,
    }


def _subtraction_item(i: int) -> dict:
    total = 6 + i
    take = 1 + (i % 5)
    return {
        "id": f"SX{i:03d}",
        "skill": "subtraction",
        "difficulty": min(9, 3 + i // 2),
        "age_band": AGE_BANDS[min(len(AGE_BANDS) - 1, i // 3)],
        "stem_en": f"{total} minus {take} equals?",
        "stem_fr": f"Combien font {total} moins {take} ?",
        "stem_kin": f"{total} ukuyemo {take} hasigara angahe?",
        "visual": f"minus_{total}_{take}",
        "answer_int": total - take,
    }


def _word_problem_item(i: int) -> dict:
    names = ["Aline", "Musa", "Sara", "Eric", "Keza", "Mami"]
    things = ["mangoes", "books", "beans", "oranges", "cups", "goats"]
    name = names[i % len(names)]
    thing = things[i % len(things)]
    thing_fr = localized_term(thing, "fr")
    thing_kin = localized_term(thing, "kin")
    start = 2 + i
    add = 1 + (i % 4)
    if i % 2 == 0:
        stem_en = f"{name} has {start} {thing} and gets {add} more. How many now?"
        stem_fr = f"{name} a {start} {thing_fr} et en reçoit encore {add}. Cela fait combien maintenant ?"
        stem_kin = f"{name} afite {start} {thing_kin} kandi yabonye izindi {add}. Bingana iki byose hamwe?"
        answer = start + add
        visual = f"{thing}_{start}_plus_{add}"
    else:
        stem_en = f"{name} has {start + add} {thing} and gives away {add}. How many remain?"
        stem_fr = f"{name} a {start + add} {thing_fr} et en donne {add}. Combien lui en reste-t-il ?"
        stem_kin = f"{name} afite {start + add} {thing_kin} kandi atanze {add}. Hasigaye bingahe?"
        answer = start
        visual = f"{thing}_{start + add}_minus_{add}"
    return {
        "id": f"WX{i:03d}",
        "skill": "word_problem",
        "difficulty": min(9, 3 + i // 2),
        "age_band": AGE_BANDS[min(len(AGE_BANDS) - 1, i // 3)],
        "stem_en": stem_en,
        "stem_fr": stem_fr,
        "stem_kin": stem_kin,
        "visual": visual,
        "answer_int": answer,
    }


def expand_curriculum(seed_items: list[dict], items_per_skill: int = 12) -> list[dict]:
    generated = list(seed_items)
    builders = {
        "counting": _counting_item,
        "number_sense": _number_sense_item,
        "addition": _addition_item,
        "subtraction": _subtraction_item,
        "word_problem": _word_problem_item,
    }
    existing_counts = {skill: 0 for skill in SKILLS}
    for item in seed_items:
        skill = item.get("skill")
        if skill in existing_counts:
            existing_counts[skill] += 1
    for skill in SKILLS:
        need = max(0, items_per_skill - existing_counts[skill])
        builder = builders[skill]
        for i in range(need):
            generated.append(builder(i + 1))
    return generated
