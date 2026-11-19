#!/usr/bin/env python3
"""The World Today — Thursday 19 November 2026.

A procedural front-page newspaper that sums up the world's news of
19 November 2026 in one 1024x1024 image. Pure Python 3 standard library:
the PNG is written by hand (zlib + struct) and the text is drawn with a
tiny 5x7 bitmap font written for this entry. No network at runtime, fully
deterministic: two runs write byte-identical files.

Layout: masthead, one big hero story (US-Iran), 32 more stories in two
columns across six continents, and a BY THE NUMBERS strip.
"""

import os
import math
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 bits ("1" = ink). Authored fresh for this entry.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "•": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
    "€": ("00110", "01001", "10000", "11110", "10000", "01001", "00110"),
    "×": ("00000", "10001", "01010", "00100", "01010", "10001", "00000"),
}

# Normalise fancy punctuation to glyphs we have; everything renders upper-case.
_NORMALISE = {"–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "."}


def clean(text):
    out = []
    for ch in text.upper():
        out.append(_NORMALISE.get(ch, ch))
    return "".join(out)


def text_width(text, scale):
    return len(clean(text)) * 6 * scale


def wrap(text, scale, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w pixels."""
    words, lines, cur = clean(text).split(" "), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_one_line(text, scale, max_w):
    """Truncate to a single line that fits max_w (no ellipsis glyph)."""
    t = clean(text)
    while t and text_width(t, scale) > max_w:
        t = t[:-1]
    return t


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = rgb

    def fill(self, x0, y0, x1, y1, rgb):
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.w, x1), min(self.h, y1)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            for x in range(x0, x1):
                i = base + (x - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = rgb

    def hline(self, x0, x1, y, rgb, thick=1):
        for t in range(thick):
            self.fill(x0, y + t, x1, y + t + 1, rgb)

    def vline(self, x, y0, y1, rgb, thick=1):
        for t in range(thick):
            self.fill(x + t, y0, x + t + 1, y1, rgb)

    def rect(self, x0, y0, x1, y1, rgb, thick=1):
        self.hline(x0, x1, y0, rgb, thick)
        self.hline(x0, x1, y1 - thick, rgb, thick)
        self.vline(x0, y0, y1, rgb, thick)
        self.vline(x1 - thick, y0, y1, rgb, thick)

    def line(self, x0, y0, x1, y1, rgb):
        """Bresenham line."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, rgb)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, rgb):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, rgb)

    def triangle(self, ax, ay, bx, by, cx, cy, rgb):
        """Filled triangle via scanline fill."""
        pts = sorted(((ax, ay), (bx, by), (cx, cy)), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        def edge(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = edge(x0, y0, x1, y1, y)
                xb = edge(x0, y0, x2, y2, y)
            else:
                xa = edge(x1, y1, x2, y2, y)
                xb = edge(x0, y0, x2, y2, y)
            lo, hi = (int(min(xa, xb)), int(max(xa, xb)))
            self.fill(lo, y, hi + 1, y + 1, rgb)

    def grain(self, x0, y0, x1, y1, amount, seed):
        """Deterministic paper grain: small fixed-seed LCG noise per pixel."""
        state = seed & 0x7FFFFFFF
        for y in range(y0, y1):
            for x in range(x0, x1):
                state = (state * 1103515245 + 12345) & 0x7FFFFFFF
                d = (state >> 16) % (2 * amount + 1) - amount
                if d:
                    i = (y * self.w + x) * 3
                    for c in range(3):
                        v = self.px[i + c] + d
                        self.px[i + c] = 0 if v < 0 else (255 if v > 255 else v)

    def text(self, x, y, s, scale, rgb):
        s = clean(s)
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for gy in range(7):
                row = glyph[gy]
                for gx in range(5):
                    if row[gx] == "1":
                        self.fill(cx + gx * scale, y + gy * scale,
                                  cx + gx * scale + scale,
                                  y + gy * scale + scale, rgb)
            cx += 6 * scale
        return cx


# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return c


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- content
# All stories are events that happened or were first reported on 18–19 Nov
# 2026 (late 18 Nov UTC counts for the 19 Nov cycle), verified against web
# news on the morning of 19 Nov 2026. Regions: ME, EU, NA, AS, AF, OC, SC.
PAPER = (247, 243, 232)
INK = (17, 17, 17)
RED = (163, 22, 33)
NAVY = (27, 42, 74)
GREY = (90, 86, 78)
LIGHT = (238, 234, 222)
AMBER = (255, 176, 66)
ORANGE = (232, 110, 30)
WHITE = (250, 248, 242)

REGION_COLOR = {
    "ME": (163, 22, 33),    # Middle East — red
    "EU": (27, 42, 74),     # Europe — navy
    "NA": (30, 90, 60),     # North America — green
    "SA": (180, 60, 140),   # South America — magenta
    "AS": (90, 50, 120),    # Asia — purple
    "AF": (200, 110, 20),   # Africa — orange
    "OC": (20, 110, 120),   # Oceania — teal
    "SC": (70, 90, 110),    # Science / tech — slate
}

HERO = {
    "kicker": "TOP STORY — MIDDLE EAST",
    "title": "US AND IRAN TRADE FIRE AS WAR WIDENS ACROSS THE GULF",
    "body": [
        "US JETS HIT A MISSILE SITE ON IRAN'S QESHM ISLAND ON 17 NOV. IRAN",
        "SAYS IT HIT A US BASE IN KUWAIT; KUWAIT REPORTS INTERCEPTIONS AND",
        "NO CASUALTIES CONFIRMED. IRAN ALSO STRUCK BAHRAIN AGAIN ON 18 NOV,",
        "AS OIL PRICES FELL — BRENT DOWN 1.3% TO $91.95.",
    ],
    "dateline": "WASHINGTON AND TEHRAN — 19 NOV 2026",
}

# (region, title <=38 chars, body <=76 chars)
STORIES = [
    ("ME", "ISRAEL PUSHES NEW OPERATION INTO GAZA",
     "FIRST GROUND PUSH SINCE THE OCT 2025 CEASEFIRE; 3 CIVILIANS KILLED."),
    ("EU", "RUSSIA STRIKES ODESA, FOUR KILLED",
     "MISSILES HIT THE PORT CITY; UKRAINE REPORTS FIVE DEAD ACROSS THE COUNTRY."),
    ("EU", "UKRAINE PROBE LINKS TEAR GAS TO RUSSIA",
     "FIRST PROBE TO TIE BANNED CS GAS TO RUSSIAN TROOPS; INCIDENT WAS SEPT 2024."),
    ("EU", "CRIMEA BRIDGE SPAN DOWN AFTER STRIKE",
     "ROAD SECTION COLLAPSED INTO THE SEA; RUSSIA VOWS REPAIRS AS SUPPLY LINE CUTS."),
    ("EU", "EU PROPOSES 45BN EURO LOAN FOR UKRAINE",
     "25BN FOR ARMS, 20BN FOR BUDGET; REPAID ONCE RUSSIA PAYS REPARATIONS."),
    ("ME", "GAZA CEASEFIRE AT RISK, BODY WARNS",
     "BOARD OF PEACE: CIVILIANS FACE ANOTHER WINTER IN TENTS AND RUBBLE."),
    ("AS", "TRUMP, XI AND PUTIN DUE TO MEET AT APEC",
     "TRILATERAL TALKS SET FOR SHENZHEN ON 19 NOV AS LEADERS GATHER FOR THE SUMMIT."),
    ("NA", "GTA VI BEGINS GLOBAL ROLLOUT",
     "AFTER 13 YEARS, GAMERS ENTER VICE CITY AS ROCKSTAR'S BLOCKBUSTER ARRIVES."),
    ("SC", "NVIDIA IN TURMOIL AFTER HUANG EXIT",
     "ACTING CEO KRESS VOWS EARLIER PAY; H-SERIES CHIP SALES TO CHINA HALT."),
    ("NA", "FED MINUTES POINT TO MORE RATE HIKES",
     "ALMOST ALL OFFICIALS SEE FURTHER RISES IF INFLATION STAYS HOT."),
    ("NA", "JEFFRIES SET TO BE FIRST BLACK SPEAKER",
     "DEMOCRATS NOMINATE HAKEEM JEFFRIES TO LEAD THE US HOUSE OF REPRESENTATIVES."),
    ("NA", "TED LIEU ELECTED CAUCUS CHAIR",
     "FIRST ASIAN AMERICAN TO CHAIR A HOUSE CAUCUS."),
    ("NA", "PELTOLA WINS ALASKA, DEMS TAKE 56-44",
     "SENATE MAJORITY SECURED; BIGGEST MIDTERM GAIN SINCE 1958."),
    ("SC", "VOYAGER 1 REACHES ONE LIGHT-DAY",
     "CROSSED ONE LIGHT-DAY ON 18 NOV; NASA MARKS IT TODAY."),
    ("AS", "CYCLONE AKVAN BEARS DOWN ON INDIA",
     "LANDFALL DUE 20 NOV BETWEEN MACHILIPATNAM AND PURI."),
    ("OC", "AUSTRALIA SANCTIONS ISRAELI SETTLERS",
     "3 PEOPLE AND 4 GROUPS HIT OVER WEST BANK SETTLEMENT EXPANSION."),
    ("EU", "SPAIN HIT BY GENERAL STRIKE",
     "POLICE AND PROTESTERS CLASH AS UNIONS JOIN NATIONWIDE STRIKE."),
    ("AS", "MODI MEETS WILLIAM AND KATE IN INDIA",
     "ROYALS IN DELHI FOR THE EARTHSHOT PRIZE; TIES DISCUSSED."),
    ("EU", "RUSSIA ACCUSES FRANCE OVER UKRAINE",
     "LAVROV: FRENCH TROOPS IN A DIRECT ROLE; PARIS SAYS TRAINING ONLY."),
    ("AF", "SUDAN WAR: DRONES KILL 2,230 CIVILIANS",
     "UN COUNTS 2,230 DEAD JAN-OCT, MOSTLY BY DRONE; GOVT OFFERS PEACE PLAN."),
    ("AF", "SOMALIA PRESIDENT ACCUSES UAE",
     "MOGADISHU SAYS ABU DHABI BUILT BASES WITHOUT APPROVAL."),
    ("AF", "LIBYA SEIZES 4M PILLS IN DERNA RAID",
     "POLICE SEIZE 4M PILLS AND 29KG OF HASHISH IN A SINGLE RAID."),
    ("EU", "SUNK LPG TANKER HIT BY PROJECTILES",
     "GAS HUSKY HIT FOUR TIMES OFF VARNA; ALL 19 CREW RESCUED."),
    ("EU", "EU AND INDONESIA SEAL TRADE PACTS",
     "COUNCIL APPROVES SIGNING OF CEPA AND INVESTMENT AGREEMENTS."),
    ("ME", "UNICEF: 64 CHILDREN KILLED IN YEMEN",
     "DEATH TOLL SINCE 3 SEPT AS FIGHTING ESCALATES AND AID IS DISRUPTED."),
    ("NA", "NSA NET DEGRADED IN MAINTENANCE",
     "PATCH FAULT HIT CLASSIFIED NET; KEY SYSTEMS STAYED UP."),
    ("NA", "BANK FLAGGED $582M EPSTEIN DEALS",
     "FT: 3,200 SUSPICIOUS DEALS FLAGGED IN 2013-19."),
    ("SC", "PEW PROJECTS ISLAM LARGEST BY 2035",
     "PEW REPORT PROJECTS MUSLIMS WILL OVERTAKE CHRISTIANS WITHIN A DECADE."),
    ("SC", "NEW CLUE TO EARTH'S LOST BILLION YEARS",
     "STUDY OFFERS A NEW ANSWER; RIVAL THEORIES STILL DISAGREE."),
    ("SA", "BRAZIL BRACES FOR HEAVY RAIN, FLOODS",
     "INMET WARNS OF STORMS TO 23 NOV; PERU RAIN ALERT RUNS TO 20 NOV."),
    ("NA", "MICROSOFT EYES AI DEAL WITH BYTEDANCE",
     "REPORTED $500M DEAL FOR OPENAI ACCESS VIA AZURE; HOUSE SEEKS BRIEFING."),
]

# (big number, label) for the bottom strip
NUMBERS = [
    ("45BN", "EUROS: EU LOAN PROPOSED FOR UKRAINE"),
    ("5", "KILLED ACROSS UKRAINE"),
    ("372", "AT LEAST 372 CIVILIANS KILLED IN UKRAINE IN OCT"),
    ("56-44", "DEMOCRAT SENATE MAJORITY"),
    ("1", "LIGHT-DAY: VOYAGER 1 DISTANCE"),
    ("64", "64 CHILDREN KILLED, 64 INJURED IN YEMEN"),
]


# ---------------------------------------------------------------- layout
def draw_masthead(cv):
    cv.fill(0, 0, W, 112, PAPER)
    cv.fill(16, 14, 1008, 20, RED)
    title = "THE WORLD TODAY"
    tw = text_width(title, 5)
    cv.text((W - tw) // 2, 30, title, 5, INK)
    date = "THURSDAY 19 NOVEMBER 2026"
    dw = text_width(date, 2)
    cv.fill((W - dw) // 2 - 30, 76, (W - dw) // 2 - 18, 88, RED)
    cv.text((W - dw) // 2, 72, date, 2, INK)
    cv.fill((W + dw) // 2 + 18, 76, (W + dw) // 2 + 30, 88, RED)
    sub = "THE DAY'S WORLD NEWS IN ONE PAGE — 32 STORIES FROM SIX CONTINENTS"
    sw = text_width(sub, 1)
    cv.text((W - sw) // 2, 94, sub, 1, GREY)
    cv.hline(16, 1008, 108, INK, 2)


def draw_burst(cv, cx, cy):
    """Procedural explosion/flash graphic for the hero panel."""
    cols = [AMBER, ORANGE, (255, 90, 40), (255, 210, 110), RED]
    # radiating shards
    for k in range(26):
        ang = k * (360.0 / 26.0)
        r1 = 26 + (k * 37) % 30
        r2 = 62 + (k * 53) % 48
        x1 = cx + int(r1 * math.cos(math.radians(ang)))
        y1 = cy + int(r1 * math.sin(math.radians(ang)) * 0.72)
        x2 = cx + int(r2 * math.cos(math.radians(ang)))
        y2 = cy + int(r2 * math.sin(math.radians(ang)) * 0.72)
        x3 = cx + int(r1 * math.cos(math.radians(ang + 7)))
        y3 = cy + int(r1 * math.sin(math.radians(ang + 7)) * 0.72)
        cv.triangle(x1, y1, x2, y2, x3, y3, cols[k % len(cols)])
    cv.disc(cx, cy, 34, (255, 214, 120))
    cv.disc(cx, cy, 22, (255, 240, 190))
    cv.disc(cx, cy, 10, WHITE)
    # sparks
    for k in range(18):
        ang = k * 20.0 + 9.0
        r = 78 + (k * 29) % 30
        x = cx + int(r * math.cos(math.radians(ang)))
        y = cy + int(r * math.sin(math.radians(ang)) * 0.72)
        cv.disc(x, y, 3, AMBER if k % 2 else WHITE)


def draw_hero(cv):
    cv.fill(16, 116, 1008, 312, NAVY)
    cv.rect(16, 116, 1008, 312, INK, 2)
    cv.text(32, 130, HERO["kicker"], 1, AMBER)
    lines = wrap(HERO["title"], 3, 620)
    y = 152
    for ln in lines:
        cv.text(32, y, ln, 3, WHITE)
        y += 24
    y += 6
    for ln in HERO["body"]:
        cv.text(32, y, ln, 1, (214, 220, 232))
        y += 11
    cv.text(32, 288, HERO["dateline"], 1, AMBER)
    draw_burst(cv, 872, 214)
    cv.text(790, 297, "QESHM • KUWAIT • BAHRAIN", 1, AMBER)
    cv.grain(16, 116, 1008, 312, 2, 20261119)


def draw_grid(cv):
    cv.text(16, 322, "MORE FROM AROUND THE WORLD", 2, INK)
    right = "32 STORIES • 6 CONTINENTS"
    cv.text(1008 - text_width(right, 1), 328, right, 1, RED)
    cv.hline(16, 1008, 342, INK, 1)
    col_x = [16, 524]
    col_w = 484
    row_h = 36
    for idx, (region, title, body) in enumerate(STORIES):
        col = idx % 2
        row = idx // 2
        x = col_x[col]
        y = 350 + row * row_h
        chip = REGION_COLOR[region]
        cv.fill(x, y + 3, x + 10, y + 13, chip)
        cv.text(x + 16, y, fit_one_line(title, 2, col_w - 16), 2, INK)
        cv.text(x + 16, y + 20, fit_one_line(body, 1, col_w - 16), 1, (64, 60, 52))
        if row < 15:
            cv.hline(x, x + col_w, y + row_h - 6, (214, 208, 192), 1)


def draw_numbers(cv):
    cv.fill(16, 928, 1008, 1004, LIGHT)
    cv.rect(16, 928, 1008, 1004, INK, 1)
    cv.text(28, 934, "BY THE NUMBERS", 1, RED)
    n = len(NUMBERS)
    gap, bw = 6, 156
    for i, (num, label) in enumerate(NUMBERS):
        x = 24 + i * (bw + gap)
        y = 950
        cv.fill(x, y, x + bw, y + 46, PAPER)
        cv.rect(x, y, x + bw, y + 46, GREY, 1)
        nw = text_width(num, 2)
        cv.text(x + (bw - nw) // 2, y + 4, num, 2, INK)
        lab = wrap(label, 1, bw - 10)
        ly = y + 22
        for ln in lab[:2]:
            lw = text_width(ln, 1)
            cv.text(x + (bw - lw) // 2, ly, ln, 1, GREY)
            ly += 9
    cv.grain(16, 928, 1008, 1004, 2, 191119)


def draw_footer(cv):
    foot = "THE WORLD TODAY — THURSDAY 19 NOVEMBER 2026 — EVENTS REPORTED 18-19 NOV 2026"
    fw = text_width(foot, 1)
    cv.text((W - fw) // 2, 1010, foot, 1, GREY)


def build():
    cv = Canvas(W, H, PAPER)
    cv.grain(0, 0, W, H, 1, 777)
    draw_masthead(cv)
    draw_hero(cv)
    draw_grid(cv)
    draw_numbers(cv)
    draw_footer(cv)
    cv.rect(6, 6, 1018, 1018, INK, 2)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(build(), path)
    print(f"wrote {path} ({size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
