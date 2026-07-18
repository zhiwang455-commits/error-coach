"""error-coach 核心逻辑 / core logic.

产品的"心脏"全部在这一个文件里 — UI (app.py) 只是外壳。
Everything that makes the product work lives here — the UI is just a shell.

对应 CLAUDE.md 的 Step 2(分类) 3(CSV) 4(计数) 5(练习题) 7(缓存)。
Maps to blueprint Steps 2 (classify), 3 (CSV), 4 (counter), 5 (practice), 7 (cache).
"""

import csv
import hashlib
import json
import os
from datetime import datetime
from urllib.parse import quote

from openai import OpenAI

# 客户端只创建一次，整个文件共用 / one client, shared by every function below
client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com")

CSV_FILE = "errors.csv"      # 全部历史 = 护城河 / the full history = the moat
CACHE_FILE = "cache.json"    # Step 7: 相同问题不再花钱 / same question never billed twice

# §4 的五个字段 — 定死了就别改，改了历史数据就作废
# the five columns from §4 — locked; changing them invalidates collected data
FIELDS = ["timestamp", "student_id", "error_type", "raw_error", "code_snippet"]

# §5 封闭分类表 — 只在这里维护一份，提示词从它生成
# §5 closed taxonomy — maintained ONCE here; the prompt is generated from it
ERROR_TYPES = ["undefined_variable", "scope_issue", "return_vs_print",
               "type_mismatch", "indentation_error", "index_out_of_range",
               "loop_logic_error", "function_argument_error",
               "dict_list_operation_error", "other"]

# 每种错误的"处方" — 犯第 3 次时弹窗用它告诉学生该学什么。
# 这些文字是教学判断,不是代码 (§8) — 措辞请你们自己审、自己改!
# The "prescription" per error type — the 3rd-time pop-out reads from here.
# This text is teaching JUDGMENT, not code (§8) — review and reword it yourselves!
# 格式 / format: (โฟกัส focus_th, focus_en, 要复习的语法 syntax to review)
LEARN_FOCUS = {
    "undefined_variable": ("ต้องสร้างตัวแปรก่อนใช้ และเช็คตัวสะกดให้ตรงกัน",
        "create a variable before using it; check spelling", "x = value · reading a NameError"),
    "scope_issue": ("ตัวแปรในฟังก์ชันกับนอกฟังก์ชันเป็นคนละตัวกัน",
        "inside a function vs outside are different worlds", "def · return · local vs global"),
    "return_vs_print": ("print แค่โชว์ผลบนจอ แต่ return ส่งค่ากลับไปใช้ต่อได้",
        "print only shows; return hands the value back", "return · result = f() · print(result)"),
    "type_mismatch": ("ข้อความกับตัวเลขบวกกันตรง ๆ ไม่ได้ ต้องแปลงชนิดก่อน",
        "text and numbers don't mix; convert first", "str() · int() · type()"),
    "indentation_error": ("Python ใช้การย่อหน้าบอกว่าโค้ดอยู่บล็อกไหน",
        "indentation IS the block structure", "4 spaces after every line ending with ':'"),
    "index_out_of_range": ("ตำแหน่งในลิสต์เริ่มที่ 0 และไปได้ไกลสุดแค่ len-1",
        "indexes start at 0 and stop at len-1", "list[0] · len() · range(len(list))"),
    "loop_logic_error": ("ลูปวิ่งไม่เท่ากับจำนวนรอบที่ตั้งใจ ลองไล่ทีละรอบ",
        "the loop runs a different count than intended", "for · while · range(start, stop)"),
    "function_argument_error": ("จำนวนและลำดับ argument ต้องตรงกับตอนประกาศฟังก์ชัน",
        "argument count and order must match the def", "def f(a, b) · calling f(1, 2)"),
    "dict_list_operation_error": ("dict ใช้ key แต่ list ใช้ตำแหน่ง วิธีเรียกต่างกัน",
        "dicts use keys, lists use positions", "d[key] · .get() · .append()"),
    "other": ("อ่าน traceback จากบรรทัดล่างสุดขึ้นบน",
        "read the traceback bottom-up", "the last line names the error"),
}

# {types} {code} {error} 是占位符；模板里有 JSON 的 { } 所以不能用 f-string
# placeholders get .replace()d in; literal JSON braces forbid an f-string
PROMPT = """You are a teaching assistant for Thai programming beginners.

Analyze the code and error below. Return ONLY JSON — no other text, no markdown fences.

Category definitions (choose by ROOT CAUSE — the single concept the student most
needs to learn. If two types seem to apply, pick the deeper misunderstanding):
- undefined_variable: uses a name that was never created (often a typo)
- scope_issue: local vs global confusion; right value exists in the wrong scope
- return_vs_print: function prints instead of returning, or a returned value is ignored
- type_mismatch: operation on incompatible types (e.g. str + int)
- indentation_error: wrong or inconsistent indentation
- index_out_of_range: list/string index past its length
- loop_logic_error: loop condition or repetition count is wrong
- function_argument_error: wrong number or order of arguments in a call
- dict_list_operation_error: wrong key/method on a dict or list (e.g. KeyError)
- other: nothing above fits

The thai_explanation and english_explanation must state exactly the same facts.

Format:
{
  "error_type": "exactly one of: [{types}]",
  "thai_explanation": "simple Thai a beginner can understand",
  "english_explanation": "the same explanation in simple English",
  "fix_th": "HOW to fix it, in Thai: the key rule + what to change (e.g. 'if you need a value from inside a function, return it'). Do NOT paste fully corrected code",
  "fix_en": "the same fix in simple English",
  "call_trace": ["step 1", "step 2", "step 3 <- the error is here"],
  "concept": "the concept the student hasn't actually learned"
}

Code:
{code}

Error:
{error}"""


def ask_ai(prompt, temperature=1.0, json_mode=False):
    """唯一直接调 API 的地方 — 以后换供应商只改这一个函数。
    The ONLY function that touches the API — swapping providers = editing here only.

    temperature: 0 = 每次几乎同答案(分类用), 1 = 有创造性(出题用)
                 0 = same answer every time (classification), 1 = creative (practice)
    json_mode: True = API 保证返回合法 JSON — 反馈里带引号也不会再把解析弄崩
               True = the API GUARANTEES valid JSON; quotes inside feedback
               text can no longer break parsing (that bug bit us twice)"""
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(
        model="deepseek-chat",
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return response.choices[0].message.content


def extract_json(text):
    """取第一个 { 到最后一个 } — AI 在外面说的客套话全部忽略。
    First { to last } — whatever chatter the AI wraps around the JSON is ignored."""
    return text[text.find("{"):text.rfind("}") + 1]


def parse_ai_json(raw):
    """解析 AI 返回的 JSON。strict=False 是关键: AI 经常在字符串里写真换行,
    严格模式直接炸 (线上就是这样崩的),宽松模式照单全收。
    Parse AI JSON. strict=False is the key: AI often puts REAL newlines inside
    strings — strict mode explodes (that crashed us in prod), lenient accepts."""
    return json.loads(extract_json(raw), strict=False)


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    # ensure_ascii=False 让泰文以原样存盘，方便人工检查
    # keeps Thai readable in the file instead of ส escape codes
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


def classify(code, error):
    """Step 2 + 7: 分类一个错误。返回 (结果字典, 是否来自缓存)。
    Classify one error. Returns (result dict, served_from_cache)."""
    # 先去掉首尾空白再算指纹 — 多敲一个空格/引号不该算"新问题"
    # trim before fingerprinting — a stray space shouldn't count as a new question
    code, error = code.strip(), error.strip()
    # md5 把 代码+报错 变成短指纹当缓存键 — 完全相同的问题只花一次钱 (§7)
    # md5 fingerprints code+error as the cache key — identical questions cost once
    key = hashlib.md5((code + "\n" + error).encode("utf-8")).hexdigest()
    cache = _load_cache()
    if key in cache:
        return cache[key], True

    prompt = (PROMPT.replace("{types}", ", ".join(ERROR_TYPES))
                    .replace("{code}", code)
                    .replace("{error}", error))
    raw = ask_ai(prompt, temperature=0, json_mode=True)   # 分类要稳定, 不要创造性 / stable, not creative
    try:
        data = parse_ai_json(raw)
    except json.JSONDecodeError:
        # AI 偶尔返回坏 JSON — 重试一次通常就好；两次都坏就让上层报错
        # occasionally the JSON is broken — one retry usually fixes it
        data = parse_ai_json(ask_ai(prompt, temperature=0, json_mode=True))

    # 保险丝：分类不在表里 → 强制 other，脏标签永远进不了 CSV (§5)
    # the fuse: unknown label → "other"; dirty labels never reach the CSV
    if data.get("error_type") not in ERROR_TYPES:
        data["error_type"] = "other"

    cache[key] = data
    _save_cache(cache)
    return data, False


def log_error(student_id, error_type, raw_error, code_snippet, timestamp=None):
    """Step 3: 追加一行到 errors.csv。 Append one row to errors.csv."""
    new_file = not os.path.exists(CSV_FILE)
    # 'a' 追加模式 — 用 'w' 每次会抹掉全部历史，护城河直接消失
    # append mode — 'w' would WIPE the history, killing the entire moat
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
            "student_id": student_id,
            "error_type": error_type,
            "raw_error": raw_error,
            "code_snippet": code_snippet,
        })


def count_times(student_id, error_type):
    """Step 4: 护城河本尊 — 这个学生犯这类错第几次了？
    THE MOAT — how many times has THIS student made THIS type of mistake?"""
    if not os.path.exists(CSV_FILE):
        return 0
    with open(CSV_FILE, encoding="utf-8") as f:
        return sum(1 for row in csv.DictReader(f)
                   if row["student_id"] == student_id
                   and row["error_type"] == error_type)


def review_attempt(problem, code, prior_feedback=None):
    """点评学生对练习题的作答 — 判对错 + 三语反馈;只引导,永不给答案。
    Review one practice attempt: verdict + feedback in th/en/zh, NEVER the answer.

    prior_feedback: 上一次的点评 — 里面可能有 AI 自己出的"加分挑战";
    不传的话,学生完成挑战反而会被当成做错 (参数比题目多了之类)
    the previous review — it may contain an EXTRA CHALLENGE the AI itself
    offered; without it, a student who completes the challenge gets marked
    wrong for 'not matching the original problem'."""
    prompt = (
        "You are a teaching assistant for Thai programming beginners.\n"
        f"Practice problem:\n{problem}\n\n"
        f"Student's attempted code:\n{code}\n\n"
        "Judge the attempt against the problem. Return ONLY JSON, no other text:\n"
        '{"verdict": "correct" or "almost" or "incorrect",\n'
        ' "th": "short feedback in simple Thai",\n'
        ' "en": "the same feedback in simple English",\n'
        ' "zh": "the same feedback in simplified Chinese"}\n'
        "Rules: NEVER include corrected code or the full answer. Name the specific "
        "line or idea that is wrong, then ask ONE guiding question that leads the "
        "student to fix it themselves. If correct, say why it works and suggest "
        "one small extra challenge."
    )
    if prior_feedback:
        prompt += (
            "\n\nYour PREVIOUS feedback to this student on this problem was:\n"
            f"{prior_feedback}\n"
            "If that feedback offered an extra challenge and the new attempt is "
            "answering it, judge the attempt against the CHALLENGE — solving the "
            "challenge counts as correct even where it goes beyond the original "
            "problem statement. Then offer one further challenge."
        )
    raw = ask_ai(prompt, temperature=0, json_mode=True)   # 评卷要稳定 / grading should be stable
    try:
        data = parse_ai_json(raw)
    except json.JSONDecodeError:
        data = parse_ai_json(ask_ai(prompt, temperature=0, json_mode=True))
    # 保险丝: 未知判定一律当"接近" / fuse: unknown verdict → "almost"
    if data.get("verdict") not in ("correct", "almost", "incorrect"):
        data["verdict"] = "almost"
    return data


def tutor_link(code):
    """生成 Python Tutor 链接 — 学生能"亲眼看"电脑一行一行执行自己的代码。
    Build a Python Tutor URL — the student WATCHES the computer run their own code.

    quote() 把代码改写成能放进网址的样子(空格→%20 换行→%0A) — 不转换链接会断。
    quote() rewrites code to survive inside a URL (space→%20, newline→%0A)."""
    return ("https://pythontutor.com/visualize.html#code="
            + quote(code, safe="") + "&py=311&mode=display")


def generate_practice(error_type, concept, avoid=None):
    """Step 5: 3 道练习题 — 一次生成 泰/英/中 三种语言,前端切换语言零成本。
    3 practice problems in Thai+English+Chinese in ONE call — switching is free.

    avoid: 这个学生已经见过的题目 — 明确叫 AI 避开,否则同类型错误常出重复题
    avoid: problems this student already saw — told to the AI explicitly, because
    for the same error type it tends to reinvent the same classic exercises."""
    prompt = (
        "You are a teaching assistant for Thai programming beginners.\n"
        f"A student repeatedly makes this type of Python mistake: {error_type} "
        f"(missing concept: {concept}).\n"
        "Write exactly 3 short practice problems that train this concept, easiest first.\n"
        "Every problem must be SELF-CONTAINED: the problem text alone contains "
        "everything needed to solve it. A fix-the-bug problem is good ONLY if the "
        "complete broken code appears verbatim inside the problem text. NEVER "
        "describe the behavior of code you do not show (e.g. 'when you call it "
        "you get 0') — the student cannot see that code, so the task is unsolvable.\n"
        "All code identifiers (function names, variables) must be in ENGLISH in "
        "every language version — only the surrounding explanation is translated. "
        "Problem text is plain sentences; you may use `inline code` and ``` code "
        "blocks, but never ** bold markers.\n"
        "Each problem has 2 progressive hints written as guiding QUESTIONS that lead\n"
        "step by step. NEVER include the answer or any solution code.\n"
        "Return ONLY JSON, no other text, exactly this shape (same 3 problems in all\n"
        "3 languages — th Thai, en simple English, zh simplified Chinese):\n"
        '{"problems": [{"th": {"problem": "...", "hints": ["...", "..."]},\n'
        '               "en": {"problem": "...", "hints": ["...", "..."]},\n'
        '               "zh": {"problem": "...", "hints": ["...", "..."]}}]}'
    )
    if avoid:
        prompt += ("\nThe student ALREADY did these — write clearly DIFFERENT "
                   "problems (different story, different data):\n- " + "\n- ".join(avoid))
    raw = ask_ai(prompt, json_mode=True)
    try:
        return parse_ai_json(raw)["problems"]
    except json.JSONDecodeError:
        # 坏 JSON 重试一次 — 和 classify() 同一招 / one retry, same trick as classify()
        return parse_ai_json(ask_ai(prompt, json_mode=True))["problems"]
