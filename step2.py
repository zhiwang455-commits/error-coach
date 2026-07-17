
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com")

ERROR_TYPES = ["undefined_variable", "scope_issue", "return_vs_print",
               "type_mismatch", "indentation_error", "index_out_of_range",
               "loop_logic_error", "function_argument_error",
               "dict_list_operation_error", "other"]

PROMPT = """You are a teaching assistant for Thai programming beginners.

Analyze the code and error below. Return ONLY JSON — no other text, no markdown fences.

Format:
{
  "error_type": "exactly one of: [undefined_variable, scope_issue, return_vs_print, type_mismatch, indentation_error, index_out_of_range, loop_logic_error, function_argument_error, dict_list_operation_error, other]",
  "thai_explanation": "simple Thai a beginner can understand",
  "english_explanation": "the same explanation in simple English",
  "call_trace": ["step 1", "step 2", "step 3 <- the error is here"],
  "concept": "the concept the student hasn't actually learned"
}

Code:
{code}

Error:
{error}"""

def extract_json(text):
    # 取第一个 { 到最后一个 } / first { to last } — chatter outside is ignored
    return text[text.find("{"):text.rfind("}") + 1]

test_code = "def add(a, b):\n    print(a + b)\n\ntotal = add(1, 2) + 10"
test_error = "TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'"

prompt = PROMPT.replace("{code}", test_code).replace("{error}", test_error)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": prompt}],
)

raw = response.choices[0].message.content
data = json.loads(extract_json(raw))          # 字符串 → 字典 / string → dict
if data["error_type"] not in ERROR_TYPES:     # 保险丝 / the fuse
    data["error_type"] = "other"

print("type    :", data["error_type"])
print("concept :", data["concept"])
print("thai    :", data["thai_explanation"])
print("english :", data["english_explanation"])
