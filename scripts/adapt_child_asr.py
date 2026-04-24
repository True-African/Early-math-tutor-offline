from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tutor.asr_adapt import augment_child_speech_manifest


DATA_DIR = ROOT / "data"
ASR_DIR = ROOT / "assets" / "audio"


def main() -> None:
    seed_manifest = DATA_DIR / "seed" / "child_utt_sample_seed.csv"
    output_manifest = DATA_DIR / "child_utt_augmented.csv"
    result = augment_child_speech_manifest(seed_manifest, output_manifest, ASR_DIR)
    print(result)


if __name__ == "__main__":
    main()
