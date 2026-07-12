# ============================================================
# 动量轮动策略模板（研究参考版）
# Momentum Rotation Strategy Template
# ============================================================
#
# 适用场景:
# - 多币种、多资产、行业或风格轮动研究
# - 从资产池中选择相对强势标的
#
# 当前限制:
# - 单标 Indicator IDE 主要消费 df 和四路信号
# - 多标轮动需要 data = {symbol: df}、组合排序和组合执行链路支持
# - 因此本模板先输出 scores / rankings，作为轮动研究和后续组合执行的基础
#
# ============================================================

my_indicator_name = "动量轮动策略模板"
my_indicator_description = "对多个标的计算动量和波动调整评分，选择相对强势资产。"

# @param lookback int 20 动量回看周期
# @param volatility_period int 20 波动率周期
# @param top_n int 3 做多排名靠前数量
# @param use_vol_adjust bool true 是否使用波动率调整

# 说明：本模板不是单标四路执行脚本；它用于多标轮动研究。
# 后续平台具备组合轮动执行后，可将 rankings 转换为组合调仓指令。

lookback = int(params.get("lookback", 20))
volatility_period = int(params.get("volatility_period", 20))
top_n = int(params.get("top_n", 3))
use_vol_adjust = bool(params.get("use_vol_adjust", True))

scores = {}

for symbol, symbol_df in data.items():
    if len(symbol_df) <= max(lookback, volatility_period):
        scores[symbol] = 0.0
        continue

    close = symbol_df["close"]
    momentum = close.iloc[-1] / close.iloc[-lookback] - 1
    returns = close.pct_change()
    volatility = returns.rolling(volatility_period).std().iloc[-1]

    if use_vol_adjust and volatility and volatility > 0:
        score = momentum / volatility
    else:
        score = momentum

    scores[symbol] = float(score)

rankings = sorted(scores.keys(), key=lambda item: scores[item], reverse=True)
selected_longs = rankings[:top_n]

output = {
    "name": my_indicator_name,
    "scores": scores,
    "rankings": rankings,
    "selected_longs": selected_longs,
    "notes": [
        "当前模板用于多标轮动研究，不直接生成单标 open_long/open_short 信号。",
        "组合执行链路完善后，可将 selected_longs 转换为调仓目标。",
    ],
}
