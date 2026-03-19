# test_full.py

from agent.ai_parser import parse_strategy
from agent.code_generator import generate_strategy_code

text = "最近30天涨幅最大的10只股票"

params = parse_strategy(text)

print("\n解析参数:")
print(params)

code = generate_strategy_code(params)

print("\n生成策略代码:\n")
print(code)