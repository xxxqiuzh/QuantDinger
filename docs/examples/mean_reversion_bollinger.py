# ============================================================
# 布林带均值回归策略模板
# Mean Reversion Bollinger Strategy Template
# ============================================================
#
# 适用场景:
# - 区间震荡、价格围绕均值反复波动的市场
# - 不适合强单边趋势行情直接裸跑
#
# 风险提示:
# - 单边趋势中可能连续逆势开仓
# - 建议保留 stopLossPct，或叠加趋势过滤
#
# ============================================================

my_indicator_name = "布林带均值回归策略模板"
my_indicator_description = "价格触及布林带外侧后押注均值回归，使用四路信号表达开平仓。"

# --- QuantDinger execution contract (v1) ---
# signal_form: four_way
# exit_owner: engine
# flip_mode: R2

# @param bb_period int 20 布林带周期
# @param bb_std float 2.0 标准差倍数
# @param exit_on_midline bool true 是否在回到中轨时平仓

# @strategy stopLossPct 0.02
# @strategy takeProfitPct 0.035
# @strategy entryPct 0.2
# @strategy trailingEnabled false
# @strategy tradeDirection both

# 说明：本模板的 close_* 表达回到中轨或反向信号时的结构性平仓；价格级止损仍由 engine 负责。
# output["signals"] 只负责图表标记，不参与下单。


def edge(signal):
    signal = signal.fillna(False).astype(bool)
    return signal & ~signal.shift(1).fillna(False)


df = df.copy()

bb_period = int(params.get("bb_period", 20))
bb_std = float(params.get("bb_std", 2.0))
exit_on_midline = bool(params.get("exit_on_midline", True))

mid = df["close"].rolling(bb_period).mean()
std = df["close"].rolling(bb_period).std()
upper = mid + std * bb_std
lower = mid - std * bb_std

raw_open_long = df["close"] < lower
raw_open_short = df["close"] > upper

if exit_on_midline:
    raw_close_long = df["close"] >= mid
    raw_close_short = df["close"] <= mid
else:
    raw_close_long = raw_open_short
    raw_close_short = raw_open_long

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
        {"name": "BB Mid", "data": mid.fillna(0).tolist(), "color": "#3F51B5", "overlay": True},
        {"name": "BB Upper", "data": upper.fillna(0).tolist(), "color": "#FF9800", "overlay": True},
        {"name": "BB Lower", "data": lower.fillna(0).tolist(), "color": "#FF9800", "overlay": True},
    ],
    "signals": [
        {"type": "buy", "text": "MRL", "data": open_long_marks, "color": "#00E676"},
        {"type": "sell", "text": "MRS", "data": open_short_marks, "color": "#FF5252"},
    ],
}
