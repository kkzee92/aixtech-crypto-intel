from pathlib import Path

from crypto_intel.cli import main

FIXTURE = Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json"


def test_cli_scan(capsys):
    assert main(["scan", str(FIXTURE)]) == 0
    out = capsys.readouterr().out
    assert "BTC-USD" in out
    assert "paper" in out


def test_cli_backtest(capsys):
    assert main(["backtest", str(FIXTURE), "--symbol", "ETH-USD"]) == 0
    assert "ending_equity" in capsys.readouterr().out


def test_cli_v12_desk_and_custody(capsys):
    assert main(["v12", str(FIXTURE)]) == 0
    assert "can_increase_size" in capsys.readouterr().out
    assert main(["desk", str(FIXTURE)]) == 0
    desk = capsys.readouterr().out
    assert "lineage_digest" in desk
    assert "SYNTHETIC" in desk
    assert main(["custody"]) == 0
    custody = capsys.readouterr().out
    assert "withdrawal_allowlist" in custody
    assert "execution_zone" in custody
