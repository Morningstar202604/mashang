#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成对外展示的品牌资产（banner / 竖版海报 / OG 分享图）。

产物：
  docs/banner.png          2560x800  仓库头图（README 顶部）
  demo/promo-poster.jpg    1080x1920 宣传片封面 / 海报
  docs/assets/og.jpg       1200x630  Open Graph 分享图

所有素材从仓库内的真实截图与数据生成，可重复执行、结果稳定（无随机数）。
用法：python tools/make_brand_assets.py
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DEMO = ROOT / "demo"

CYAN = (0, 229, 255)
GREEN = (0, 255, 156)
MAGENTA = (255, 45, 120)
YELLOW = (247, 255, 0)
BG0 = (7, 9, 15)
BG1 = (11, 18, 32)
TEXT_HI = (230, 241, 255)
TEXT_MID = (143, 163, 191)

FONT_CN = "C:/Windows/Fonts/msyhbd.ttc"
FONT_CN_REG = "C:/Windows/Fonts/msyh.ttc"
FONT_MONO = "C:/Windows/Fonts/consolab.ttf"
FONT_MONO_REG = "C:/Windows/Fonts/consola.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def grid(draw, w, h, step=64, color=(0, 229, 255, 18)):
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=color, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=color, width=1)


def corners(draw, w, h, pad=28, length=72, color=CYAN, width=3):
    for x, y, dx, dy in (
        (pad, pad, 1, 1), (w - pad, pad, -1, 1),
        (pad, h - pad, 1, -1), (w - pad, h - pad, -1, -1),
    ):
        draw.line([(x, y), (x + dx * length, y)], fill=color, width=width)
        draw.line([(x, y), (x, y + dy * length)], fill=color, width=width)


def vertical_gradient(w, h, top=BG1, bottom=BG0):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def spaced(draw, xy, text, fnt, fill, spacing=8):
    """逐字加字距绘制（PIL 没有 letter-spacing）。"""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def banner():
    w, h = 2560, 800
    img = vertical_gradient(w, h)
    d = ImageDraw.Draw(img, "RGBA")
    grid(d, w, h, 64, (0, 229, 255, 20))
    corners(d, w, h, pad=34, length=90)

    d.text((110, 92), "M A S H A N G   ·   O F F L I N E   C O D I N G   T E R M I N A L",
           font=font(FONT_MONO_REG, 30), fill=GREEN)
    d.text((104, 170), "码上", font=font(FONT_CN, 200), fill=CYAN)
    d.text((520, 208), "MASHANG", font=font(FONT_MONO, 120), fill=MAGENTA)
    d.text((112, 420), "码上，就是马上。把真实的编程终端装进口袋",
           font=font(FONT_CN, 62), fill=TEXT_HI)
    d.text((112, 510), "CPython 3.13 + JavaScript runtime  ·  38 lessons  ·  assert-judged  ·  fully offline core",
           font=font(FONT_MONO_REG, 30), fill=TEXT_MID)

    chips = [("离线 CPython 3.13", CYAN), ("38 讲闯关", GREEN), ("assert 自动判题", CYAN), ("MIT 开源", YELLOW)]
    x = 112
    for label, color in chips:
        f = font(FONT_CN_REG, 30)
        tw = d.textlength(label, font=f)
        box = (x, 594, x + tw + 52, 664)
        d.rounded_rectangle(box, radius=35, outline=color, width=2, fill=(color[0], color[1], color[2], 20))
        d.text((x + 26, 610), label, font=f, fill=color)
        x = box[2] + 22

    d.text((2330, 700), "38 LESSONS · 8 CHALLENGES · PYTHON + JAVASCRIPT",
           font=font(FONT_MONO_REG, 24), fill=(90, 105, 130), anchor="ra")
    img.save(DOCS / "banner.png", optimize=True)
    print("docs/banner.png", img.size)


def phone_paste(canvas, shot_path, box):
    shot = Image.open(shot_path).convert("RGB")
    tw, th = box[2] - box[0], box[3] - box[1]
    scale = min(tw / shot.width, th / shot.height)
    resized = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)
    x = box[0] + (tw - resized.width) // 2
    y = box[1] + (th - resized.height) // 2
    canvas.paste(resized, (x, y))


def promo_poster():
    w, h = 1080, 1920
    img = vertical_gradient(w, h)
    d = ImageDraw.Draw(img, "RGBA")
    grid(d, w, h, 72, (0, 229, 255, 16))
    corners(d, w, h, pad=30, length=80)
    d.text((74, 86), "MASHANG · 码上", font=font(FONT_CN, 34), fill=GREEN)
    d.text((72, 150), "码上，", font=font(FONT_CN, 116), fill=TEXT_HI)
    d.text((72, 280), "就是马上。", font=font(FONT_CN, 116), fill=CYAN)
    d.text((76, 434), "装进口袋的赛博朋克编程学习终端",
           font=font(FONT_CN_REG, 42), fill=TEXT_MID)
    d.text((76, 496), "CPython 3.13  ·  38 讲  ·  assert 判题  ·  全离线",
           font=font(FONT_CN_REG, 28), fill=GREEN)

    phone_paste(img, DEMO / "app" / "home.png", (250, 570, 830, 1490))
    d.rounded_rectangle((250, 570, 830, 1490), radius=34, outline=CYAN, width=3)

    d.text((540, 1630), "离线写码 · 变量快照 · 六段位成长", font=font(FONT_CN_REG, 38),
           fill=TEXT_HI, anchor="ma")
    d.text((540, 1700), "github.com/badhope/mashang", font=font(FONT_MONO_REG, 30),
           fill=MAGENTA, anchor="ma")
    d.text((540, 1800), "MIT LICENSE · ANDROID 7.0+ · FREE", font=font(FONT_CN_REG, 22),
           fill=(90, 105, 130), anchor="ma")
    img.convert("RGB").save(DEMO / "promo-poster.jpg", quality=88, optimize=True, progressive=True)
    print("demo/promo-poster.jpg", img.size)


def og_image():
    w, h = 1200, 630
    img = vertical_gradient(w, h)
    d = ImageDraw.Draw(img, "RGBA")
    grid(d, w, h, 56, (0, 229, 255, 18))
    d.text((60, 54), "MASHANG · 码上", font=font(FONT_MONO, 26), fill=GREEN)
    d.text((56, 104), "码上，就是马上。", font=font(FONT_CN, 74), fill=TEXT_HI)
    d.text((58, 208), "CPython 3.13 装进口袋 · 38 讲 · assert 判题 · 全离线",
           font=font(FONT_CN_REG, 30), fill=TEXT_MID)
    phone_paste(img, DEMO / "app" / "lesson_exercise.png", (790, 60, 1160, 600))
    d.rounded_rectangle((790, 60, 1160, 600), radius=26, outline=CYAN, width=2)
    d.text((60, 500), "ANDROID 7.0+  ·  MIT  ·  GITHUB.COM/BADHOPE/MASHANG",
           font=font(FONT_MONO_REG, 22), fill=MAGENTA)
    img.save(DOCS / "assets" / "og.jpg", quality=88, optimize=True, progressive=True)
    print("docs/assets/og.jpg", img.size)


def main():
    (DOCS / "assets").mkdir(parents=True, exist_ok=True)
    banner()
    promo_poster()
    og_image()


if __name__ == "__main__":
    main()
