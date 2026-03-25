"""
Creates a TikTok app review demo video showing the WiredWrong Publisher integration.
Saves to output/tiktok_demo.mp4
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import ImageClip, concatenate_videoclips
from loguru import logger

W, H = 1920, 1080
BG = (10, 10, 20)
ACCENT = (120, 60, 220)
WHITE = (255, 255, 255)
GRAY = (160, 160, 180)
GREEN = (60, 220, 120)
TERM_BG = (18, 18, 28)
TERM_GREEN = (80, 220, 100)
TERM_WHITE = (220, 220, 220)
TERM_CYAN = (80, 200, 220)
TERM_YELLOW = (220, 200, 80)


def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def make_frame(draw_fn, duration=3.0):
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_fn(img, draw)
    arr = np.array(img)
    return ImageClip(arr, duration=duration)


def draw_header(draw, title, subtitle=None):
    # Purple top bar
    draw.rectangle([0, 0, W, 90], fill=ACCENT)
    f_title = load_font(36, bold=True)
    draw.text((40, 25), title, fill=WHITE, font=f_title)
    if subtitle:
        f_sub = load_font(24)
        draw.text((40, 110), subtitle, fill=GRAY, font=f_sub)


def draw_terminal_box(draw, x, y, w, h, lines):
    """Draw a fake terminal window with colored text lines."""
    draw.rectangle([x, y, x+w, y+h], fill=TERM_BG, outline=ACCENT, width=2)
    # Title bar
    draw.rectangle([x, y, x+w, y+30], fill=(30, 30, 50))
    draw.text((x+12, y+6), "● ● ●  Terminal — WiredWrong Publisher", fill=GRAY, font=load_font(14))
    f_mono = load_font(18)
    ty = y + 42
    for color, text in lines:
        draw.text((x+18, ty), text, fill=color, font=f_mono)
        ty += 26


def draw_badge(draw, x, y, text, color=GREEN):
    f = load_font(18, bold=True)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0] + 24
    draw.rounded_rectangle([x, y, x+tw, y+32], radius=8, fill=color)
    draw.text((x+12, y+6), text, fill=(10, 10, 20), font=f)


# ── Slide 1: Title card ────────────────────────────────────────────────────
def slide_title(img, draw):
    draw.rectangle([0, 0, W, H], fill=BG)
    draw.rectangle([0, 0, W, 8], fill=ACCENT)
    draw.rectangle([0, H-8, W, H], fill=ACCENT)

    logo_font = load_font(96, bold=True)
    title_font = load_font(48, bold=True)
    sub_font = load_font(28)

    # WW logo circle
    cx, cy = W//2, H//2 - 60
    draw.ellipse([cx-110, cy-110, cx+110, cy+110], fill=(20, 15, 50), outline=ACCENT, width=6)
    draw.text((cx-60, cy-56), "WW", fill=WHITE, font=logo_font)

    draw.text((W//2 - 280, cy + 140), "WiredWrong Publisher", fill=WHITE, font=title_font)
    draw.text((W//2 - 310, cy + 200), "TikTok Content Posting API — Integration Demo", fill=GRAY, font=sub_font)
    draw_badge(draw, W//2 - 80, cy + 260, "v1.0  |  Personal Creator Tool", color=ACCENT)


# ── Slide 2: What the app does ────────────────────────────────────────────
def slide_overview(img, draw):
    draw_header(draw, "WiredWrong Publisher — What It Does",
                "Automated cross-posting of original psychology short-form videos to TikTok")

    f = load_font(26)
    f_bold = load_font(26, bold=True)
    items = [
        ("1.", "Produces original psychology video content (scripts, voiceover, B-roll, render)"),
        ("2.", "Uploads to YouTube Shorts — the primary publishing platform"),
        ("3.", "Cross-posts the same MP4 to TikTok using Content Posting API"),
        ("4.", "All posts are original content owned by the creator — no third-party users"),
    ]
    y = 180
    for num, text in items:
        draw.rectangle([80, y, 86, y+36], fill=ACCENT)
        draw.text((110, y), num, fill=ACCENT, font=f_bold)
        draw.text((160, y), text, fill=WHITE, font=f)
        y += 70

    draw_terminal_box(draw, 80, 470, W-160, 200, [
        (TERM_CYAN,  "$ python scripts/run_pipeline.py upload"),
        (TERM_WHITE, ""),
        (TERM_GREEN, "✓ YouTube uploaded: https://youtube.com/shorts/xyz"),
        (TERM_GREEN, "✓ TikTok cross-posted: publish_id=ABC123"),
        (TERM_WHITE, ""),
        (TERM_YELLOW,"  Pipeline complete — 1 video published to YouTube + TikTok"),
    ])


# ── Slide 3: OAuth2 login flow ────────────────────────────────────────────
def slide_auth(img, draw):
    draw_header(draw, "Login Kit — OAuth2 Authentication Flow",
                "Creator authenticates once via browser. Token stored locally. No user data collected.")

    steps = [
        ("Step 1", "Run setup script:", "python scripts/setup_tiktok_auth.py"),
        ("Step 2", "Browser opens TikTok authorization page", "Creator clicks 'Authorize'"),
        ("Step 3", "TikTok redirects with auth code", "Script exchanges code for access + refresh tokens"),
        ("Step 4", "Tokens saved to config/tiktok_token.json", "Auto-refresh before each upload session"),
    ]
    f_label = load_font(20, bold=True)
    f_text = load_font(20)
    f_code = load_font(18)

    y = 165
    for label, line1, line2 in steps:
        draw.rounded_rectangle([80, y, W-80, y+75], radius=10, fill=(20, 20, 40), outline=(60, 60, 100), width=1)
        draw_badge(draw, 100, y+20, label, color=ACCENT)
        draw.text((230, y+14), line1, fill=WHITE, font=f_text)
        draw.text((230, y+42), line2, fill=TERM_CYAN, font=f_code)
        y += 95

    draw_terminal_box(draw, 80, y+10, W-160, 140, [
        (TERM_WHITE, "Opening TikTok authorization in browser..."),
        (TERM_GREEN, "✓ Authorization code received"),
        (TERM_GREEN, "✓ Token exchanged successfully"),
        (TERM_GREEN, "✓ Token saved to config/tiktok_token.json"),
        (TERM_YELLOW, "  Authenticated as: @wiredwrong_b15"),
    ])


# ── Slide 4: Content Posting API — scopes ─────────────────────────────────
def slide_scopes(img, draw):
    draw_header(draw, "Content Posting API — Scopes Used",
                "video.publish + video.upload — used exclusively to post creator's own original content")

    f = load_font(22)
    f_bold = load_font(22, bold=True)
    f_code = load_font(19)

    # Scope cards
    scopes = [
        ("video.upload", TERM_CYAN,
         "Initiates chunked file upload to TikTok servers.",
         "Used once per video to send the MP4 file."),
        ("video.publish", GREEN,
         "Publishes the uploaded video to the creator's TikTok profile.",
         "Privacy: PUBLIC_TO_EVERYONE. Content: original psychology shorts."),
        ("user.info.basic", GRAY,
         "Included automatically with Login Kit.",
         "Used only to confirm authenticated creator identity."),
    ]

    y = 160
    for scope, color, desc1, desc2 in scopes:
        draw.rounded_rectangle([80, y, W-80, y+110], radius=10, fill=(18, 18, 35), outline=color, width=2)
        draw.text((110, y+14), scope, fill=color, font=f_bold)
        draw.text((110, y+50), desc1, fill=WHITE, font=f)
        draw.text((110, y+78), desc2, fill=GRAY, font=f_code)
        y += 130

    draw_terminal_box(draw, 80, y+10, W-160, 100, [
        (TERM_CYAN,  "POST /v2/post/publish/video/init/   →  chunk_size, total_chunk_count"),
        (TERM_GREEN, "PUT  upload_url                     →  binary video chunks"),
        (TERM_GREEN, "GET  /v2/post/publish/status/fetch/ →  publish_id confirmed"),
    ])


# ── Slide 5: Upload pipeline ──────────────────────────────────────────────
def slide_pipeline(img, draw):
    draw_header(draw, "End-to-End Upload Pipeline",
                "Every video goes through the same automated pipeline — no human in the loop after approval")

    stages = [
        ("Idea", "Topic generated from analytics + trends"),
        ("Script", "Claude AI writes hook, body, CTA"),
        ("Voice", "ElevenLabs TTS narration"),
        ("B-roll", "Pexels stock footage fetched"),
        ("Render", "MoviePy assembles final MP4"),
        ("YouTube", "Uploaded via YouTube Data API v3"),
        ("TikTok", "Cross-posted via Content Posting API"),
    ]

    f = load_font(20)
    f_bold = load_font(20, bold=True)
    box_w = (W - 120) // len(stages) - 10
    x = 60
    y = 180

    for i, (label, desc) in enumerate(stages):
        color = GREEN if label in ("YouTube", "TikTok") else ACCENT
        draw.rounded_rectangle([x, y, x+box_w, y+80], radius=8, fill=(18, 18, 40), outline=color, width=2)
        tw = draw.textlength(label, font=f_bold)
        draw.text((x + (box_w-tw)//2, y+10), label, fill=color, font=f_bold)
        # Wrap desc
        words = desc.split()
        line, lines = "", []
        for w in words:
            if draw.textlength(line + w, font=f) < box_w - 10:
                line += w + " "
            else:
                lines.append(line.strip())
                line = w + " "
        lines.append(line.strip())
        ty = y + 38
        for l in lines[:2]:
            lw = draw.textlength(l, font=f)
            draw.text((x + (box_w-lw)//2, ty), l, fill=GRAY, font=f)
            ty += 22

        if i < len(stages)-1:
            draw.line([x+box_w+2, y+40, x+box_w+12, y+40], fill=ACCENT, width=2)
        x += box_w + 12

    # Sample video output
    draw_terminal_box(draw, 60, 310, W-120, 260, [
        (TERM_CYAN,  "$ python scripts/run_pipeline.py upload"),
        (TERM_WHITE, ""),
        (TERM_WHITE, "  Uploading: 'Your Best Work Traps You'"),
        (TERM_GREEN, "  ✓ YouTube: https://youtube.com/shorts/HBAG1QkPX2k"),
        (TERM_GREEN, "  ✓ TikTok init OK — publish_id: 7ABC123DEF"),
        (TERM_GREEN, "  ✓ Chunks uploaded (32.4 MB in 4 chunks)"),
        (TERM_GREEN, "  ✓ TikTok published — status: PUBLISH_COMPLETE"),
        (TERM_WHITE, ""),
        (TERM_YELLOW, "  ✓ Pipeline complete — video live on both platforms"),
    ])


# ── Slide 6: Privacy + compliance ─────────────────────────────────────────
def slide_privacy(img, draw):
    draw_header(draw, "Privacy & Compliance",
                "Single-creator tool — no user data collected, no third parties, no public interface")

    f = load_font(24)
    f_bold = load_font(24, bold=True)

    rows = [
        ("Data collected from TikTok users", "None"),
        ("Third-party access to tokens", "None — stored locally only"),
        ("Public-facing interface", "None — CLI tool, private machine"),
        ("Other accounts accessing the app", "None — single creator only"),
        ("Content posted", "Original psychology short-form videos"),
        ("Post frequency", "Up to 10 videos/day, creator-approved"),
        ("Token storage", "config/tiktok_token.json (local disk only)"),
    ]

    y = 165
    for i, (question, answer) in enumerate(rows):
        bg = (18, 18, 35) if i % 2 == 0 else (22, 22, 42)
        draw.rectangle([80, y, W-80, y+52], fill=bg)
        draw.text((110, y+14), question, fill=GRAY, font=f)
        draw.text((W-500, y+14), answer, fill=GREEN, font=f_bold)
        y += 54

    draw.text((110, y+20), "Channel:", fill=GRAY, font=f)
    draw.text((110, y+50), "youtube.com/@WiredWrong  |  TikTok: @wiredwrong_b15", fill=ACCENT, font=f_bold)


# ── Build video ────────────────────────────────────────────────────────────
slides = [
    (slide_title,    4.0),
    (slide_overview, 5.0),
    (slide_auth,     5.0),
    (slide_scopes,   5.0),
    (slide_pipeline, 6.0),
    (slide_privacy,  5.0),
]

clips = []
for fn, dur in slides:
    clips.append(make_frame(fn, duration=dur))

logger.info("Compositing demo video...")
final = concatenate_videoclips(clips, method="compose")
out = Path("output/tiktok_demo.mp4")
final.write_videofile(
    str(out),
    fps=24,
    codec="libx264",
    audio=False,
    logger=None,
)
logger.info(f"Demo video saved: {out} ({out.stat().st_size/1024/1024:.1f} MB)")
