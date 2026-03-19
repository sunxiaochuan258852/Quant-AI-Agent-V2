import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = """
You convert Chinese or English trading-strategy requests into JSON.
Return JSON only. Do not add markdown, commentary, or code fences.

Supported strategy types and fields:
1. momentum
- lookback_days: int
- stock_count: int

2. ma_breakout
- ma_period: int
- threshold: float
- stock_code: str

3. kdj_timing
- stock_code: str
- k_period: int
- buy_threshold: int
- sell_threshold: int

4. alpaca_rotation
- total_stock_nums: int
- sell_stock_nums: int
- rebalance_days: int
- start_date: str
- end_date: str
- random_seed: int

5. brandes_value
- hold_count: int
- start_date: str
- end_date: str
- rebalance_period_days: int

Rules:
- Output valid JSON.
- Always include strategy_type.
- Use common A-share / ETF codes when the request names a well-known Chinese asset.
- If the user does not specify optional values, use reasonable defaults from the examples below.

Examples:
Input: 最近60天涨幅最高的20只股票
Output: {"strategy_type": "momentum", "lookback_days": 60, "stock_count": 20}

Input: 5日均线突破1%买入平安银行
Output: {"strategy_type": "ma_breakout", "ma_period": 5, "threshold": 1.01, "stock_code": "000001.XSHE"}

Input: 我要做一份十只股票的kdj策略
Output: {"strategy_type": "kdj_timing", "stock_code": "000001.XSHE", "k_period": 9, "buy_threshold": 20, "sell_threshold": 80}

Input: 做一个羊驼策略，随机持有30只股票，每22个交易日调仓一次，卖出收益最差的6只股票，再随机买入6只，回测区间2009年到2021年
Output: {"strategy_type": "alpaca_rotation", "total_stock_nums": 30, "sell_stock_nums": 6, "rebalance_days": 22, "start_date": "2009-01-01", "end_date": "2021-12-31", "random_seed": 42}

Input: 做一个布兰德价值投资策略，持股30只，每月第1个交易日调仓，回测区间2016年4月到2024年9月
Output: {"strategy_type": "brandes_value", "hold_count": 30, "start_date": "2016-04-01", "end_date": "2024-09-26", "rebalance_period_days": 1}
"""


def _build_client(api_key=None):
    resolved_api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not resolved_api_key:
        raise ValueError("Missing DeepSeek API key.")

    return OpenAI(
        api_key=resolved_api_key,
        base_url="https://api.deepseek.com",
    )


def _extract_json_object(content):
    stripped = (content or "").strip()
    if not stripped:
        raise ValueError("Empty response from model.")

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Model did not return JSON.")

    return json.loads(stripped[start : end + 1])


def parse_strategy(text, api_key=None):
    normalized_text = text.strip()
    if not normalized_text:
        raise ValueError("Strategy description cannot be empty.")

    client = _build_client(api_key=api_key)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": normalized_text},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content if response.choices else ""
    return _extract_json_object(content)
