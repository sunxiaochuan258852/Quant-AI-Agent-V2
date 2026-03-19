STRATEGY_NAME = "kdj_timing"

PARAM_SCHEMA = {
    "stock_code": {
        "type": "str",
        "default": "000001.XSHE",
        "description": "交易标的"
    },
    "k_period": {
        "type": "int",
        "default": 9,
        "description": "KDJ周期"
    },
    "buy_threshold": {
        "type": "float",
        "default": 20,
        "description": "超卖阈值（K值低于该值买入）"
    },
    "sell_threshold": {
        "type": "float",
        "default": 80,
        "description": "超买阈值（K值高于该值卖出）"
    }
}


def generate(params):
    stock = params.get("stock_code", "000001.XSHE")
    k_period = params.get("k_period", 9)
    buy_th = params.get("buy_threshold", 20)
    sell_th = params.get("sell_threshold", 80)

    return f"""
from jqdata import *


def _order_target_percent(context, security, percent):
    if "order_target_value" in globals():
        return order_target_value(security, context.portfolio.total_value * percent)
    if hasattr(context, "order_target_value"):
        return context.order_target_value(security, context.portfolio.total_value * percent)
    if "order_target_percent" in globals():
        return order_target_percent(security, percent)
    if hasattr(context, "order_target_percent"):
        return context.order_target_percent(security, percent)
    raise NameError("order_target_percent is not defined in this environment")


def _order_target_zero(context, security):
    if "order_target" in globals():
        return order_target(security, 0)
    if "order_target_value" in globals():
        return order_target_value(security, 0)
    if hasattr(context, "order_target"):
        return context.order_target(security, 0)
    if hasattr(context, "order_target_value"):
        return context.order_target_value(security, 0)
    raise NameError("order_target is not defined in this environment")


def _holding_amount(context, security):
    position = context.portfolio.positions[security] if security in context.portfolio.positions else None
    return position.total_amount if position else 0


# KDJ Timing Strategy

def initialize(context):
    g.stock = "{stock}"
    g.k_period = {k_period}
    g.buy_th = {buy_th}
    g.sell_th = {sell_th}

    run_daily(trade, time='09:35')


def trade(context):
    df = get_price(g.stock, count=g.k_period)

    # 防御：数据不足直接退出
    if df is None or len(df) < g.k_period:
        return

    low_list = df['low']
    high_list = df['high']
    close_list = df['close']

    low_min = low_list.min()
    high_max = high_list.max()

    # 防止除0
    if high_max == low_min:
        return

    # RSV计算
    rsv = (close_list.iloc[-1] - low_min) / (high_max - low_min) * 100

    # 简化KDJ（单点版本）
    k = rsv
    d = k
    j = 3 * k - 2 * d
    holding_amount = _holding_amount(context, g.stock)

    # 买入逻辑（超卖反弹）
    if k < g.buy_th and holding_amount == 0:
        _order_target_percent(context, g.stock, 1)

    # 卖出逻辑（超买回落）
    elif k > g.sell_th and holding_amount > 0:
        _order_target_zero(context, g.stock)
"""
