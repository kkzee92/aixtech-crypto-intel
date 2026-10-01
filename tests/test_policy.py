import json
from pathlib import Path

from crypto_intel.market import load_candles

ROOT = Path(__file__).parents[1]


def test_fixture_is_labelled_synthetic():
    payload = json.loads((ROOT / "fixtures" / "candles_synthetic.json").read_text())
    assert payload["label"] == "SYNTHETIC"
    assert len(load_candles(ROOT / "fixtures" / "candles_synthetic.json")) >= 9
