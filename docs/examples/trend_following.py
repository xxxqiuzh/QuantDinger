# ============================================================
# 趋势跟踪策略模板
# Trend Following Strategy Template
# ============================================================
#
# 适用场景:
# - BTC/ETH 等高流动性标的
# - 趋势明确、震荡噪音较少的市场
#
# 风险提示:
# - 横盘震荡时容易出现连续假突破
# - 建议配合 stopLossPct / trailingEnabled 使用
#
# ============================================================

my_indicator_name = "趋势跟踪策略模板"
my_indicator_description = "使用 EMA 趋势方向和 ADX 强度过滤生成四路交易信号。"

# --- QuantDinger execution contract (v1) ---
# signal_form: four_way
# exit_owner: engine
# flip_mode: R2

# @param fast_period int 12 快线 EMA 周期
# @param slow_period int 36 慢线 EMA 周期
# @param adx_period int 14 ADX 周期
# @param adx_threshold float 18.0 趋势强度阈值
# @param use_adx_filter bool true 是否启用 ADX 过滤

# @strategy stopLossPct 0.025
# @strategy takeProfitPct 0.06
# @strategy entryPct 0.25
# @strategy trailingEnabled true
# @strategy trailingStopPct 0.02
# @strategy trailingActivationPct 0.04
# @strategy tradeDirection both

# 说明：本模板只负责趋势入场和反手信号；固定止损、固定止盈和追踪止盈由 engine 负责。
# output["signals"] 只负责图表标记，不参与下单。


def edge(signal):
    signal = signal.fillna(False).astype(bool)
    return signal & ~signal.shift(1).fillna(False)


df = df.copy()

fast_period = int(params.get("fast_period", 12))
slow_period = int(params.get("slow_period", 36))
adx_period = int(params.get("adx_period", 14))
adx_threshold = float(params.get("adx_threshold", 18.0))
use_adx_filter = bool(params.get("use_adx_filter", True))

ema_fast = df["close"].ewm(span=fast_period, adjust=False).mean()
ema_slow = df["close"].ewm(span=slow_period, adjust=False).mean()

up_move = df["high"].diff()
down_move = -df["low"].diff()
plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
prev_close = df["close"].shift(1)
tr = pd.concat(
    [
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ],
    axis=1,
).max(axis=1)
atr = tr.rolling(adx_period).mean()
plus_di = 100 * plus_dm.rolling(adx_period).mean() / atr.replace(0, np.nan)
minus_di = 100 * minus_dm.rolling(adx_period).mean() / atr.replace(0, np.nan)
dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
adx = dx.rolling(adx_period).mean()

trend_ok = adx >= adx_threshold
if not use_adx_filter:
    trend_ok = ema_fast.notna()

raw_open_long = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1)) & trend_ok
raw_open_short = (ema_fast < ema_slow) & (ema_fast.shift(1) >= ema_slow.shift(1)) & trend_ok

df["open_long"] = edge(raw_open_long)
df["close_short"] = df["open_long"]
df["open_short"] = edge(raw_open_short)
df["close_long"] = df["open_short"]

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
        {"name": f"EMA{fast_period}", "data": ema_fast.fillna(0).tolist(), "color": "#FF9800", "overlay": True},
        {"name": f"EMA{slow_period}", "data": ema_slow.fillna(0).tolist(), "color": "#3F51B5", "overlay": True},
        {"name": "ADX", "data": adx.fillna(0).tolist(), "color": "#13C2C2", "overlay": False},
    ],
    "signals": [
        {"type": "buy", "text": "TL", "data": open_long_marks, "color": "#00E676"},
        {"type": "sell", "text": "TS", "data": open_short_marks, "color": "#FF5252"},
    ],
}
