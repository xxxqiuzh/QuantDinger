from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "docs" / "examples"


EXPECTED_TEMPLATES = [
    "trend_following.py",
    "mean_reversion_bollinger.py",
    "atr_trailing_stop.py",
    "momentum_rotation.py",
    "grid_range.py",
]


def _read_template(name):
    return (EXAMPLES / name).read_text(encoding="utf-8")


def test_research_strategy_templates_exist():
    missing = [name for name in EXPECTED_TEMPLATES if not (EXAMPLES / name).exists()]
    assert missing == []


def test_executable_templates_declare_four_way_contract():
    executable_templates = [
        "trend_following.py",
        "mean_reversion_bollinger.py",
        "atr_trailing_stop.py",
        "grid_range.py",
    ]
    for name in executable_templates:
        code = _read_template(name)
        assert "signal_form: four_way" in code
        assert "flip_mode: R2" in code
        assert 'df["open_long"]' in code
        assert 'df["close_long"]' in code
        assert 'df["open_short"]' in code
        assert 'df["close_short"]' in code
        assert "output = {" in code
        assert "# @param" in code
        assert "# @strategy" in code


def test_momentum_rotation_template_documents_current_limitations():
    code = _read_template("momentum_rotation.py")
    assert "scores = {}" in code
    assert "当前限制" in code
    assert "多标" in code
    assert "ranking" in code or "rankings" in code
