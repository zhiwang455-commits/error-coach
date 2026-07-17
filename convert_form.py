"""把 Google Form 导出的 CSV 变成正式数据 / Google Form export -> real data.

用法 / usage:
  1. 表单回应表格: File -> Download -> CSV, 存成 ~/error-coach/form_responses.csv
  2. (建议先删掉演示数据 / delete demo data first):  rm errors.csv cache.json
  3. ./venv/bin/python convert_form.py

做三件事 / does three things:
  - 昵称 -> student_01... (匿名化, 真名/昵称绝不进 errors.csv)
  - 每条错误跑一次 AI 分类, 写入 errors.csv  (约 40 次调用, 几分钱)
  - 生成 labeling_sheet.csv 给你人工标注 -> eval.py 算准确率 (§2.5)
"""

import csv
import sys

import coach

SRC = "form_responses.csv"

# Google 导出的列顺序 = 表单题目顺序: 0=时间戳 1=昵称 2=代码 3=报错 (4=可选说明)
# column order mirrors the form: timestamp, nickname, code, error, (optional note)
try:
    with open(SRC, encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]  # [1:] 跳过表头 / skip the header row
except FileNotFoundError:
    sys.exit(f"找不到 {SRC} / not found — download it from the form's Google Sheet first")

nick_to_id = {}  # 只存在内存和打印输出里, 不落盘 / mapping never written to disk


def student_id(nickname):
    nick = nickname.strip().lower()
    if nick not in nick_to_id:
        nick_to_id[nick] = f"student_{len(nick_to_id) + 1:02d}"
    return nick_to_id[nick]


with open("labeling_sheet.csv", "w", newline="", encoding="utf-8") as f:
    sheet = csv.writer(f)
    # hand_label 留空 — 你自己读代码手工填, 这是 ground truth (§2.5)
    # hand_label stays empty — YOU fill it by reading each error; that's ground truth
    sheet.writerow(["row", "code_snippet", "raw_error", "ai_label", "hand_label"])

    for i, row in enumerate(rows, 1):
        ts, nick, code, error = row[0], row[1], row[2], row[3]
        data, cached = coach.classify(code, error)
        coach.log_error(student_id(nick), data["error_type"], error, code,
                        timestamp=ts)
        sheet.writerow([i, code, error, data["error_type"], ""])
        print(f"{i:>3}/{len(rows)}  {data['error_type']:<28}"
              f"{'(cache)' if cached else ''}")

print("\n昵称对照表 (自己留档, 不要提交) / nickname map (keep private):")
for nick, sid in nick_to_id.items():
    print(f"  {sid} = {nick}")
print(f"\n完成 / done: {len(rows)} rows -> errors.csv + labeling_sheet.csv")
print("下一步 / next: 打开 labeling_sheet.csv 填 hand_label 列, 然后跑 eval.py")
