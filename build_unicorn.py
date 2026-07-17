"""把校徽图变成"点阵独角兽" — 生成 unicorn_dots.html,app.py 直接读取显示。
Turns the emblem into a dot-unicorn — writes unicorn_dots.html for app.py to show.

运行 / run:  ./venv/bin/python build_unicorn.py   (改了参数后重跑一次即可)
"""
import random

import numpy as np
from PIL import Image

STEP = 4        # 每 4px 取一个点 — 越小点越密 / dot grid spacing: smaller = denser
SCALE = 0.5     # 显示大小 = 原图一半 / display size = half the emblem
GOLDS = ["#ffd75e", "#ffe9a8", "#e8c04a", "#d9e3a8"]  # 金色系随机点缀 / gold shades

alpha = np.asarray(Image.open("college_logo.png").convert("RGBA"))[:, :, 3]
h, w = alpha.shape
# 三组点交错闪 — 同一组共用一条 box-shadow,一个元素画几百个点,零 JS 零性能负担
# 3 groups twinkle out of phase; each group is ONE element whose box-shadow paints
# every dot — hundreds of dots, no JS, no per-dot DOM cost
groups = [[], [], []]
for y in range(0, h, int(STEP / SCALE)):
    for x in range(0, w, int(STEP / SCALE)):
        if alpha[y, x] > 100:   # 只在徽章笔画上放点 / dots only on the emblem strokes
            random.choice(groups).append(
                f"{int(x * SCALE)}px {int(y * SCALE)}px 0 {random.choice(GOLDS)}")

# 每组两段动画: ud-in 飞入 + ud-seq 三次闪光; 组间错开一点,像点点流进来
# two animations per group: ud-in (fly in) + ud-seq (3 shines); slight stagger
shadows = "".join(
    f".ud{i}{{box-shadow:{','.join(g)};"
    f"animation:ud-in .9s cubic-bezier(.2,.7,.3,1) {i * .12}s both,"
    f"ud-seq 7.5s ease-in-out {1.1 + i * .3}s 1 forwards}}"
    for i, g in enumerate(groups))
html = f"""<style>
.unicorn-dots{{position:fixed;top:4.2rem;right:1.4rem;width:{int(w*SCALE)}px;
  height:{int(h*SCALE)}px;z-index:999;pointer-events:none}}
.unicorn-dots i{{position:absolute;width:3px;height:3px;border-radius:50%}}
{shadows}
/* 进场: 从屏幕左边快速飞到右上角 / entrance: dots rush in from the left */
@keyframes ud-in{{from{{transform:translateX(-88vw);opacity:0}}
  to{{transform:none;opacity:1}}}}
/* 三次闪光: 金→白→紫, 之后停在紫色 (forwards = 定格在最后一帧,不再动)
   3 shines gold→white→purple, then HOLD purple — forwards freezes the last frame */
@keyframes ud-seq{{
  0%,24%,54%{{opacity:.55;filter:none}}
  12%{{opacity:1;filter:brightness(1.35) drop-shadow(0 0 6px #ffd75e)}}
  40%{{opacity:1;filter:saturate(.15) brightness(1.9) drop-shadow(0 0 6px #ffffff)}}
  74%{{opacity:1;filter:hue-rotate(225deg) saturate(1.35) drop-shadow(0 0 7px #c084fc)}}
  100%{{opacity:.85;filter:hue-rotate(225deg) saturate(1.2)}}}}
@media (max-width:900px){{.unicorn-dots{{display:none}}}}
@media (prefers-reduced-motion:reduce){{.unicorn-dots i{{animation:none!important;
  opacity:.85;filter:hue-rotate(225deg) saturate(1.2)}}}}
</style><div class="unicorn-dots"><i class="ud0"></i><i class="ud1"></i><i class="ud2"></i></div>"""
with open("unicorn_dots.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"dots: {sum(len(g) for g in groups)} → unicorn_dots.html")
