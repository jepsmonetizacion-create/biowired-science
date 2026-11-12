import json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
import cairocffi as cairo

W, H, FPS = 1920, 1080, 30
DUR = 255.556
G, WH, MU, OR, BL, PU, RD = "#3DFFA0", "#FFFFFF", "#B9D4D8", "#FFB454", "#5CC8FF", "#A78BFA", "#FF6B6B"
BG1, BG2 = "#0E3A44", "#061A20"
FONT = "Inter Display"

T = json.load(open(os.path.join(HERE, "timing.json")))
NP = max(o["p"] for o in T) + 1
PST = [min(o["start"] for o in T if o["p"] == i) for i in range(NP)]
SENT = [[o["start"] for o in T if o["p"] == i] for i in range(NP)]


def rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


def col(c, h, a=1.0):
    r, g, b = rgb(h)
    c.set_source_rgba(r, g, b, max(0.0, min(1.0, a)))


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ap(t, t0, d=0.5):
    return ease((t - t0) / d)


def text(c, s, x, y, size, h=WH, a=1.0, bold=False, align="l", sp=0):
    if a <= 0.004:
        return 0
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)
    if sp:
        widths = [c.text_extents(ch)[4] + sp for ch in s]
        tw = sum(widths) - sp
        x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
        col(c, h, a)
        for ch, w in zip(s, widths):
            c.move_to(x0, y); c.show_text(ch); x0 += w
        return tw
    tw = c.text_extents(s)[4]
    x0 = x - tw / 2 if align == "c" else (x - tw if align == "r" else x)
    col(c, h, a); c.move_to(x0, y); c.show_text(s)
    return tw


def rrect(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()


def card(c, x, y, w, h, a=1.0, edge=G, r=26):
    if a <= 0.004:
        return
    rrect(c, x, y, w, h, r); col(c, "#FFFFFF", 0.05 * a); c.fill_preserve()
    col(c, edge, 0.35 * a); c.set_line_width(2.5); c.stroke()


def line(c, pts, h=G, w=6, a=1.0, glow=True):
    if a <= 0.004 or len(pts) < 2:
        return
    c.new_path()
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    passes = [(w * 3.2, 0.10), (w * 1.9, 0.22), (w, 1.0)] if glow else [(w, 1.0)]
    for lw, al in passes:
        c.move_to(*pts[0])
        for p in pts[1:]:
            c.line_to(*p)
        col(c, h, a * al); c.set_line_width(lw); c.stroke()


def dot(c, x, y, r, h=G, a=1.0, fill=True, lw=4):
    if a <= 0.004:
        return
    c.new_path()
    c.arc(x, y, r, 0, 2 * math.pi); col(c, h, a)
    if fill:
        c.fill()
    else:
        c.set_line_width(lw); c.stroke()


def arrow(c, x1, y1, x2, y2, h=MU, a=1.0, w=4):
    if a <= 0.004:
        return
    line(c, [(x1, y1), (x2, y2)], h, w, a, glow=False)
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (-1, 1):
        line(c, [(x2, y2), (x2 - 20 * math.cos(ang + s * 0.5), y2 - 20 * math.sin(ang + s * 0.5))], h, w, a, glow=False)


def ecg(ph):
    ph %= 1.0
    g = lambda m, s: math.exp(-((ph - m) / s) ** 2)
    return g(0.30, 0.018) - 0.22 * g(0.26, 0.02) - 0.30 * g(0.34, 0.02) + 0.22 * g(0.56, 0.06) + 0.10 * g(0.14, 0.04)


def ppg(ph):
    ph %= 1.0
    g = lambda m, s: math.exp(-((ph - m) / s) ** 2)
    return g(0.25, 0.11) + 0.42 * g(0.52, 0.13)


def noise(x):
    return (math.sin(x * 12.9898) * 43758.5453) % 1.0 * 2 - 1


def title(c, s, t, sub=None):
    a = ap(t, 0.1, 0.5)
    text(c, s, 120, 215, 50, WH, a, bold=True)
    line(c, [(120, 245), (120 + 150 * a, 245)], G, 5, a, glow=False)
    if sub:
        text(c, sub, 120, 300, 32, MU, a)


def watch(c, cx, cy, s=1.0, a=1.0, big="1h 12m", small="DEEP SLEEP", ring=0.7, tag=None):
    if a <= 0.004:
        return
    w, h = 300 * s, 360 * s
    for yy, hh in ((cy - h / 2 - 150 * s, 170 * s), (cy + h / 2 - 20 * s, 170 * s)):
        rrect(c, cx - 105 * s, yy, 210 * s, hh, 30 * s); col(c, "#13262C", a); c.fill()
    rrect(c, cx - w / 2, cy - h / 2, w, h, 70 * s); col(c, "#1B3138", a); c.fill_preserve()
    col(c, MU, 0.35 * a); c.set_line_width(3); c.stroke()
    rrect(c, cx - w / 2 + 18 * s, cy - h / 2 + 18 * s, w - 36 * s, h - 36 * s, 54 * s); col(c, "#030B0E", a); c.fill()
    c.set_line_cap(cairo.LINE_CAP_ROUND); c.new_path()
    c.arc(cx, cy - 20 * s, 92 * s, 0, 2 * math.pi); col(c, G, 0.15 * a); c.set_line_width(14 * s); c.stroke()
    c.new_path(); c.arc(cx, cy - 20 * s, 92 * s, -math.pi / 2, -math.pi / 2 + 2 * math.pi * ring); col(c, G, a); c.set_line_width(14 * s); c.stroke()
    text(c, small, cx, cy - 42 * s, 17 * s, MU, a, align="c", sp=2 * s)
    text(c, big, cx, cy + 6 * s, 44 * s, WH, a, bold=True, align="c")
    if tag:
        rrect(c, cx - 78 * s, cy + 96 * s, 156 * s, 40 * s, 20 * s); col(c, OR, 0.95 * a); c.fill()
        text(c, tag, cx, cy + 124 * s, 21 * s, "#1A1200", a, bold=True, align="c", sp=1.5 * s)


def tiles(c, x, y, seq, n_show, tw=38, th=70, gap=4, a=1.0, mark=None):
    cm = {"L": BL, "D": G, "R": PU, "W": MU}
    for i, s in enumerate(seq):
        k = max(0.0, min(1.0, n_show - i))
        if k <= 0:
            break
        hh = th * {"W": 0.35, "R": 0.6, "L": 0.8, "D": 1.0}[s]
        rrect(c, x + i * (tw + gap), y + th - hh, tw, hh, 7); col(c, cm[s], 0.85 * a * k); c.fill()
        if mark and mark[i]:
            rrect(c, x + i * (tw + gap) - 3, y - 6, tw + 6, th + 12, 9); col(c, OR, a * k); c.set_line_width(3); c.stroke()


def legend(c, x, y, a):
    for i, (n, h) in enumerate((("Light", BL), ("Deep", G), ("REM", PU))):
        dot(c, x + i * 190, y - 10, 11, h, a)
        text(c, n, x + i * 190 + 24, y, 30, MU, a)


def bar(c, x, y, w, h, f0, f1, hcol, a=1.0):
    rrect(c, x, y, w, h, h / 2); col(c, "#FFFFFF", 0.08 * a); c.fill()
    if f1 - f0 > 0.003:
        rrect(c, x + w * f0, y, max(h, w * (f1 - f0)), h, h / 2); col(c, hcol, a); c.fill()


# ---------------- scenes ----------------
def s_hook(c, t, d, S):
    watch(c, 520, 560, 1.15, ap(t, 0.2, 0.6), ring=0.7 * ap(t, 0.5, 2.0))
    a1 = ap(t, S[1], 0.5)
    text(c, "Your watch has never", 880, 420, 76, WH, a1, bold=True)
    text(c, "seen your brain.", 880, 510, 76, G, a1, bold=True)
    text(c, "Deep sleep is defined by what your brain is doing.", 880, 610, 38, MU, ap(t, S[2], 0.5))
    text(c, "So where did that number come from?", 880, 720, 46, WH, ap(t, S[3], 0.5), bold=True)


def s_lab(c, t, d, S):
    title(c, "IN A SLEEP LAB: POLYSOMNOGRAPHY", t)
    a = ap(t, 0.4, 0.6)
    dot(c, 340, 560, 150, MU, 0.7 * a, fill=False, lw=5)
    line(c, [(300, 705), (290, 790)], MU, 5, 0.7 * a, glow=False); line(c, [(380, 705), (390, 790)], MU, 5, 0.7 * a, glow=False)
    for i in range(5):
        ang = math.pi * (1.15 + i * 0.175)
        ex, ey = 340 + 150 * math.cos(ang), 560 + 150 * math.sin(ang)
        k = ap(t, S[1] + i * 0.15, 0.3)
        line(c, [(ex, ey), (ex + (i - 2) * 30, ey - 80)], G, 3, 0.6 * k, glow=False)
        dot(c, ex, ey, 13, G, k)
    rows = [("Brain waves", S[1], 370), ("Eye movements", S[2], 520), ("Muscle tone", S[2] + 1.3, 670)]
    for idx, (lab, t0, y) in enumerate(rows):
        k = ap(t, t0, 0.5)
        text(c, lab, 640, y - 62, 30, MU, k)
        pts = []
        for i in range(0, 286):
            x = 640 + i * 4; u = i * 0.05 + t * 1.6
            if idx == 0:
                v = 26 * math.sin(u * 2.1) + 14 * math.sin(u * 5.3 + 1) + 8 * math.sin(u * 9.7)
            elif idx == 1:
                v = 38 * math.tanh(4 * math.sin(u * 0.55)) * (0.5 + 0.5 * math.sin(u * 0.13))
            else:
                v = 16 * noise(int(u * 14)) * (0.6 + 0.4 * math.sin(u * 0.4))
            pts.append((x, y + v))
        n = int(len(pts) * k)
        line(c, pts[:n], [G, BL, PU][idx], 4, k)
    seq = "WLLLDDDDLLRRLLDDDLLRRRLLLRRW"
    n = (t - S[3]) * 9
    if n > 0:
        text(c, "30-second blocks", 640, 780, 28, MU, ap(t, S[3], 0.4))
        tiles(c, 640, 800, seq, n, tw=34, th=62)
        legend(c, 1240, 780, ap(t, S[3] + 1.0, 0.5))


def s_brain(c, t, d, S):
    title(c, "SLEEP STAGES ARE DEFINED BY THE BRAIN", t)
    k = ap(t, S[1] - 0.2, 0.5)
    card(c, 120, 300, 810, 560, k)
    text(c, "DEEP SLEEP", 170, 380, 44, G, k, bold=True)
    pts = [(170 + i * 4, 590 + 95 * math.sin(i * 0.045 + t * 1.2) + 14 * math.sin(i * 0.16 + t)) for i in range(178)]
    line(c, pts, G, 5, k)
    text(c, "Slow, large brain waves", 170, 800, 34, MU, k)
    k2 = ap(t, S[2], 0.5)
    card(c, 990, 300, 810, 560, k2, edge=PU)
    text(c, "REM", 1040, 380, 44, PU, k2, bold=True)
    pts = [(1040 + i * 4, 560 + 22 * math.sin(i * 0.33 + t * 6) + 12 * math.sin(i * 0.71 + t * 9)) for i in range(178)]
    line(c, pts, PU, 4, k2)
    ex = 26 * math.tanh(3 * math.sin(t * 5.0))
    for cx in (1330, 1460):
        dot(c, cx, 690, 40, WH, 0.9 * k2, fill=False, lw=4); dot(c, cx + ex, 690, 15, WH, k2)
    text(c, "Active brain · darting eyes · relaxed muscles", 1040, 800, 31, MU, k2)


def s_noaccess(c, t, d, S):
    watch(c, 480, 560, 0.95, ap(t, 0.1, 0.5), ring=0.7)
    text(c, "WRIST", 480, 920 - 60, 30, MU, ap(t, 0.3, 0.5), align="c", sp=6)
    a = ap(t, 0.3, 0.5)
    dot(c, 1420, 500, 170, PU, 0.8 * a, fill=False, lw=5)
    pts = [(1300 + i * 4, 500 + 26 * math.sin(i * 0.2 + t * 4) + 12 * math.sin(i * 0.5 + t * 7)) for i in range(60)]
    line(c, pts, PU, 4, a)
    text(c, "BRAIN", 1420, 740, 30, MU, a, align="c", sp=6)
    c.set_dash([18, 16]); line(c, [(690, 520), (1230, 500)], MU, 4, 0.7 * a, glow=False); c.set_dash([])
    k = ap(t, S[1], 0.35)
    line(c, [(920, 470), (1000, 550)], RD, 12, k); line(c, [(1000, 470), (920, 550)], RD, 12, k)
    text(c, "No access to any of that.", 960, 850, 50, WH, k, bold=True, align="c")


def s_two(c, t, d, S):
    text(c, "TWO SENSORS DO THE WORK", 960, 330, 68, WH, ap(t, 0.1, 0.5), bold=True, align="c")
    for i, (n, a1, a2, hh) in enumerate((("1", "ACCELEROMETER", "detects motion", BL), ("2", "GREEN LIGHT", "reads your pulse", G))):
        k = ap(t, 0.9 + i * 0.8, 0.5); x = 240 + i * 760
        card(c, x, 440, 680, 340, k, edge=hh)
        text(c, n, x + 60, 660, 150, hh, k, bold=True)
        text(c, a1, x + 190, 590, 46, WH, k, bold=True)
        text(c, a2, x + 190, 650, 36, MU, k)


def s_accel(c, t, d, S):
    title(c, "SENSOR 1: ACCELEROMETER", t, "It detects motion")
    x0, x1, y = 160, 1760, 560
    line(c, [(x0, y + 170), (x1, y + 170)], MU, 2, 0.3, glow=False)
    prog = ease(t / min(d, 7.0))
    pts = []
    for i in range(0, 401):
        f = i / 400; x = x0 + (x1 - x0) * f
        amp = 150 if f < 0.3 else (150 * math.exp(-(f - 0.3) * 30) + 6)
        if 0.62 < f < 0.65:
            amp = 60
        pts.append((x, y - abs(amp * noise(i * 1.7)) * 0.9 + 150))
    n = max(2, int(len(pts) * prog))
    line(c, pts[:n], BL, 4, 1.0)
    text(c, "Moving", x0 + 150, 370, 32, MU, ap(t, 1.0, 0.5))
    k = ap(t, S[2], 0.6)
    rrect(c, x0 + (x1 - x0) * 0.36, 400, (x1 - x0) * 0.62, 340, 20); col(c, G, 0.08 * k); c.fill_preserve(); col(c, G, 0.5 * k); c.set_line_width(2.5); c.stroke()
    text(c, "No movement  →  probably asleep", x0 + (x1 - x0) * 0.67, 470, 38, G, k, bold=True, align="c")
    text(c, "Used by sleep researchers for decades", 960, 830, 34, MU, ap(t, S[3], 0.5), align="c")
    k4 = ap(t, S[4], 0.4)
    if k4 > 0:
        text(c, "ACTIGRAPHY", 1760, 215, 54, G, k4, bold=True, align="r", sp=6)


def s_ppg(c, t, d, S):
    title(c, "SENSOR 2: THE GREEN LIGHT", t)
    bpm = 1.05; ph = t * bpm; pulse = ppg(ph)
    a = ap(t, 0.3, 0.5)
    rrect(c, 200, 300, 720, 80, 20); col(c, "#1B3138", a); c.fill()
    text(c, "BACK OF THE WATCH", 560, 350, 26, MU, a, align="c", sp=3)
    rrect(c, 200, 400, 720, 420, 12); col(c, "#E8B79A", 0.10 * a); c.fill()
    text(c, "SKIN", 230, 450, 24, MU, 0.8 * a, sp=3)
    th = 34 + 16 * pulse
    rrect(c, 200, 660 - th / 2, 720, th, th / 2); col(c, "#FF5C6C", 0.85 * a); c.fill()
    text(c, "BLOOD VESSEL", 230, 750, 24, "#FF9AA5", a, sp=3)
    for lx in (380, 740):
        dot(c, lx, 392, 16, G, a)
        line(c, [(lx, 400), (lx + (560 - lx) * 0.75, 650)], G, 7, 0.9 * a)
        line(c, [(lx + (560 - lx) * 0.75, 650), (560, 404)], G, 5, a * (0.85 - 0.6 * pulse))
    rrect(c, 530, 380, 60, 22, 6); col(c, WH, a); c.fill()
    text(c, "light sensor", 560, 285, 24, MU, ap(t, S[3], 0.4), align="c")
    card(c, 1020, 300, 760, 380, a)
    text(c, "LIGHT BOUNCING BACK", 1060, 360, 26, MU, a, sp=3)
    pts = [(1060 + i * 4, 610 - 170 * (1 - 0.75 * ppg((i * 4 / 260.0) + ph - 2.6))) for i in range(171)]
    line(c, pts, G, 5, a)
    text(c, "Blood absorbs green light", 1020, 750, 36, WH, ap(t, S[1], 0.5), bold=True)
    text(c, "Each heartbeat = a small wave of blood", 1020, 805, 34, MU, ap(t, S[2], 0.5))
    k = ap(t, S[4], 0.4)
    text(c, "PHOTOPLETHYSMOGRAPHY  ·  PPG", 1780, 215, 40, G, k, bold=True, align="r", sp=3)


def s_metrics(c, t, d, S):
    title(c, "FROM ONE PULSE SIGNAL", t)
    pts = [(160 + i * 4, 400 - 90 * ppg(i * 4 / 230.0 - t * 1.05)) for i in range(401)]
    line(c, pts, G, 5, ap(t, 0.2, 0.6))
    items = (("HEART RATE", "58", "beats / min", 1.6), ("TIME BETWEEN BEATS", "±", "it varies beat to beat", d * 0.42), ("BREATHING RATE", "14", "breaths / min", d * 0.72))
    for i, (h1, big, sub, t0) in enumerate(items):
        k = ap(t, t0, 0.5); x = 130 + i * 565
        card(c, x, 500, 530, 330, k)
        text(c, h1, x + 40, 565, 28, MU, k, sp=3)
        text(c, big, x + 40, 720, 130, WH, k, bold=True)
        text(c, sub, x + 40, 790, 30, MU, k)
    text(c, "Example values", 1790, 880, 22, MU, 0.6 * ap(t, 2.0, 0.5), align="r")


def s_plus(c, t, d, S):
    k = ap(t, 0.2, 0.5)
    card(c, 250, 380, 580, 260, k, edge=BL); text(c, "MOVEMENT", 540, 535, 72, WH, k, bold=True, align="c")
    text(c, "+", 960, 545, 120, G, ap(t, 0.8, 0.4), bold=True, align="c")
    k2 = ap(t, 1.2, 0.5)
    card(c, 1090, 380, 580, 260, k2); text(c, "PULSE", 1380, 535, 72, WH, k2, bold=True, align="c")
    text(c, "Nothing else.", 960, 790, 60, G, ap(t, S[1], 0.4), bold=True, align="c")


def s_body(c, t, d, S):
    title(c, "YOUR BODY CHANGES WITH EACH STAGE", t)
    k = ap(t, S[1] - 0.2, 0.5)
    card(c, 120, 300, 1680, 260, k)
    text(c, "DEEP SLEEP", 170, 370, 38, G, k, bold=True)
    text(c, "heart slow and steady  ·  barely moving", 170, 530, 30, MU, k)
    pts = [(520 + i * 4, 470 - 110 * ecg(i * 4 / 300.0 - t * 0.9)) for i in range(310)]
    line(c, pts, G, 4, k)
    k2 = ap(t, S[2], 0.5)
    card(c, 120, 600, 1680, 260, k2, edge=PU)
    text(c, "REM", 170, 670, 38, PU, k2, bold=True)
    text(c, "body still  ·  heart and breathing irregular", 170, 830, 30, MU, k2)
    pts = []
    for i in range(310):
        u = i * 4 / 230.0 - t * 1.25
        u2 = u + 0.22 * math.sin(u * 1.7) + 0.15 * math.sin(u * 0.63 + 2)
        pts.append((520 + i * 4, 770 - 105 * ecg(u2)))
    line(c, pts, PU, 4, k2)


def s_train(c, t, d, S):
    title(c, "HOW THE ALGORITHM LEARNS", t, "Nights recorded in a sleep lab")
    k = ap(t, 0.5, 0.5)
    card(c, 120, 380, 560, 180, k, edge=BL); text(c, "WATCH", 160, 445, 34, BL, k, bold=True); text(c, "movement + pulse", 160, 500, 32, WH, k)
    card(c, 120, 620, 560, 180, k, edge=PU); text(c, "BRAIN SENSORS", 160, 685, 34, PU, k, bold=True); text(c, "the true sleep stage", 160, 740, 32, WH, k)
    k2 = ap(t, 2.2, 0.5)
    arrow(c, 700, 470, 860, 560, MU, k2); arrow(c, 700, 710, 860, 620, MU, k2)
    pul = 1 + 0.03 * math.sin(t * 4)
    card(c, 880 - 5 * pul, 480, 420, 220, k2)
    text(c, "ALGORITHM", 1090, 580, 46, G, k2, bold=True, align="c"); text(c, "learns the patterns", 1090, 640, 30, MU, k2, align="c")
    k3 = ap(t, S[1], 0.5)
    arrow(c, 1320, 590, 1440, 590, MU, k3)
    for i, (n, h) in enumerate((("Light", BL), ("Deep", G), ("REM", PU))):
        kk = ap(t, S[1] + 0.5 + i * 0.5, 0.4)
        rrect(c, 1470, 440 + i * 105, 300, 80, 40); col(c, h, 0.18 * kk); c.fill_preserve(); col(c, h, kk); c.set_line_width(3); c.stroke()
        text(c, n, 1620, 493 + i * 105, 36, WH, kk, bold=True, align="c")


def s_guess(c, t, d, S):
    title(c, "AN EDUCATED GUESS", t)
    k = ap(t, 0.3, 0.5)
    pts = [(140 + i * 4, 600 - 110 * ppg(i * 4 / 200.0 - t * 1.05)) for i in range(120)]
    line(c, pts, G, 5, k)
    text(c, "your pulse", 380, 760, 30, MU, k, align="c")
    arrow(c, 650, 560, 760, 560, MU, k)
    card(c, 790, 450, 380, 220, k); text(c, "ALGORITHM", 980, 575, 42, G, k, bold=True, align="c")
    arrow(c, 1200, 560, 1310, 560, MU, k)
    watch(c, 1540, 560, 0.85, k, ring=0.7, tag="ESTIMATE" if t > S[1] else None)
    text(c, "Built from your heartbeat, not measured from your brain.", 960, 835, 38, WH, ap(t, S[1] + 0.3, 0.5), bold=True, align="c")


def s_good(c, t, d, S):
    q = 1 - ap(t, S[0] + 1.1, 0.4) if False else 1.0
    t13 = PST[13] - PST[12]
    aq = ap(t, 0.05, 0.3) * (1 - ap(t, t13 - 0.1, 0.4))
    text(c, "HOW GOOD IS THE GUESS?", 960, 560, 84, WH, aq, bold=True, align="c")
    u = t - t13
    if u < 0:
        return
    S13 = [x - PST[13] for x in SENT[13]]
    title(c, "TESTED AGAINST THE SLEEP LAB", u)
    k = ap(u, 0.4, 0.5)
    card(c, 120, 300, 1680, 170, k)
    text(c, "2021", 170, 410, 84, G, k, bold=True)
    text(c, "7 consumer sleep trackers  vs.  polysomnography", 440, 375, 40, WH, k, bold=True)
    text(c, "US Navy sleep lab  ·  published in the journal Sleep", 440, 430, 30, MU, k)
    k2 = ap(u, S13[1], 0.5)
    text(c, "Time truly ASLEEP, correctly detected", 120, 580, 36, MU, k2)
    f = 0.93 * ease((u - S13[1] - 0.3) / 1.6)
    bar(c, 120, 610, 1300, 70, 0, f, G, k2)
    text(c, "≥ 93%", 1470, 672, 96, G, k2, bold=True)
    text(c, "Fairly good at the big picture", 120, 790, 44, WH, ap(u, S13[2], 0.5), bold=True)
    text(c, "Source: Chinoy et al., 2021, Sleep", 1800, 880, 22, MU, 0.7 * k, align="r")


def s_wake(c, t, d, S):
    title(c, "BUT SPOTTING WAKEFULNESS…", t)
    k0 = ap(t, 0.3, 0.5)
    text(c, "Time truly ASLEEP, correctly detected", 120, 350, 30, MU, 0.6 * k0)
    bar(c, 120, 370, 1300, 44, 0, 0.93, G, 0.45 * k0); text(c, "≥ 93%", 1470, 408, 50, G, 0.6 * k0, bold=True)
    k = ap(t, S[1] - 0.3, 0.5)
    text(c, "Time truly AWAKE, correctly detected", 120, 540, 36, MU, k)
    f = ease((t - S[1]) / 1.6)
    bar(c, 120, 570, 1300, 70, 0.18 * f, 0.18 * f + 0.36 * f, OR, k)
    text(c, "18–54%", 1470, 632, 90, OR, k, bold=True)
    k2 = ap(t, S[2], 0.5)
    text(c, "Lying still looks a lot like sleep,", 120, 770, 44, WH, k2, bold=True)
    text(c, "so awake time gets counted as sleep.", 120, 830, 44, WH, k2, bold=True)
    text(c, "Source: Chinoy et al., 2021, Sleep", 1800, 880, 22, MU, 0.7 * k0, align="r")


def s_stages(c, t, d, S):
    title(c, "SLEEP STAGES: THE WEAKEST PART", t)
    lab = "WLLLDDDDLLRRLLDDDLLRRRLLLRRWLLDDLLRR"
    wat = "WLLLLLDDLLLRLLLLDDLRRLLLLLRRLLLLLLRL"
    mk = [a != b for a, b in zip(lab, wat)]
    k = ap(t, 0.4, 0.5)
    text(c, "Sleep lab", 120, 365, 32, MU, k); tiles(c, 330, 310, lab, (t - 0.5) * 14, a=k)
    text(c, "Watch", 120, 495, 32, MU, k); tiles(c, 330, 440, wat, (t - 1.6) * 14, a=k, mark=mk if t > 4.0 else None)
    legend(c, 330, 580, k); text(c, "Illustration, not real data", 1800, 580, 22, MU, 0.7 * k, align="r")
    k2 = ap(t, S[1], 0.5)
    card(c, 120, 630, 1680, 110, k2, edge=MU)
    text(c, "Study limits: healthy young adults, older devices. Newer watches may do better.", 160, 698, 34, MU, k2)
    k3 = ap(t, S[2], 0.5)
    text(c, "Light / deep / REM is still the least reliable part of your report.", 120, 830, 42, G, k3, bold=True)


def s_ortho(c, t, d, S):
    t17 = PST[17] - PST[16]
    if t < t17 + 0.4:
        a = ap(t, 0.05, 0.3) * (1 - ap(t, t17 - 0.1, 0.4))
        r = 150 * (1 + 0.04 * math.sin(t * 6))
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.new_path()
        c.arc(960, 480, r, 0.75 * math.pi, 2.25 * math.pi); col(c, WH, 0.12 * a); c.set_line_width(26); c.stroke()
        c.new_path(); c.arc(960, 480, r, 0.75 * math.pi, 0.75 * math.pi + 1.5 * math.pi * 0.62); col(c, OR, a); c.set_line_width(26); c.stroke()
        text(c, "62", 960, 515, 110, WH, a, bold=True, align="c"); text(c, "SLEEP SCORE", 960, 575, 24, MU, a, align="c", sp=4)
        text(c, "When the score becomes the problem", 960, 790, 54, WH, a, bold=True, align="c")
    u = t - t17
    if u < 0:
        return
    S17 = [x - PST[17] for x in SENT[17]]
    title(c, "CHASING THE PERFECT SCORE", u)
    k = ap(u, 0.4, 0.5)
    card(c, 120, 300, 1680, 170, k)
    text(c, "2017", 170, 410, 84, G, k, bold=True)
    text(c, "3 case reports of patients fixated on tracker data", 440, 375, 40, WH, k, bold=True)
    text(c, "Journal of Clinical Sleep Medicine", 440, 430, 30, MU, k)
    k2 = ap(u, S17[1], 0.5)
    text(c, "Time in bed", 120, 560, 32, MU, k2)
    for i in range(6):
        hh = (70 + i * 26) * ease((u - S17[1] - i * 0.35) / 0.6)
        rrect(c, 130 + i * 90, 800 - hh, 60, max(hh, 1), 10); col(c, OR, k2 * (0.5 + 0.1 * i)); c.fill()
    text(c, "More and more time in bed, chasing a better score:", 760, 650, 34, WH, k2)
    text(c, "the opposite of what sleep therapists recommend.", 760, 700, 34, MU, k2)
    k3 = ap(u, S17[2], 0.5)
    text(c, "ORTHOSOMNIA", 1790, 830, 76, G, k3, bold=True, align="r", sp=8)
    text(c, "Source: Baron et al., 2017", 1800, 880, 22, MU, 0.7 * k, align="r")


def s_quote(c, t, d, S):
    a = ap(t, 0.1, 0.5)
    text(c, "A number meant to help you rest", 960, 490, 68, WH, a, bold=True, align="c")
    text(c, "can become one more thing keeping you up.", 960, 590, 68, G, ap(t, 1.3, 0.5), bold=True, align="c")


def s_tips(c, t, d, S):
    title(c, "HOW TO USE YOUR SLEEP DATA", t)
    items = (("1", "Look at trends", "over weeks, not one night", S[2]), ("2", "Trust total sleep time", "more than the stage breakdown", S[3]), ("3", "Compare the score", "with how you feel during the day", S[4]))
    for i, (n, a1, a2, t0) in enumerate(items):
        k = ap(t, t0, 0.5); y = 310 + i * 190
        card(c, 120, y, 1680, 160, k)
        text(c, n, 175, y + 115, 100, G, k, bold=True)
        text(c, a1, 300, y + 75, 46, WH, k, bold=True); text(c, a2, 300, y + 125, 34, MU, k)
        if i == 0:
            pts = [(1300 + j * 34, y + 100 - 22 * math.sin(j * 0.9) - j * 3.5) for j in range(13)]
            line(c, pts, G, 4, k)
            for p in pts:
                dot(c, p[0], p[1], 6, G, k)


def s_doctor(c, t, d, S):
    a = ap(t, 0.1, 0.5)
    text(c, "A useful estimate,", 960, 420, 84, WH, a, bold=True, align="c")
    text(c, "not a diagnosis.", 960, 525, 84, G, ap(t, 1.4, 0.5), bold=True, align="c")
    k = ap(t, S[1], 0.5)
    card(c, 330, 640, 1260, 170, k, edge=OR)
    text(c, "Sleeping badly for weeks?", 960, 715, 44, WH, k, bold=True, align="c")
    text(c, "That is a conversation for a doctor, not an app.", 960, 772, 36, MU, k, align="c")


def mark(c, cx, cy, s, a):
    c.save(); c.translate(cx - 400 * s, cy - 400 * s); c.scale(s, s)
    line(c, [(170, 400), (285, 400), (322, 325), (362, 505), (402, 245), (442, 475), (468, 400), (525, 400)], G, 20, a)
    for pts in ([(525, 400), (575, 345), (628, 345)], [(525, 400), (640, 400)], [(525, 400), (575, 455), (618, 455)]):
        line(c, pts, G, 20, a)
    for x, y in ((152, 400), (646, 345), (658, 400), (636, 455)):
        dot(c, x, y, 18, BG2, 1.0 if a > 0.5 else a); dot(c, x, y, 18, G, a, fill=False, lw=12)
    c.restore()


def s_end(c, t, d, S):
    a = ap(t, 0.1, 0.6)
    mark(c, 960, 330, 0.75, a)
    text(c, "BIOWIRED", 960, 560, 110, WH, a, bold=True, align="c")
    text(c, "SCIENCE", 960, 630, 48, G, a, align="c", sp=22)
    k = ap(t, 1.2, 0.5)
    text(c, "Next: how the green light reads your heart", 960, 760, 44, WH, k, bold=True, align="c")
    text(c, "Sources in the description  ·  Educational content, not medical advice", 960, 830, 28, MU, k, align="c")


SCENES = [  # (first paragraph, function, section label)
    (0, s_hook, ""), (1, s_lab, "THE GOLD STANDARD"), (2, s_brain, "THE GOLD STANDARD"), (3, s_noaccess, "THE GOLD STANDARD"),
    (4, s_two, "WHAT THE WATCH MEASURES"), (5, s_accel, "WHAT THE WATCH MEASURES"), (6, s_ppg, "WHAT THE WATCH MEASURES"),
    (7, s_metrics, "WHAT THE WATCH MEASURES"), (8, s_plus, "WHAT THE WATCH MEASURES"), (9, s_body, "FROM PULSE TO SLEEP STAGE"),
    (10, s_train, "FROM PULSE TO SLEEP STAGE"), (11, s_guess, "FROM PULSE TO SLEEP STAGE"), (12, s_good, "HOW ACCURATE IS IT?"),
    (14, s_wake, "HOW ACCURATE IS IT?"), (15, s_stages, "HOW ACCURATE IS IT?"), (16, s_ortho, "WHEN THE SCORE IS THE PROBLEM"),
    (18, s_quote, "WHEN THE SCORE IS THE PROBLEM"), (19, s_tips, "WHAT TO DO"), (20, s_doctor, "WHAT TO DO"), (21, s_end, ""),
]
BOUNDS = [PST[p] for p, _, _ in SCENES] + [DUR]
BOUNDS[0] = 0.0


def make_bg():
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(s)
    g = cairo.RadialGradient(W / 2, H * 0.45, 50, W / 2, H * 0.45, W * 0.75)
    g.add_color_stop_rgb(0, *rgb(BG1)); g.add_color_stop_rgb(1, *rgb(BG2))
    c.set_source(g); c.paint()
    col(c, G, 0.035); c.set_line_width(1)
    for x in range(0, W, 80):
        c.move_to(x, 0); c.line_to(x, H)
    for y in range(0, H, 80):
        c.move_to(0, y); c.line_to(W, y)
    c.stroke()
    return s


def caption(c, t):
    cur = None
    for o in T:
        if o["start"] - 0.05 <= t:
            cur = o
        else:
            break
    if cur is None or t > cur["end"] + 0.6:
        return
    c.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL); c.set_font_size(38)
    words, lines, ln = cur["text"].split(), [], ""
    for w in words:
        if c.text_extents((ln + " " + w).strip())[4] > 1500:
            lines.append(ln); ln = w
        else:
            ln = (ln + " " + w).strip()
    lines.append(ln)
    # split long sentences into pages of two lines, timed by share
    pages = [lines[i:i + 2] for i in range(0, len(lines), 2)]
    span = max(0.01, cur["end"] - cur["start"])
    tot = sum(len(" ".join(p)) for p in pages); acc = 0; page = pages[-1]
    for p in pages:
        acc += len(" ".join(p))
        if (t - cur["start"]) / span <= acc / tot:
            page = p; break
    y0 = 1010 - (len(page) - 1) * 50
    wmax = max(c.text_extents(l)[4] for l in page)
    rrect(c, 960 - wmax / 2 - 30, y0 - 46, wmax + 60, len(page) * 50 + 18, 16); col(c, "#000000", 0.5); c.fill()
    for i, l in enumerate(page):
        text(c, l, 960, y0 + i * 50, 38, WH, 1.0, align="c")


def frame(c, bg, t):
    c.set_source_surface(bg); c.paint()
    i = 0
    while i + 1 < len(SCENES) and t >= BOUNDS[i + 1]:
        i += 1
    t0, t1 = BOUNDS[i], BOUNDS[i + 1]
    p, fn, lab = SCENES[i]
    S = [x - t0 for x in SENT[p]]
    while len(S) < 6:
        S.append(S[-1] + 2.0)
    a = ap(t - t0, 0, 0.35) * (1 - ap(t - t0, (t1 - t0) - 0.25, 0.25)) if i < len(SCENES) - 1 else ap(t - t0, 0, 0.35)
    c.push_group(); fn(c, t - t0, t1 - t0, S); c.pop_group_to_source(); c.paint_with_alpha(a)
    if fn not in (s_end,):
        mark(c, 150, 92, 0.16, 0.9)
        text(c, "BIOWIRED SCIENCE", 215, 102, 24, WH, 0.85, bold=True, sp=3)
        if lab:
            text(c, lab, 1800, 102, 22, MU, 0.8, align="r", sp=3)
        caption(c, t)
    col(c, "#FFFFFF", 0.08); c.rectangle(0, H - 6, W, 6); c.fill()
    col(c, G, 0.9); c.rectangle(0, H - 6, W * t / DUR, 6); c.fill()


def main():
    bg = make_bg()
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); c = cairo.Context(surf)
    if sys.argv[1] == "preview":
        import os
        os.makedirs(os.path.join(HERE, "prev"), exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]] or [BOUNDS[i] + (BOUNDS[i + 1] - BOUNDS[i]) * f for i in range(len(SCENES)) for f in (0.55, 0.93)]
        for n, t in enumerate(ts):
            frame(c, bg, t); surf.write_to_png(os.path.join(HERE, "prev", f"f{n:02d}.png"))
        return
    out = sys.argv[2]
    n = int(DUR * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", os.path.join(HERE, "narration.mp3"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
    for k in range(n):
        frame(c, bg, k / FPS); surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
        if k % 600 == 0:
            print(k, n, flush=True)
    ff.stdin.close(); ff.wait(); print("done", ff.returncode)


main()
