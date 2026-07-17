import os
from openai import OpenAI

# คีย์ถูกอ่านจาก .bashrc — ไม่เขียนคีย์ลงไฟล์ / key comes from .bashrc, never this file
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com",
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "Say hello in Thai and English, one sentence."}
    ],
)

print(response.choices[0].message.content)
