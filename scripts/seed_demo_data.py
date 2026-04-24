from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tutor.adaptive import choose_next_item, init_mastery, update_mastery
from tutor.curriculum_loader import load_curriculum
from tutor.storage import get_or_create_learner, init_db, save_attempt, save_mastery


DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "local_store.sqlite"


def main() -> None:
    rng = random.Random(7)
    init_db(DB_PATH)
    curriculum = load_curriculum(DATA_DIR)
    learner_id, learner_name = get_or_create_learner(DB_PATH, "Akeza", "kin", init_mastery())
    mastery = init_mastery()
    recent_ids: list[str] = []
    for step in range(18):
        item = choose_next_item(curriculum, mastery, recent_ids)
        correct_prob = 0.72 - (float(item.get("difficulty", 1)) * 0.03)
        correct = rng.random() < max(0.2, min(0.92, correct_prob))
        response_value = int(item["answer_int"]) if correct else max(0, int(item["answer_int"]) - 1)
        language = rng.choice(["kin", "en", "fr"])
        response_text = str(response_value)
        save_attempt(DB_PATH, learner_id, item["id"], item["skill"], correct, response_text, response_value, language)
        mastery = update_mastery(mastery, item["skill"], correct)
        save_mastery(DB_PATH, learner_id, mastery)
        recent_ids = (recent_ids + [item["id"]])[-6:]
    print(f"Seeded demo learner {learner_name} with 18 attempts.")


if __name__ == "__main__":
    main()
