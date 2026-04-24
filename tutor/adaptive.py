from __future__ import annotations

from tutor import SKILLS


# Each skill starts with a small mastery probability and is updated after every answer.
def init_mastery(default: float = 0.35) -> dict[str, float]:
    return {skill: default for skill in SKILLS}


# This is the Bayesian Knowledge Tracing update step used by the tutor.
def update_bkt(
    prior: float,
    correct: bool,
    transit: float = 0.12,
    slip: float = 0.1,
    guess: float = 0.2,
) -> float:
    prior = max(0.001, min(0.999, float(prior)))
    if correct:
        posterior = (prior * (1 - slip)) / ((prior * (1 - slip)) + ((1 - prior) * guess))
    else:
        posterior = (prior * slip) / ((prior * slip) + ((1 - prior) * (1 - guess)))
    posterior = posterior + (1 - posterior) * transit
    return round(max(0.01, min(0.99, posterior)), 4)


def update_mastery(mastery: dict[str, float], skill: str, correct: bool) -> dict[str, float]:
    next_state = dict(mastery)
    next_state[skill] = update_bkt(next_state.get(skill, 0.35), correct)
    return next_state


# The next item comes from the weakest skill first, with difficulty matched to current mastery.
def choose_next_item(
    curriculum: list[dict],
    mastery: dict[str, float],
    recent_ids: list[str] | None = None,
) -> dict:
    recent_ids = recent_ids or []
    target_skill = min(SKILLS, key=lambda skill: mastery.get(skill, 0.35))
    target_difficulty = max(1, min(9, round(1 + mastery.get(target_skill, 0.35) * 8)))
    candidates = [item for item in curriculum if item.get("skill") == target_skill and item.get("id") not in recent_ids]
    if not candidates:
        candidates = [item for item in curriculum if item.get("id") not in recent_ids] or curriculum
    candidates.sort(key=lambda item: (abs(int(item.get("difficulty", 1)) - target_difficulty), int(item.get("difficulty", 1)), item.get("id", "")))
    return candidates[0]


def elo_expected(player_rating: float, item_rating: float) -> float:
    return 1.0 / (1.0 + 10 ** ((item_rating - player_rating) / 400.0))


# Elo is used as a comparison baseline in the evaluation notebook and script.
def elo_update(player_rating: float, item_rating: float, correct: bool, k: float = 24.0) -> float:
    expected = elo_expected(player_rating, item_rating)
    observed = 1.0 if correct else 0.0
    return player_rating + k * (observed - expected)
