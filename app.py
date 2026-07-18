"""error-coach 界面 / UI — 外壳，不含业务逻辑，全部逻辑在 coach.py。
The shell. No business logic here — everything real lives in coach.py.

运行 / run:  ./venv/bin/streamlit run app.py
"""

import os
from urllib.parse import quote

import altair as alt   # Streamlit 自带的画图库 — 不加 .interactive() 图就是静态的,不会误触缩放
import pandas as pd    # altair ships with Streamlit; charts without .interactive() cannot zoom
import streamlit as st

import coach

st.set_page_config(page_title="error-coach", page_icon="🧭", layout="centered")
# 校徽 — st.logo 固定显示在页面左上角,图已抠好透明底,金色在深色主题上正好
# college emblem — st.logo pins it top-left; transparent PNG, gold suits dark mode
st.logo("college_logo.png", size="large")

# 页面顶部居中的队徽 connect — 转成 base64 塞进 HTML,才能用 CSS 类控制居中和变色
# team logo top-center; base64-inlined so a CSS class can center + recolor it
import base64
with open("connect_logo.png", "rb") as f:
    _logo64 = base64.b64encode(f.read()).decode()
st.markdown(
    f'<div style="text-align:center;margin:0 0 6px">'
    f'<img class="connect-logo" src="data:image/png;base64,{_logo64}" width="320"></div>',
    unsafe_allow_html=True)

# —— MATRIX 模式 / matrix mode ————————————————————————————————
# 一个开关切换全站主题;下面所有颜色都从这组变量取,图表跟着一起变色
# one switch retints the whole site; charts read these variables too
matrix = st.toggle("MATRIX MODE", key="matrix_mode")
if matrix:
    C_ACC, C_SEC = "#00FF41", "#1B8A3A"      # 图表: 主色荧光绿 / 次色暗绿
    C_INK, C_CELL, C_DIM = "#B6FFC5", "#0E3D1C", "#66D97F"
    CURSOR_GLOW, CURSOR_EDGE = "#00FF41", "#008F11"
    SPARK_GLYPHS, SPARK_COLOR = ["0", "1"], ("#00FF41", "#00FF41")
else:
    C_ACC, C_SEC = "#FFB454", "#83c9ff"
    C_INK, C_CELL, C_DIM = "#F4F1E8", "#2f4a63", "#D7ECFF"
    CURSOR_GLOW, CURSOR_EDGE = "#a855f7", "#7c3aed"
    SPARK_GLYPHS = ["\U0001F49C", "\U0001F90D", "\U0001F495", "♡"]
    SPARK_COLOR = ("#c084fc", "#a855f7")

if matrix:
    # 全站换装: 黑底 + 荧光绿 + 等宽"黑客"字体 + 微微发光
    # full restyle: black, neon green, monospace hacker font, soft glow
    st.markdown("""<style>
    .stApp, [data-testid="stHeader"] {background:#000 !important}
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp small,
    .stApp [data-testid="stMetricValue"], .stApp [data-testid="stMetricLabel"] {
        color:#00FF41 !important;
        font-family:"Courier New", monospace !important;
        text-shadow:0 0 6px rgba(0,255,65,.35);
    }
    .stApp textarea, .stApp input, .stApp [data-baseweb="select"] > div {
        background:#020D04 !important; color:#00FF41 !important;
        border:1px solid #0F5C23 !important; font-family:"Courier New",monospace !important;
    }
    .stApp button {
        background:#020D04 !important; color:#00FF41 !important;
        border:1px solid #00FF41 !important;
    }
    .unicorn-dots {filter:hue-rotate(205deg) saturate(1.6)}  /* 独角兽也变绿 */
    /* 队徽变绿: 白色本身转不了色,先 sepia 上色再转到绿 + 荧光
       white can't hue-rotate (no color in it) — sepia tints it first, then rotate to green */
    .connect-logo {filter:brightness(.85) sepia(1) hue-rotate(85deg) saturate(4)
                   brightness(1.15) drop-shadow(0 0 10px rgba(0,255,65,.45));}
    /* 图标是"图标字体"画的(span 里其实是文字 keyboard_arrow_right) —
       上面强制 Courier 会把它变回原文压在标签上,这里把图标字体还回去
       icons are an ICON FONT (the span literally contains its name);
       forcing Courier broke the ligature — restore the icon font here */
    .stApp [data-testid="stIconMaterial"],
    .stApp span[class*="material-symbols"] {
        font-family:"Material Symbols Rounded" !important;
        text-shadow:none !important;
    }
    </style>""", unsafe_allow_html=True)
# 右上角闪烁的"点阵独角兽" — 由 build_unicorn.py 从校徽取样生成,纯 CSS 动画零性能负担
# the twinkling dot-unicorn in the top-right — sampled from the emblem by
# build_unicorn.py; pure CSS animation, no JS, costs nothing
with open("unicorn_dots.html", encoding="utf-8") as f:
    _unicorn = f.read()
# 开场秀只演一次 — 之后每次重跑都直接定格紫色,绝不再闪 (闪多了会干扰使用)
# the entrance show plays ONCE per visit; every rerun after that renders the
# unicorn frozen in purple — repeated flashing would distract the student
if st.session_state.get("unicorn_played"):
    _unicorn += ("<style>.unicorn-dots i{animation:none!important;"
                 "opacity:.85;filter:hue-rotate(225deg) saturate(1.2)}</style>")
st.session_state.unicorn_played = True
st.markdown(_unicorn, unsafe_allow_html=True)

# 紫光鼠标 — 浏览器不能给系统光标加光,但 CSS 可以把光标"换成"一张自带紫色光晕的
# SVG 箭头图。cursor: url(图, 热点x 热点y), auto — auto 是图加载失败时的后备
# purple-glow cursor: CSS swaps the arrow for an SVG that carries its own glow;
# the two numbers are the "hotspot" (which pixel actually clicks); auto = fallback
_arrow = quote(f"""<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28">
<filter id="g"><feGaussianBlur stdDeviation="1.6"/></filter>
<path d="M4 2 L4 22 L9.2 17.5 L12.6 25 L15.8 23.5 L12.4 16.2 L19 16 Z"
 fill="{CURSOR_GLOW}" filter="url(#g)" opacity=".9"/>
<path d="M5 3 L5 20 L9.5 16.3 L12.7 23 L14.8 22 L11.7 15.2 L17.5 15 Z"
 fill="#fff" stroke="{CURSOR_EDGE}" stroke-width="1"/></svg>""")
st.markdown(f"""<style>
.stApp, .stApp * {{cursor: url('data:image/svg+xml,{_arrow}') 5 3, auto}}
textarea, input {{cursor: text !important}}      /* 打字区仍是文字光标 / typing areas */
button, [role="tab"], a, summary {{cursor: pointer !important}}  /* 可点的仍是手型 */
</style>""", unsafe_allow_html=True)

# 星尘拖尾 — st.markdown 会拦掉 <script>,所以借一个 0 高的组件 iframe 运行 JS;
# iframe 和主页面同源,能拿到 window.parent 去操作真正的页面
# stardust trail — st.markdown blocks <script>, so a 0-height component iframe
# runs the JS; it is same-origin, so window.parent reaches the real page
import json as _json
import streamlit.components.v1 as components
_spark_js = """<script>
const P = window.parent;
// 每次重跑都更新粒子样式 — Matrix 开关一按,新粒子立刻变成绿色的 0 和 1
// refreshed on every rerun — flipping Matrix mode changes new particles instantly
P.__sdGlyphs = __GLYPHS__;
P.__sdColors = __SDCOLORS__;
// 只挂一次监听 + 尊重"减少动态"系统设置 / attach once; honor reduced-motion
if (!P.__stardust && !P.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  P.__stardust = true;
  const doc = P.document;
  const st = doc.createElement('style');
  st.textContent = `@keyframes sd-fade{from{opacity:.95;transform:translate(0,0) rotate(0) scale(1)}
    to{opacity:0;transform:translate(var(--dx),22px) rotate(var(--rot)) scale(.3)}}`;
  doc.head.appendChild(st);
  let last = 0;
  doc.addEventListener('mousemove', e => {
    const now = performance.now();
    if (now - last < 45) return;   // 限流: 最多每 45ms 一颗心,不拖慢页面 / throttle
    last = now;
    const s = doc.createElement('div');
    const glyphs = P.__sdGlyphs;   // 普通=爱心, Matrix=0/1 / hearts normally, 0/1 in Matrix
    s.textContent = glyphs[Math.random()*glyphs.length|0];
    s.style.cssText = `position:fixed;left:${e.clientX + Math.random()*12 - 6}px;
      top:${e.clientY + Math.random()*12 - 6}px;pointer-events:none;z-index:99999;
      font-size:${9 + Math.random()*8}px;color:${P.__sdColors[0]};
      text-shadow:0 0 6px ${P.__sdColors[1]};--dx:${Math.random()*28 - 14}px;
      --rot:${Math.random()*50 - 25}deg;
      animation:sd-fade ${0.7 + Math.random()*0.5}s ease-out forwards`;
    doc.body.appendChild(s);
    setTimeout(() => s.remove(), 1300);   // 心燃尽即删除,页面不积垃圾 / clean up
  });
}
</script>"""
# json.dumps 把 Python 列表变成合法的 JS 数组写进脚本 / lists → JS arrays safely
components.html(_spark_js.replace("__GLYPHS__", _json.dumps(SPARK_GLYPHS))
                         .replace("__SDCOLORS__", _json.dumps(list(SPARK_COLOR))),
                height=0)

# —— Matrix 数字雨 / digital rain ——————————————————————————————
# 开关打开 → 造一块全屏画布画绿色字符雨; 关掉 → 删画布停计时器
# on → full-screen canvas of falling green glyphs; off → canvas removed
components.html(("""<script>
const P = window.parent, doc = P.document, ON = __ON__;
let c = doc.getElementById('mx-rain');
if (ON && !c && !P.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  c = doc.createElement('canvas'); c.id = 'mx-rain';
  // 盖在页面上但只有 14% 不透明度,内容照样能读; 点击穿透
  // overlays the page at 14% opacity — content stays readable, clicks pass through
  c.style.cssText = 'position:fixed;inset:0;z-index:9990;pointer-events:none;opacity:.14';
  doc.body.appendChild(c);
  const ctx = c.getContext('2d');
  const size = () => { c.width = P.innerWidth; c.height = P.innerHeight; };
  size(); P.addEventListener('resize', size);
  const chars = 'アイウエオカキクケコサシスセソ01234567890101';
  const fs = 16; let drops = [];
  P.__mxTimer = setInterval(() => {
    const n = Math.ceil(c.width / fs);
    while (drops.length < n) drops.push(Math.random() * -60);
    drops.length = n;
    // 每帧铺一层半透明黑 → 旧字符渐渐淡出,形成拖尾 / translucent black = the fading tail
    ctx.fillStyle = 'rgba(0,0,0,0.08)'; ctx.fillRect(0, 0, c.width, c.height);
    ctx.fillStyle = '#00FF41'; ctx.font = fs + 'px monospace';
    for (let i = 0; i < drops.length; i++) {
      ctx.fillText(chars[Math.random() * chars.length | 0], i * fs, drops[i] * fs);
      if (drops[i] * fs > c.height && Math.random() > 0.975) drops[i] = 0;
      drops[i]++;
    }
  }, 50);
}
if (!ON && c) { clearInterval(P.__mxTimer); c.remove(); }
</script>""").replace("__ON__", "true" if matrix else "false"), height=0)

# —— Matrix 光标时钟 / cursor clock (90s classic, matrix green) ——————
# 日期文字绕着光标转圈,中间是真会走的时/分/秒针 — 全部荧光绿
# the date orbits the cursor; real hour/minute/second hands tick — all neon green
components.html(("""<script>
const P = window.parent, doc = P.document, ON = __ON__;
let cv = doc.getElementById('mx-clock');
if (ON && !cv && !P.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  cv = doc.createElement('canvas'); cv.id = 'mx-clock';
  cv.style.cssText = 'position:fixed;inset:0;z-index:99998;pointer-events:none';
  doc.body.appendChild(cv);
  const ctx = cv.getContext('2d');
  const size = () => { cv.width = P.innerWidth; cv.height = P.innerHeight; };
  size(); P.addEventListener('resize', size);
  let tx = P.innerWidth/2, ty = P.innerHeight/2, x = tx, y = ty;
  P.__mxcMove = e => { tx = e.clientX; ty = e.clientY; };
  doc.addEventListener('mousemove', P.__mxcMove);
  const G = '#00FF41';
  const hand = (ang, len, w, alpha) => {   // 一根表针 / one clock hand
    ctx.beginPath(); ctx.lineWidth = w; ctx.lineCap = 'round';
    ctx.strokeStyle = `rgba(0,255,65,${alpha})`;
    ctx.moveTo(x, y); ctx.lineTo(x + Math.sin(ang)*len, y - Math.cos(ang)*len);
    ctx.stroke();
  };
  const step = () => {
    // 光标缓动追踪 — 90 年代那种飘飘的跟随感 / eased follow = the floaty 90s feel
    x += (tx-x)*0.2; y += (ty-y)*0.2;
    ctx.clearRect(0, 0, cv.width, cv.height);
    const now = new Date();
    ctx.shadowColor = G; ctx.shadowBlur = 6;   // 荧光 / the neon glow
    // 日期文字沿圆圈排一圈,整体缓慢旋转 / date characters on a slowly spinning ring
    const txt = now.toDateString().toUpperCase() + ' * ';
    const rot = performance.now()/6000, R = 44;
    ctx.fillStyle = G; ctx.font = '11px monospace';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    for (let i = 0; i < txt.length; i++) {
      const a = rot + i/txt.length * 2*Math.PI;
      ctx.save();
      ctx.translate(x + Math.sin(a)*R, y - Math.cos(a)*R);
      ctx.rotate(a);                     // 每个字符转到与圆相切 / chars tangent to ring
      ctx.fillText(txt[i], 0, 0);
      ctx.restore();
    }
    // 三根真实时间的表针 / three hands showing the REAL time
    const s = now.getSeconds() + now.getMilliseconds()/1000;
    const m = now.getMinutes() + s/60, h = (now.getHours()%12) + m/60;
    hand(h/12*2*Math.PI, 16, 2.5, .9);   // 时针短而粗 / hour: short, thick
    hand(m/60*2*Math.PI, 24, 1.5, .8);   // 分针 / minute
    hand(s/60*2*Math.PI, 30, 1,  1);     // 秒针长而亮,会平滑扫动 / second: sweeps
    ctx.beginPath(); ctx.fillStyle = G;  // 中心点 / center dot
    ctx.arc(x, y, 2, 0, 2*Math.PI); ctx.fill();
    ctx.shadowBlur = 0;
    P.__mxcRAF = P.requestAnimationFrame(step);
  };
  step();
}
if (!ON && cv) {
  P.cancelAnimationFrame(P.__mxcRAF);
  doc.removeEventListener('mousemove', P.__mxcMove);
  cv.remove();
}
</script>""").replace("__ON__", "true" if matrix else "false"), height=0)

# 只给图表用的"好看名字" — CSV 里永远存 snake_case 原名,闭表 (§5) 一个字都不动
# pretty DISPLAY names for charts only — the CSV keeps the raw snake_case taxonomy
PRETTY = {
    "undefined_variable": "undefined variable",
    "scope_issue": "scope issue",
    "return_vs_print": "return vs print",
    "type_mismatch": "type mismatch",
    "indentation_error": "indentation",
    "index_out_of_range": "index out of range",
    "loop_logic_error": "loop logic",
    "function_argument_error": "function arguments",
    "dict_list_operation_error": "dict / list operation",
    "other": "other",
}

# 练习题的三种语言: 按钮文字 → (JSON里的键, "提示"这个词的说法)
# the three practice languages: button label → (key in the JSON, the word for "hint")
LANGS = {"ไทย": ("th", "คำใบ้"), "English": ("en", "Hint"), "中文": ("zh", "提示")}


def show_practice(where):
    """显示练习题 + 语言切换。where 用来给两处控件起不同名字,Streamlit 不许重名。
    Renders practice + language switch. `where` keeps the widget ids unique —
    Streamlit forbids two widgets with the same identity (dialog vs page)."""
    # segmented_control = 一排可选按钮 — 三种语言当场切换,不再调 API
    # a row of toggle buttons — switching languages costs zero API calls
    # 旧版练习题是纯文本 — 万一浏览器里还留着,直接原样显示,不让页面崩
    # old-format practice was plain text — if one lingers in the session, just show it
    if isinstance(st.session_state.practice, str):
        st.markdown(st.session_state.practice)
        return
    choice = st.segmented_control("ภาษา / Language / 语言", list(LANGS),
                                  default="ไทย", key=f"lang_{where}")
    lang, hint_word = LANGS[choice or "ไทย"]   # 取消选择时退回泰语 / deselect → Thai
    for i, p in enumerate(st.session_state.practice, 1):
        st.markdown(f"**{i}. {p[lang]['problem']}**")
        # 提示藏进折叠框 — 先自己想,卡住才点开 (§8.5: 引导,不给答案)
        # hints live in expanders — think first, open only when stuck
        for j, hint in enumerate(p[lang]["hints"], 1):
            with st.expander(f"{hint_word} {j}"):
                st.write(hint)
        # 每道题一个作答框 — 写完点检查,AI 只点评引导,不给正确答案
        # one answer box per problem; the AI reviews and guides, never solves
        attempt = st.text_area("เขียนโค้ดของคุณ / Write your code / 写你的代码",
                               key=f"attempt_{where}_{i}", height=120)
        if st.button("ตรวจโค้ด / Check my code", key=f"check_{where}_{i}",
                     disabled=not attempt.strip()):
            with st.spinner("กำลังตรวจ / checking..."):
                # 用英文题干送审最稳,反馈会按上面选的语言显示
                # review against the English problem text; feedback follows the switch
                st.session_state[f"fb_{where}_{i}"] = coach.review_attempt(
                    p["en"]["problem"], attempt)
        fb = st.session_state.get(f"fb_{where}_{i}")
        if fb:
            # 对/接近/不对 → 绿/黄/红 三种框 / verdict picks the box color
            box = {"correct": st.success, "almost": st.warning,
                   "incorrect": st.error}[fb["verdict"]]
            box(fb.get(lang) or fb["en"])
        st.divider()


def make_practice(data):
    """出一套新题,并记住出过什么 — 下次生成时叫 AI 避开,保证题目不重样。
    Generate a fresh set AND remember it — next time the AI is told to avoid these.

    setdefault: 键不存在就先建一个空列表 / create the list on first use
    只回传最近 6 题 — 提示词太长又贵又乱 / only the last 6 go back: prompts cost money"""
    seen = st.session_state.setdefault("seen_problems", [])
    st.session_state.practice = coach.generate_practice(
        data["error_type"], data["concept"], avoid=seen[-6:])
    seen.extend(p["th"]["problem"] for p in st.session_state.practice)
    # 新题目 → 旧的作答和点评全部清掉 / new set → wipe old answers and feedback
    for k in [k for k in st.session_state
              if str(k).startswith(("fb_", "attempt_"))]:
        del st.session_state[k]
# 倒转字母版标题 — 每个字母换成 Unicode 里的"倒立字符",再倒序排列
# upside-down title: each letter swapped for its flipped Unicode twin, order reversed
st.title("ɥɔɐoɔ-ɹoɹɹǝ")
st.caption("ChatGPT forgives and forgets. We just... don't forget. Sleep well. ¬‿¬")

# 学生页 / 老师页 两个标签 (§8: input box / result card / teacher view)
tab_student, tab_teacher = st.tabs(["นักเรียน · Student", "อาจารย์ · Professor"])


# ------------------------------------------------------- ⚠️ 第3次弹窗 / 3rd-time pop-out
# @st.dialog 是装饰器: 把下面的函数变成"弹窗" — 调用函数那一刻弹窗打开 (demo 的高潮 §9)
# @st.dialog is a decorator: it turns this function into a modal — calling it opens it
@st.dialog("⚠️ จุดที่ต้องตั้งใจ / Pay attention here")
def repeat_alert():
    last = st.session_state.last
    data, n = last["data"], last["n"]
    # .get(键, 默认值): 万一类型不在处方表里就用 "other" 的,弹窗永不崩
    # .get(key, default): unknown type falls back to "other" — the dialog never crashes
    th, en, study = coach.LEARN_FOCUS.get(data["error_type"], coach.LEARN_FOCUS["other"])
    st.error(f"นี่คือครั้งที่ {n} ของ **{data['error_type']}** — "
             "พลาด 1 ครั้งคือเผลอ แต่ 3 ครั้งคือยังไม่เข้าใจจริง / "
             "once is a slip, three times is a concept gap.")
    st.markdown(f"🎯 **โฟกัสที่ / Focus on:** {th}\n\n_{en}_")
    st.markdown(f"📖 **ทบทวนไวยากรณ์นี้ / Review this syntax:** `{study}`")
    st.markdown(f"💡 **ในโค้ดของคุณ / In your code specifically:** {data['concept']}")
    # st.link_button 在新标签页打开外部网站 / opens an external site in a new tab
    st.link_button("🐍 ดูคอมพิวเตอร์คิดทีละบรรทัด / Watch the computer run your code (Python Tutor)",
                   coach.tutor_link(last["code"]))
    # 弹窗内的按钮只重跑弹窗自己(fragment), 弹窗不会因此关闭
    # a button INSIDE a dialog reruns only the dialog itself — it stays open
    if st.button("✏️ สร้างโจทย์ฝึกเฉพาะจุดนี้ / Make practice for exactly this"):
        with st.spinner("กำลังสร้างโจทย์ / writing problems..."):
            make_practice(data)
    if "practice" in st.session_state:
        show_practice("dialog")

# ---------------------------------------------------------------- student tab
with tab_student:
    # 匿名代号，不用真名 (§4) / anonymous IDs, never real names
    student_id = st.selectbox(
        "คุณคือใคร / Who are you?",
        [f"student_{i:02d}" for i in range(1, 9)],
    )
    code = st.text_area("วางโค้ดของคุณ / Paste your Python code", height=160)
    error = st.text_area("วางข้อความ error / Paste the full error message", height=110)

    if st.button("🔍 อธิบาย error / Explain my error",
                 disabled=not (code.strip() and error.strip())):
        with st.spinner("กำลังวิเคราะห์ / analyzing..."):
            try:
                data, cached = coach.classify(code, error)
            except Exception as exc:  # 坏 JSON 重试后仍失败等 / API or parse failure
                st.error(f"วิเคราะห์ไม่สำเร็จ / analysis failed: {exc}")
                st.stop()
        # 先数历史再写入 → n 就是"这是第几次" / count BEFORE logging → n = "Nth time"
        n = coach.count_times(student_id, data["error_type"]) + 1
        coach.log_error(student_id, data["error_type"], error, code)
        # 存进 session_state：Streamlit 每次点击都重跑脚本，不存就丢了
        # Streamlit re-runs this whole script on every click — state must be saved
        # 多存一份 code — 弹窗要用它生成 Python Tutor 链接
        # also keep the code — the pop-out needs it for the Python Tutor link
        st.session_state.last = {"data": data, "cached": cached, "n": n, "code": code}
        st.session_state.pop("practice", None)  # 新错误 → 旧练习题作废
        # 到达第 3 次 → 当场弹窗,不等学生自己发现 / hit the 3rd time → pop out NOW
        if n >= 3:
            repeat_alert()

    if "last" in st.session_state:
        data = st.session_state.last["data"]
        n = st.session_state.last["n"]

        # demo 的高潮台词 (§9) / the climax line of the demo
        if n >= 3:
            st.error(f"⚠️ นี่คือครั้งที่ {n} ของคุณ — This is your **{n}th time** "
                     f"making a **{data['error_type']}** mistake!")
        elif n == 2:
            st.warning(f"ครั้งที่ 2 / 2nd time: **{data['error_type']}**")
        else:
            st.info(f"ประเภท / type: **{data['error_type']}**")

        st.subheader("คำอธิบาย / Explanation")
        st.write("🇹🇭 " + data["thai_explanation"])
        st.write("🇬🇧 " + data["english_explanation"])

        # 学生最需要的一句话:怎么改 — 用醒目的琥珀色 (:orange[] 是 st.markdown 的着色语法)
        # the line students actually need: HOW TO FIX — in eye-catching amber
        # 旧缓存里没有 fix 字段 → 用处方表 LEARN_FOCUS 兜底,页面永不空白
        # old cache entries lack fix fields → the LEARN_FOCUS prescriptions fill in
        focus = coach.LEARN_FOCUS.get(data["error_type"], coach.LEARN_FOCUS["other"])
        st.subheader("วิธีแก้ / How to fix")
        st.markdown(f"🔑 :orange[**{data.get('fix_th') or focus[0]}**]")
        st.markdown(f":orange[{data.get('fix_en') or focus[1]}]")

        st.subheader("ลำดับเหตุการณ์ / What happened, step by step")
        for i, step in enumerate(data["call_trace"], 1):
            # 出错的那一步标红加粗 — 一眼锁定问题 / the failing step in bold red
            if "error is here" in step or "←" in step or "<-" in step:
                st.markdown(f"{i}. :red[**{step}**]")
            else:
                st.write(f"{i}. {step}")

        st.subheader("แนวคิดที่ต้องเรียน / The concept to learn")
        st.markdown(f"💡 :violet[**{data['concept']}**]")

        if st.session_state.last["cached"]:
            st.caption("♻️ served from cache — no API call, zero cost (§7)")

        # 任何次数都能练 — 犯 1 次也想自测的学生不该被拦住 (原来只在 ≥2 次时显示)
        # practice at ANY count — a student who wants to self-test after 1 mistake
        # shouldn't be blocked (this used to require n >= 2)
        if st.button("✏️ สร้างโจทย์ฝึก / Generate practice problems"):
            with st.spinner("กำลังสร้างโจทย์ / writing problems..."):
                make_practice(data)
        if "practice" in st.session_state:
            st.subheader("โจทย์ฝึก / Practice problems")
            show_practice("page")

# ---------------------------------------------------------------- teacher tab
with tab_teacher:
    if not os.path.exists(coach.CSV_FILE):
        st.info("ยังไม่มีข้อมูล / No errors logged yet.")
    else:
        df = pd.read_csv(coach.CSV_FILE)
        counts = df["error_type"].value_counts()

        # 一句话诊断 (§6 teacher view) / the one-sentence diagnosis
        top_two = counts.head(2)
        pct = int(round(top_two.sum() / len(df) * 100))
        # .get(t, t): 万一出现表外类型就原样显示,不崩 / unknown type shows as-is, no crash
        names = " and ".join(f"**{PRETTY.get(t, t)}**" for t in top_two.index)
        st.markdown(f"### {pct}% of all errors are {names}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Errors logged", len(df))
        c2.metric("Students", df["student_id"].nunique())
        # cache.json 里每条 = 一次真实 API 调用 → 差值就是省下的钱 (§7)
        # each cache entry = one real API call → the gap is the money saved
        api_calls = len(coach._load_cache())
        c3.metric("Unique AI analyses", api_calls,
                  help="Repeat questions are served from cache at zero cost.")

        # st.bar_chart 自带缩放/平移,手机一误触图就拉坏 → 换 Altair 静态图,顺便统一成 pitch 风格
        # st.bar_chart ships with zoom/pan — one mistouch wrecks it. Static Altair, pitch-deck style.
        st.subheader("ความถี่ตามประเภท / Errors by type")
        type_df = counts.rename_axis("error_type").reset_index(name="count")
        # 换成带图标的显示名 / swap in the icon display names (chart only, data untouched)
        type_df["error_type"] = type_df["error_type"].map(lambda t: PRETTY.get(t, t))
        # value_counts 已按多→少排好 → 前 3 行就是"卡住区",涂琥珀色 (和 deck 同一套视觉)
        # value_counts is sorted desc → first 3 rows ARE the stuck zone; amber like the deck
        type_df["zone"] = ["stuck zone (top 3)" if i < 3 else "others"
                           for i in range(len(type_df))]
        bars = (alt.Chart(type_df)
                .mark_bar(cornerRadiusEnd=4)
                # 横条 → 错误类型名横着放,好读 / horizontal bars → type names read naturally
                # paddingInner=0.45: 条与条之间留 45% 空隙,不再挤成一团
                # 45% breathing room between bars — no more cramming
                .encode(y=alt.Y("error_type:N", sort="-x", title=None,
                                axis=alt.Axis(labelColor=C_INK, labelFontSize=14,
                                              labelFontWeight=600, labelLimit=260),
                                scale=alt.Scale(paddingInner=0.45)),
                        x=alt.X("count:Q", axis=None),
                        color=alt.Color("zone:N", title=None,
                                        scale=alt.Scale(domain=["stuck zone (top 3)", "others"],
                                                        range=[C_ACC, C_SEC]))))
        # 数字直接标在条尾 — 不用悬浮就看得见 / value at the bar end, no hover needed
        labels = bars.mark_text(align="left", dx=6).encode(text="count:Q",
                                                           color=alt.value(C_INK))
        # alt.Step(44): 不定总高度,而是"每一行固定 44px" — 7 种错误就自动 7×44 高,
        # 行数再多标签也不会被挤到消失 / 44px PER ROW — labels can never be squeezed out
        st.altair_chart((bars + labels).properties(height=alt.Step(44))
                        .configure_view(strokeWidth=0),
                        use_container_width=True)

        # 谁在哪种错误上犯了几次 — 行=错误类型(文字横排好读), 列=学生
        # who is stuck where — rows = error types (horizontal, readable), columns = students
        st.subheader("ใครติดตรงไหน / Who is stuck where")
        grid = df.groupby(["error_type", "student_id"]).size().reset_index(name="count")
        grid["error_type"] = grid["error_type"].map(lambda t: PRETTY.get(t, t))
        hot = alt.datum.count >= 3   # ⚠️ 第3次红线 — 产品的核心时刻 / the 3rd-time line
        cells = (alt.Chart(grid)
                 .mark_rect(cornerRadius=6)
                 .encode(x=alt.X("student_id:N", title=None,
                                 # orient="top": 学生号放上面 · labelExpr 把 student_01 缩成 01
                                 # header on top; labelExpr shortens student_01 → 01
                                 axis=alt.Axis(orient="top", labelAngle=0, labelColor=C_DIM,
                                               labelExpr="replace(datum.label,'student_','')"),
                                 scale=alt.Scale(paddingInner=0.15)),
                         y=alt.Y("error_type:N", title=None,
                                 sort=alt.EncodingSortField("count", op="sum", order="descending"),
                                 axis=alt.Axis(labelColor=C_INK, labelFontSize=14,
                                               labelFontWeight=600, labelLimit=260),
                                 scale=alt.Scale(paddingInner=0.2)),
                         # 到达 3 次 → 琥珀色警报, 其余 → 蓝色 / ≥3 amber alarm, else blue
                         color=alt.condition(hot, alt.value(C_ACC), alt.value(C_CELL))))
        nums = cells.mark_text(fontWeight="bold", fontSize=14).encode(
            text="count:Q",
            color=alt.condition(hot, alt.value("#14161F"), alt.value(C_DIM)))
        # 每行固定 46px — 类型再多也每行清清楚楚 / 46px per row, always readable
        st.altair_chart((cells + nums).properties(height=alt.Step(46))
                        .configure_view(strokeWidth=0),
                        use_container_width=True)
        st.caption("3 ครั้งขึ้นไป = ยังไม่เข้าใจคอนเซ็ปต์ / 3+ times = a concept gap, not a slip")

        with st.expander("ดูข้อมูลดิบ / raw data"):
            st.dataframe(df)
