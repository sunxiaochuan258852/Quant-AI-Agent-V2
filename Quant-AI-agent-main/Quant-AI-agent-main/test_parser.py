# test_parser.py

from agent.ai_parser import parse_strategy

text = "最近30天涨幅最大的10只股票"

result = parse_strategy(text)

print("\n解析结果:")
print(result)