STRATEGY_NAME = "ma_breakout"

PARAM_SCHEMA = {
    "ma_period": {
        "type": "int",
        "default": 5,
        "description": "均线周期"
    },
    "threshold": {
        "type": "float",
        "default": 1.01,
        "description": "突破阈值（如1.01表示上涨1%）"
    },
    "stock_code": {
        "type": "str",
        "default": "000001.XSHE",
        "description": "交易标的"
    }
}


def generate(params):
    ma = params.get("ma_period", 5)
    threshold = params.get("threshold", 1.01)
    stock = params.get("stock_code", "000001.XSHE")

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


# MA Breakout Strategy

def initialize(context):
    g.stock = "{stock}"
    g.ma_period = {ma}
    g.threshold = {threshold}
    set_option("use_real_price", True)
    run_daily(trade, time='open')

def trade(context):
    df = attribute_history(g.stock, g.ma_period, "1d", ["close"], skip_paused=True)

    # 防止数据不足
    if df is None or len(df) < g.ma_period:
        return

    ma = df['close'].mean()
    current_data = get_current_data()
    price = current_data[g.stock].day_open
    if price is None or price <= 0:
        return

    holding_amount = _holding_amount(context, g.stock)

    # 突破买入
    if price > ma * g.threshold and holding_amount == 0:
        _order_target_percent(context, g.stock, 1)

    # 跌破均线卖出
    elif price < ma and holding_amount > 0:
        _order_target_zero(context, g.stock)
"""
