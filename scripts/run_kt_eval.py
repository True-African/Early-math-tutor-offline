from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tutor import SKILLS
from tutor.adaptive import elo_expected, elo_update, init_mastery, update_bkt
from tutor.curriculum_loader import load_curriculum


OUT_DIR = ROOT / "outputs"
DATA_DIR = ROOT / "data"


def item_rating(item: dict) -> float:
    return 850.0 + float(item.get("difficulty", 1)) * 35.0


def auc_score(labels: list[int], scores: list[float]) -> float:
    positives = [(s, l) for s, l in zip(scores, labels) if l == 1]
    negatives = [(s, l) for s, l in zip(scores, labels) if l == 0]
    if not positives or not negatives:
        return 0.5
    wins = 0.0
    total = 0.0
    for p, _ in positives:
        for n, _ in negatives:
            total += 1.0
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return round(wins / total, 4) if total else 0.5


def simulate_replay(curriculum: list[dict], n_learners: int = 120, attempts_per_learner: int = 24, seed: int = 42) -> dict:
    rng = random.Random(seed)
    items_by_skill = {skill: [item for item in curriculum if item["skill"] == skill] for skill in SKILLS}

    labels: list[int] = []
    bkt_scores: list[float] = []
    elo_scores: list[float] = []
    replay_rows = []

    for learner_idx in range(n_learners):
        hidden_mastery = {skill: rng.uniform(0.2, 0.8) for skill in SKILLS}
        bkt_mastery = init_mastery()
        elo_rating = 1000.0
        learner_id = f"L{learner_idx:03d}"

        for step in range(attempts_per_learner):
            target_skill = rng.choice(SKILLS) if step < 5 else min(SKILLS, key=lambda s: bkt_mastery[s])
            item = rng.choice(items_by_skill[target_skill])
            difficulty = float(item.get("difficulty", 1))
            hidden_prob = max(0.05, min(0.95, hidden_mastery[target_skill] - 0.035 * (difficulty - 1) + rng.uniform(-0.04, 0.04)))
            label = 1 if rng.random() < hidden_prob else 0

            bkt_pred = bkt_mastery[target_skill]
            elo_pred = elo_expected(elo_rating, item_rating(item))

            labels.append(label)
            bkt_scores.append(float(bkt_pred))
            elo_scores.append(float(elo_pred))
            replay_rows.append(
                {
                    "learner_id": learner_id,
                    "step": step,
                    "skill": target_skill,
                    "item_id": item["id"],
                    "difficulty": difficulty,
                    "label": label,
                    "hidden_prob": round(hidden_prob, 4),
                    "bkt_pred": round(float(bkt_pred), 4),
                    "elo_pred": round(float(elo_pred), 4),
                }
            )

            bkt_mastery[target_skill] = update_bkt(bkt_mastery[target_skill], bool(label))
            elo_rating = elo_update(elo_rating, item_rating(item), bool(label))
            hidden_mastery[target_skill] = max(0.05, min(0.97, hidden_mastery[target_skill] + (0.06 if label else 0.01)))

    bkt_auc = auc_score(labels, bkt_scores)
    elo_auc = auc_score(labels, elo_scores)
    return {
        "bkt_auc": bkt_auc,
        "elo_auc": elo_auc,
        "learners": n_learners,
        "attempts_per_learner": attempts_per_learner,
        "events": len(replay_rows),
        "summary": (
            f"Measured on synthetic held-out replay with {n_learners} learners and {len(replay_rows)} answer events. "
            f"BKT reached AUC {bkt_auc}, compared with Elo baseline AUC {elo_auc}."
        ),
        "replay_rows": replay_rows,
    }


def write_outputs(result: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = {
        key: value
        for key, value in result.items()
        if key != "replay_rows"
    }
    (OUT_DIR / "kt_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    header = "learner_id,step,skill,item_id,difficulty,label,hidden_prob,bkt_pred,elo_pred\n"
    rows = [
        ",".join(
            [
                row["learner_id"],
                str(row["step"]),
                row["skill"],
                row["item_id"],
                str(row["difficulty"]),
                str(row["label"]),
                str(row["hidden_prob"]),
                str(row["bkt_pred"]),
                str(row["elo_pred"]),
            ]
        )
        for row in result["replay_rows"]
    ]
    (OUT_DIR / "kt_replay.csv").write_text(header + "\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    curriculum = load_curriculum(DATA_DIR)
    result = simulate_replay(curriculum)
    write_outputs(result)
    print(result["summary"])


if __name__ == "__main__":
    main()
