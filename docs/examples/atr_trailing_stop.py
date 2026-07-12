# ============================================================
# ATR 动态止损策略模板
# ATR Trailing Stop Strategy Template
# ============================================================
#
# 适用场景:
# - 波动率变化明显，固定百分比止损过紧或过宽的市场
# - 趋势跟踪策略的动态退出示例
#
# 风险提示:
# - ATR 周期过短会过度敏感
# - ATR 周期过长会滞后，可能放大回撤
#
# ============================================================

my_indicator_name = "ATR 动态止损策略模板"
my_indicator_description = "使用 EMA 入场，使用 ATR Chandelier Stop 生成结构性平仓信号。"

# --- QuantDinger execution contract (v1) ---
# signal_form: four_way
# exit_owner: indicator
# flip_mode: R2

# @param ema_period int 50 趋势 EMA 周期
# @param atr_period int 14 ATR 周期
# @param atr_mult float 2.5 ATR 止损倍数
# @param channel_period int 20 最高/最低价回看周期

# @strategy stopLossPct 0.03
# @strategy takeProfitPct 0.0
# @strategy entryPct 0.2
# @strategy trailingEnabled false
# @strategy tradeDirection both

# 说明：本模板把 ATR 止损写进 close_*，因此 exit_owner 为 indicator。
# engine 的 stopLossPct 仍可作为硬止损兜底；不建议再叠加很窄的 trailingEnabled。
# output["signals"] 只负责图表标记，不参与下单。


def edge(signal):
    signal = signal.fillna(False).astype(bool)
    return signal & ~signal.shift(1).fillna(False)


df = df.copy()

ema_period = int(params.get("ema_period", 50))
atr_period = int(params.get("atr_period", 14))
atr_mult = float(params.get("atr_mult", 2.5))
channel_period = int(params.get("channel_period", 20))

ema = df["close"].ewm(span=ema_period, adjust=False).mean()
prev_close = df["close"].shift(1)
tr = pd.concat(
    [
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ],
    axis=1,
).max(axis=1)
atr = tr.rolling(atr_period).mean()

highest_close = df["close"].rolling(channel_period).max()
lowest_close = df["close"].rolling(channel_period).min()
long_stop = highest_close - atr * atr_mult
short_stop = lowest_close + atr * atr_mult

raw_open_long = (df["close"] > ema) & (df["close"].shift(1) <= ema.shift(1))
raw_open_short = (df["close"] < ema) & (df["close"].shift(1) >= ema.shift(1))
raw_close_long = df["close"] < long_stop.shift(1)
raw_close_short = df["close"] > short_stop.shift(1)

df["open_long"] = edge(raw_open_long)
df["open_short"] = edge(raw_open_short)
df["close_long"] = edge(raw_close_long | raw_open_short)
df["close_short"] = edge(raw_close_short | raw_open_long)

n = len(df)
open_long_marks = [
    df["low"].iloc[i] * 0.995 if bool(df["open_long"].iloc[i]) else None for i in range(n)
]
open_short_marks = [
    df["high"].iloc[i] * 1.005 if bool(df["open_short"].iloc[i]) else None for i in range(n)
]

output = {
    "name": my_indicator_name,
    "plots": [
        {"name": f"EMA{ema_period}", "data": ema.fillna(0).tolist(), "color": "#3F51B5", "overlay": True},
        {"name": "ATR Long Stop", "data": long_stop.fillna(0).tolist(), "color": "#F5222D", "overlay": True},
        {"name": "ATR Short Stop", "data": short_stop.fillna(0).tolist(), "color": "#13C2C2", "overlay": True},
        {"name": f"ATR{atr_period}", "data": atr.fillna(0).tolist(), "color": "#722ED1", "overlay": False},
    ],
    "signals": [
        {"type": "buy", "text": "ATL", "data": open_long_marks, "color": "#00E676"},
        {"type": "sell", "text": "ATS", "data": open_short_marks, "color": "#FF5252"},
    ],
}
