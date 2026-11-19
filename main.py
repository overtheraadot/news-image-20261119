#!/usr/bin/env python3
"""THE WORLD - Thursday 19 November 2026.

A newspaper front page that sums up the day's world news in one image.
Draws everything itself (5x7 bitmap font, polygon world map, hand-rolled
PNG encoder) with Python 3.13 standard library only, no network, and no
third-party imports. Deterministic: two runs write identical bytes.

Layout (1024x1024):
  masthead -> world-map strip with story dots -> lead story (GTA VI)
  -> 35 numbered stories in 3 columns, grouped by region, colour-coded
  by category -> sources footer.
"""
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (24, 24, 24)
GREY = (96, 96, 90)
RULE = (24, 24, 24)
RED = (176, 42, 32)
OCEAN = (214, 230, 240)
LAND = (122, 139, 122)
LANDLINE = (90, 105, 90)
DOT = (176, 42, 32)
LEADBG = (255, 248, 220)

CATS = {
    "POLITICS": (39, 68, 114),
    "CONFLICT": (169, 50, 38),
    "ECONOMY": (30, 132, 73),
    "TECH": (108, 52, 131),
    "CULTURE": (160, 120, 10),
    "SPORT": (17, 120, 100),
    "SCIENCE": (46, 134, 193),
    "WORLD": (97, 106, 107),
}

# 5x7 bitmap font, '#' = ink. Only the glyphs the page uses.
FONT = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (" ### ", "#  ##", "# # #", "##  #", "#   #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "),
    ",": ("     ", "     ", "     ", "     ", " ##  ", " ##  ", " #   "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "'": ("  #  ", "  #  ", "     ", "     ", "     ", "     ", "     "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "/": ("    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "),
    "(": ("   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "),
    ")": (" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "),
    "%": ("#   #", "#  # ", "   # ", "  #  ", " #   ", "#  # ", "#   #"),
    "&": (" ##  ", "#  # ", "#  # ", " #   ", "# # #", "#  # ", " ## #"),
    "$": ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
    "+": ("     ", "  #  ", "  #  ", " ### ", "  #  ", "  #  ", "     "),
    "=": ("     ", "     ", "#####", "     ", "#####", "     ", "     "),
    ":": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    ";": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "),
    '"': (" # # ", " # # ", "     ", "     ", "     ", "     ", "     "),
    "*": ("     ", "# # #", " ### ", "#####", " ### ", "# # #", "     "),
    "#": (" # # ", " # # ", "#####", " # # ", "#####", " # # ", " # # "),
    "@": (" ### ", "#   #", "# ###", "# # #", "# ## ", "#    ", " ### "),
    "_": ("     ", "     ", "     ", "     ", "     ", "     ", "#####"),
    "<": ("   # ", "  #  ", " #   ", "#    ", " #   ", "  #  ", "   # "),
    ">": (" #   ", "  #  ", "   # ", "    #", "   # ", "  #  ", " #   "),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            if yy < 0 or yy >= self.h:
                continue
            base = (yy * self.w + max(x, 0)) * 3
            for xx in range(max(x, 0), min(x + w, self.w)):
                i = (yy * self.w + xx) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def fill_poly(self, pts, color):
        # Scanline fill of a simple polygon (lon/lat already mapped to px).
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                for x in range(int(xs[j]), int(xs[j + 1]) + 1):
                    self.set(x, y, color)

    def text(self, x, y, s, scale=1, color=INK):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale=1):
        return len(s) * 6 * scale - scale


def wrap(text, width_chars):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= width_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw.extend(canvas.px[y * stride:(y + 1) * stride])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h,
                                      8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

LEAD = {
    "headline": "VICE CITY OPENS: GTA VI LAUNCHES TODAY",
    "summary": ("After 13 years, Rockstar's Grand Theft Auto VI is out on PS5 and "
                "Xbox Series X/S. Some 15 million copies were pre-ordered."),
}

# (category, headline, summary, lat, lon or None)
# Columns are regional: Americas & Europe | Middle East & Asia | Africa & the World
COLUMNS = [
    ("AMERICAS & EUROPE", [
        ("POLITICS", "JEFFRIES SET TO BE FIRST BLACK SPEAKER",
         "House Democrats nominate Hakeem Jeffries 251-11; the full House votes on 3 January.", 38.9, -77.0),
        ("POLITICS", "PELTOLA WINS ALASKA, DEMS TAKE SENATE",
         "Democrat Mary Peltola wins Alaska's Senate race, securing a 56-44 "
         "Democratic majority in the chamber.", 64.0, -152.0),
        ("POLITICS", "US TIGHTENS RULES FOR WORK GREEN CARDS",
         "Washington proposes tougher rules for work green cards, lengthening the hiring process.", 38.9, -77.0),
        ("TECH", "SENATORS: AI CYBER THREATS OUTPACING US",
         "US senators warn the White House that AI-enabled cyber threats are "
         "outpacing US defences.", 38.9, -77.0),
        ("WORLD", "MCDONALD'S ABUSE: GIRLS TARGETED AT 18",
         "An inquiry hears McDonald's staff waited for younger girls to turn "
         "18 before abusing them, witnesses say.", 51.5, -0.1),
        ("ECONOMY", "DEUTSCHE BANK AND $582M EPSTEIN LINK",
         "Deutsche Bank handled $582m of transactions linked to Jeffrey Epstein in 2013-2018, reports say.", 50.1, 8.7),
        ("CULTURE", "VAN GOGH SELLS FOR RECORD $190.4M",
         "A Van Gogh painting sells for a record $190.4 million after a row "
         "over its Nazi-era history.", 52.4, 4.9),
        ("POLITICS", "MELENCHON COULD WIN, MINISTER WARNS",
         "France's justice minister says hard-left leader Jean-Luc Melenchon could win the presidency.", 48.9, 2.35),
        ("ECONOMY", "EU PLANS EUR 45BN LOAN FOR UKRAINE",
         "The EU proposes a EUR 45 billion loan to Kyiv, to be repaid after "
         "Russia pays war reparations.", 50.85, 4.35),
        ("CONFLICT", "CRIMEAN BRIDGE ATTACKED AGAIN",
         "The Crimean Bridge is attacked again, a Russian official says.", 45.3, 36.5),
        ("CONFLICT", "ZELENSKY: US BLOCKING PAID MISSILES",
         "Ukraine's president accuses the US of delaying missile deliveries Kyiv already paid for.", 50.4, 30.5),
        ("WORLD", "CLIMBER SURVIVES 100M ALPS FALL",
         "A 31-year-old German mountaineer survives a 100-metre fall in the "
         "Tyrolean Alps, local authorities say.", 47.3, 11.0),
    ]),
    ("MIDDLE EAST & ASIA", [
        ("POLITICS", "TRUMP, XI AND PUTIN MEET IN SHENZHEN",
         "The US, Chinese and Russian leaders shake hands in Shenzhen and hold "
         "a trilateral meeting on Thursday.", 22.5, 114.0),
        ("CONFLICT", "SAUDI BRACES FOR LONG YEMEN WAR",
         "Saudi Arabia prepares for its war with the Houthis to last into 2027, Reuters reports.", 24.7, 46.7),
        ("CONFLICT", "HOUTHI ROCKET KILLS 53 IN YEMEN",
         "A Houthi rocket attack on a military camp kills at least 53 soldiers of Yemen's government.", 15.4, 44.2),
        ("CONFLICT", "ISRAELI TANKS CROSS GAZA CEASEFIRE LINE",
         "Israel's military launches a rare ground operation in Gaza beyond "
         "the Yellow Line ceasefire boundary.", 31.5, 34.4),
        ("WORLD", "SAUDI: DANGER PASSED IN SOUTHERN CITIES",
         "Saudi Arabia says the danger has passed in three southern cities after air raid alerts.", 24.7, 46.7),
        ("POLITICS", "INDIA, JAPAN REVIEW DEFENCE TIES",
         "India and Japan hold a 2+2 dialogue in Tokyo to review defence and strategic cooperation.", 35.7, 139.7),
        ("POLITICS", "MODI MEETS WILLIAM AND KATE IN DELHI",
         "India's PM meets the Prince and Princess of Wales to discuss "
         "boosting UK-India ties.", 28.6, 77.2),
        ("WORLD", "CYCLONE AKVAN NEARS INDIA'S COAST",
         "Cyclone Akvan is likely to cross the coast between Machilipatnam "
         "and Puri, India's disaster agency says.", 17.0, 82.3),
        ("CONFLICT", "NORTH KOREA FIRES MISSILES AFTER DRILL",
         "North Korea launches ballistic missiles hours after joint US, South Korean and Japanese drills end.", 39.0, 125.8),
        ("POLITICS", "MYANMAR FACES ICJ GENOCIDE VERDICT",
         "Myanmar faces a historic UN court verdict over the Rohingya "
         "massacres, in a landmark genocide case.", 21.9, 96.0),
        ("POLITICS", "CANADA RESETS CHINA TIES, EYES US DEAL",
         "PM Mark Carney says Canada is adjusting China ties as Ottawa seeks the right trade deal with the US.", 45.4, -75.7),
        ("POLITICS", "SOMALIA ACCUSES UAE OF SECRET BASES",
         "Somalia accuses the UAE of secretly building military bases on its soil without approval.", 2.0, 45.3),
    ]),
    ("AFRICA & THE WORLD", [
        ("WORLD", "COCAINE AND MILLIONS OF PILLS SEIZED",
         "Cocaine and millions of pills are seized in eastern Libya, "
         "officials say, in a major drugs bust.", 32.9, 22.0),
        ("WORLD", "LPG TANKER OFF BULGARIA HIT BY FIRE",
         "An LPG tanker that sank off Bulgaria was hit by projectiles, an "
         "official says.", 43.0, 28.0),
        ("POLITICS", "AUSTRALIA SANCTIONS ISRAELI SETTLERS",
         "Australia sanctions Israeli settlers and organisations over West "
         "Bank expansion.", -35.3, 149.1),
        ("ECONOMY", "ANTHROPIC DEBUTS ON NASDAQ AS ANT",
         "Claude-maker Anthropic starts trading on Nasdaq after pricing its IPO at $83 a share, above its range.", 37.8, -122.4),
        ("ECONOMY", "NVIDIA REVENUE DOUBLES TO $115.8BN",
         "Nvidia reports quarterly revenue of $115.8 billion, up 103%, but "
         "its shares fall after the results.", 37.4, -122.1),
        ("ECONOMY", "WALL ST MIXED; DOW FALLS 561 POINTS",
         "US stocks end mixed: the Dow falls 1.11% to 50,198 and the S&P 500 logs a fifth straight loss.", 40.7, -74.0),
        ("CULTURE", "ISLAM TO BE LARGEST FAITH BY 2035",
         "A Pew Research report projects Islam will become the world's "
         "largest religion by 2035.", 38.9, -77.0),
        ("SCIENCE", "VOYAGER 1 REACHES ONE LIGHT-DAY",
         "NASA's Voyager 1, in space for almost 50 years, is believed to "
         "have reached one light-day from Earth.", 34.0, -118.0),
        ("SCIENCE", "FINLAND OPENS FIRST NUCLEAR WASTE SITE",
         "Finland approves the operation of the world's first repository for "
         "spent nuclear fuel.", 60.2, 25.0),
        ("SCIENCE", "REEFS FACE EXTINCTION IN 50 YEARS",
         "Nearly all coral reefs face extinction within 50 years from climate "
         "change, an IUCN study warns.", -18.3, 147.7),
        ("SCIENCE", "EARTH'S MISSING BILLION YEARS FOUND?",
         "Earth is missing over a billion years of geological history; scientists may have found why.", 51.5, -0.1),
        ("SPORT", "DUCKETT 133 PUTS ENGLAND ON TOP",
         "Ben Duckett scores 133 as England take a strong position against "
         "Australia in the third ODI.", -33.9, 151.2),
    ]),
]

# Rough continent outlines as (lon, lat) polygons.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 80),
     (-80, 73), (-75, 72), (-70, 62), (-65, 60), (-55, 52), (-60, 47),
     (-70, 44), (-75, 39), (-80, 32), (-81, 26), (-90, 21), (-95, 19),
     (-105, 20), (-115, 28), (-125, 40), (-125, 49), (-140, 60),
     (-155, 58), (-165, 60)],
    [(-58, 64), (-45, 60), (-40, 65), (-30, 68), (-20, 70), (-25, 76),
     (-45, 76), (-58, 74)],
    [(-80, 10), (-72, 12), (-62, 10), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-40, -20), (-48, -28), (-58, -35), (-65, -41), (-70, -50),
     (-73, -54), (-73, -40), (-72, -20), (-80, -5), (-81, 0)],
    [(-17, 15), (-10, 30), (-5, 35), (10, 37), (20, 32), (32, 31),
     (35, 28), (43, 12), (51, 11), (48, 2), (40, -5), (40, -15),
     (35, -25), (28, -33), (20, -35), (15, -27), (12, -18), (9, 4),
     (-8, 5)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (40, 68), (55, 69),
     (70, 72), (90, 75), (110, 76), (130, 72), (150, 70), (170, 66),
     (178, 65), (170, 60), (162, 56), (158, 52), (142, 50), (140, 40),
     (135, 35), (130, 32), (122, 30), (120, 25), (110, 20), (108, 12),
     (105, 9), (100, 8), (98, 12), (95, 16), (90, 22), (85, 20), (80, 15),
     (77, 8), (72, 20), (66, 25), (60, 25), (56, 26), (52, 28), (48, 30),
     (44, 29), (40, 31), (36, 36), (30, 36), (26, 38), (22, 37), (19, 40),
     (15, 44), (12, 44), (8, 44), (3, 43), (-2, 37), (-6, 36)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (137, -35),
     (140, -38), (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (142, -15), (142, -11), (136, -12), (132, -12), (126, -14),
     (122, -17), (118, -20)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51)],
    [(130, 31), (132, 33), (135, 34), (138, 35), (140, 36), (141, 39),
     (141, 42), (143, 44), (145, 44), (142, 42), (140, 38), (137, 37),
     (133, 35), (131, 33)],
    [(95, 5), (98, 3), (100, -2), (104, -4), (106, -6), (110, -7),
     (114, -8), (118, -9), (120, -10), (125, -9), (130, -3), (135, -4),
     (138, -8), (141, -8), (140, -4), (137, 0), (132, 0), (128, 2),
     (125, 1), (120, 0), (117, 0), (113, 2), (108, 3), (103, 2), (100, 5)],
    [(44, -16), (47, -15), (50, -16), (49, -20), (46, -24), (44, -25),
     (43, -20)],
    [(167, -45), (170, -42), (174, -41), (176, -38), (178, -38),
     (175, -40), (172, -43), (168, -46)],
]


def project(lon, lat):
    x = 16 + (lon + 180.0) / 360.0 * 992
    y = 100 + (80.0 - lat) / 138.0 * 126
    return int(x), int(y)


def draw_map(cv):
    cv.rect(16, 100, 992, 126, OCEAN)
    for lon in range(-180, 181, 60):
        x, _ = project(lon, 80)
        cv.vline(x, 100, 126, (190, 205, 215))
    for lat in range(-60, 81, 30):
        _, y = project(0, lat)
        cv.hline(16, y, 992, (190, 205, 215))
    for poly in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in poly]
        cv.fill_poly(pts, LAND)
    # Story dots: every grid story has a lat/lon.
    for _region, stories in COLUMNS:
        for story in stories:
            _cat, _h, _s, lat, lon = story
            x, y = project(lon, lat)
            cv.circle(x, y, 5, (255, 255, 255))
            cv.circle(x, y, 4, DOT)
    cv.rect(16, 100, 992, 2, RULE)
    cv.rect(16, 224, 992, 2, RULE)


def draw(cv):
    cv.rect(0, 0, W, H, PAPER)

    # Masthead.
    title = "THE WORLD"
    tw = cv.text_w(title, 8)
    cv.text((W - tw) // 2, 10, title, 8, INK)
    date_line = "THURSDAY 19 NOVEMBER 2026  -  37 STORIES FROM ONE DAY"
    dw = cv.text_w(date_line, 2)
    cv.text((W - dw) // 2, 72, date_line, 2, GREY)
    cv.hline(16, 92, 992, RULE, 3)
    cv.hline(16, 97, 992, RULE, 1)

    # World map strip.
    draw_map(cv)
    cap = "RED DOTS MARK WHERE THE DAY'S NEWS HAPPENED"
    cv.text((W - cv.text_w(cap, 1)) // 2, 230, cap, 1, GREY)

    # Lead story banner.
    cv.rect(16, 236, 992, 76, LEADBG)
    cv.rect(16, 236, 8, 76, RED)
    cv.text(32, 246, LEAD["headline"], 3, INK)
    lead_lines = wrap(LEAD["summary"], 78)
    for i, line in enumerate(lead_lines[:2]):
        cv.text(32, 274 + i * 14, line, 2, INK)

    # Column headers (regions).
    col_x = [16, 352, 688]
    for i, (region, _stories) in enumerate(COLUMNS):
        rw = cv.text_w(region, 1)
        cv.text(col_x[i] + (320 - rw) // 2, 318, region, 1, GREY)
    cv.hline(16, 328, 992, RULE, 1)

    # Story grid: 12 rows x 3 columns.
    num = 0
    for ci, (_region, stories) in enumerate(COLUMNS):
        x = col_x[ci]
        for ri, story in enumerate(stories):
            cat, headline, summary, _lat, _lon = story
            num += 1
            y0 = 332 + ri * 56
            cv.text(x, y0 + 2, "%02d" % num, 1, RED)
            chip_w = len(cat) * 6 + 8
            cv.rect(x + 16, y0, chip_w, 11, CATS[cat])
            cv.text(x + 20, y0 + 2, cat, 1, (255, 255, 255))
            hl = wrap(headline, 26)
            for i, line in enumerate(hl[:2]):
                cv.text(x, y0 + 13 + i * 14, line, 2, INK)
            sl = wrap(summary, 53)
            for i, line in enumerate(sl[:2]):
                cv.text(x, y0 + 42 + i * 7, line, 1, INK)

    # Footer.
    foot = ("SOURCES: AP, REUTERS, BBC, CNN, AL JAZEERA, THE HINDU, NDTV "
            "- ALL EVENTS OF 19 NOVEMBER 2026")
    cv.text((W - cv.text_w(foot, 1)) // 2, 1008, foot, 1, GREY)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw(cv)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
