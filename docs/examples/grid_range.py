# ============================================================
# 区间网格策略模板
# Range Grid Strategy Template
# ============================================================
#
# 适用场景:
# - 价格在明确区间内震荡
# - 希望用规则化低买高卖捕捉波动
#
# 风险提示:
# - 单边突破区间会导致库存或踏空风险
# - 真实网格更适合由专门 grid engine 管理挂单和成交同步
# - 本模板用于 Indicator IDE 中演示区间网格信号，不替代实盘网格引擎
#
# ============================================================

my_indicator_name = "区间网格策略模板"
my_indicator_description = "在预设区间内生成低买高卖信号，用于演示网格策略的指标侧表达。"

# --- QuantDinger execution contract (v1) ---
# signal_form: four_way
# exit_owner: indicator
# flip_mode: R2

# @param lower_bound float 0.0 区间下边界，0 表示自动使用回看低点
# @param upper_bound float 0.0 区间上边界，0 表示自动使用回看高点
# @param range_period int 120 自动区间回看周期
# @param grid_count int 12 网格数量
# @param breakout_buffer_pct float 0.01 破网缓冲比例

# @strategy stopLossPct 0.03
# @strategy takeProfitPct 0.0
# @strategy entryPct 0.1
# @strategy trailingEnabled false
# @strategy tradeDirection both

# 说明：本模板把触网买卖写进 open_* / close_*；破网后用 close_* 表达风险退出。
# output["signals"] 只负责图表标记，不参与下单。


def edge(signal):
    signal = signal.fillna(False).astype(bool)
    return signal & ~signal.shift(1).fillna(False)


df = df.copy()

lower_bound = float(params.get("lower_bound", 0.0))
upper_bound = float(params.get("upper_bound", 0.0))
range_period = int(params.get("range_period", 120))
grid_count = max(int(params.get("grid_count", 12)), 1)
breakout_buffer_pct = float(params.get("breakout_buffer_pct", 0.01))

auto_lower = df["low"].rolling(range_period).min()
auto_upper = df["high"].rolling(range_period).max()

lower = auto_lower if lower_bound <= 0 else df["close"] * 0 + lower_bound
upper = auto_upper if upper_bound <= 0 else df["close"] * 0 + upper_bound
grid_step = (upper - lower) / grid_count

position_in_grid = ((df["close"] - lower) / grid_step.replace(0, np.nan)).round()
prev_position = position_in_grid.shift(1)

inside_range = (df["close"] >= lower) & (df["close"] <= upper)
cross_down_grid = inside_range & (position_in_grid < prev_position)
cross_up_grid = inside_range & (position_in_grid > prev_position)

breakdown = df["close"] < lower * (1 - breakout_buffer_pct)
breakout = df["close"] > upper * (1 + breakout_buffer_pct)

df["open_long"] = edge(cross_down_grid)
df["close_long"] = edge(cross_up_grid | breakdown)
df["open_short"] = edge(cross_up_grid)
df["close_short"] = edge(cross_down_grid | breakout)

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
        {"name": "Grid Lower", "data": lower.fillna(0).tolist(), "color": "#52C41A", "overlay": True},
        {"name": "Grid Upper", "data": upper.fillna(0).tolist(), "color": "#F5222D", "overlay": True},
    ],
    "signals": [
        {"type": "buy", "text": "GL", "data": open_long_marks, "color": "#00E676"},
        {"type": "sell", "text": "GS", "data": open_short_marks, "color": "#FF5252"},
    ],
}
