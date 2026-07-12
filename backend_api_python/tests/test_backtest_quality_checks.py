from app.services.backtest import BacktestService


def _codes(checks):
    return {item["id"]: item for item in checks}


def test_backtest_quality_checks_flag_missing_costs_and_risk_controls():
    svc = BacktestService()
    checks = svc._build_quality_checks(
        metrics={"totalTrades": 4, "maxDrawdown": -22.0},
        trades=[
            {"type": "open_long", "profit": 0},
            {"type": "close_long", "profit": 100},
            {"type": "open_long", "profit": 0},
            {"type": "close_long", "profit": -30},
        ],
        strategy_config={"risk": {}},
        commission=0,
        slippage=0,
    )

    by_id = _codes(checks)
    assert by_id["commission_configured"]["status"] == "WARN"
    assert by_id["slippage_configured"]["status"] == "WARN"
    assert by_id["stop_loss_configured"]["status"] == "FAIL"
    assert by_id["trade_sample_size"]["status"] == "WARN"
    assert by_id["max_drawdown"]["status"] == "WARN"


def test_backtest_quality_checks_explain_trailing_take_profit_rule():
    svc = BacktestService()
    checks = svc._build_quality_checks(
        metrics={"totalTrades": 30, "maxDrawdown": -8.0},
        trades=[{"type": "close_long", "profit": 1.0}] * 30,
        strategy_config={
            "risk": {
                "stopLossPct": 0.02,
                "takeProfitPct": 0.04,
                "trailing": {"enabled": True, "pct": 0.02, "activationPct": 0.03},
            }
        },
        commission=0.001,
        slippage=0.0005,
    )

    by_id = _codes(checks)
    assert by_id["commission_configured"]["status"] == "PASS"
    assert by_id["slippage_configured"]["status"] == "PASS"
    assert by_id["trailing_take_profit_semantics"]["status"] == "WARN"
    assert by_id["sample_out_of_sample"]["status"] == "WARN"
    assert by_id["parameter_stability"]["status"] == "WARN"
