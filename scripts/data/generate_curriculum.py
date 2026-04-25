from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tutor.curriculum_loader import expand_curriculum, load_seed_curriculum, save_json

DATA_DIR = ROOT / "data"


def main() -> None:
    seed = load_seed_curriculum(DATA_DIR)
    generated = expand_curriculum(seed, items_per_skill=12)
    out_path = DATA_DIR / "generated_curriculum.json"
    save_json(out_path, generated)
    print(f"Saved {len(generated)} curriculum items to {out_path}")


if __name__ == "__main__":
    main()
