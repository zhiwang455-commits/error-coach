"""Step 2.5 — 分类器准确率 / classifier accuracy. 就是一个除法 (§2.5).

先在 labeling_sheet.csv 的 hand_label 列填上你自己判断的类别
(必须用 ERROR_TYPES 里的原词), 然后:  ./venv/bin/python eval.py
"""

import csv
import sys

from coach import ERROR_TYPES

try:
    with open("labeling_sheet.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
except FileNotFoundError:
    sys.exit("先跑 convert_form.py / run convert_form.py first")

labeled = [r for r in rows if r["hand_label"].strip()]
if not labeled:
    sys.exit("hand_label 列还是空的 — 先人工标注 / fill the hand_label column first")

# 你手填的标签也要在封闭表里 — 拼错的标签会让准确率虚低
# your hand labels must come from the closed list too — typos fake a low score
bad = [r["hand_label"].strip() for r in labeled
       if r["hand_label"].strip() not in ERROR_TYPES]
if bad:
    sys.exit(f"这些 hand_label 不在 ERROR_TYPES 里 / not in the taxonomy: {set(bad)}")

correct = sum(1 for r in labeled if r["hand_label"].strip() == r["ai_label"])
acc = correct / len(labeled)

print(f"hand-labeled : {len(labeled)}")
print(f"AI correct   : {correct}")
print(f"accuracy     = {acc:.0%}   <- pitch 台词: 'on {len(labeled)} hand-labeled real errors'")

# 错在哪类 — 告诉你该改提示词还是该改分类表 (§2.5 的工程产出)
# where it fails tells you whether to fix the prompt or the taxonomy
misses = {}
for r in labeled:
    if r["hand_label"].strip() != r["ai_label"]:
        pair = f"{r['hand_label'].strip()} -> AI said {r['ai_label']}"
        misses[pair] = misses.get(pair, 0) + 1
if misses:
    print("\nmisses:")
    for pair, n in sorted(misses.items(), key=lambda x: -x[1]):
        print(f"  {n}x  {pair}")
