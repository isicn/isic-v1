#!/usr/bin/env python3
"""Generate Odoo 19-style module icons for ISIC custom modules.

Usage: python3 scripts/generate_icons.py

Generates 100x100 RGBA PNG icons using 4x supersampling (400x400 -> 100x100)
to achieve smooth anti-aliased edges matching Odoo 19's native icon style.
"""

import math
import os

from PIL import Image, ImageDraw

# === Odoo 19 Color Palette ===
TEAL = (26, 211, 187, 255)
PURPLE = (152, 81, 132, 255)
AMBER = (251, 185, 69, 255)
CORAL = (252, 134, 139, 255)
SKY_BLUE = (46, 188, 250, 255)
DEEP_BLUE = (8, 139, 245, 255)
ORANGE = (247, 134, 19, 255)
RED = (249, 70, 76, 255)
DARK_TEAL = (0, 94, 122, 255)
DARK_PURPLE = (113, 34, 88, 255)
NAVY = (20, 68, 150, 255)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

SCALE = 4  # Supersampling factor
SIZE = 100
CANVAS = SIZE * SCALE  # 400


# === Helper Functions ===

def s(val):
    """Scale a coordinate value by SCALE factor."""
    return int(val * SCALE)


def new_canvas():
    """Create transparent 400x400 RGBA canvas."""
    return Image.new("RGBA", (CANVAS, CANVAS), TRANSPARENT)


def finalize(img, path):
    """Downsample 400x400 to 100x100 and save optimized PNG."""
    small = img.resize((SIZE, SIZE), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    small.save(path, "PNG", optimize=True)
    fsize = os.path.getsize(path)
    print(f"  {os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))}: {path} ({fsize} bytes)")


def draw_rounded_rect(draw, bbox, radius, fill):
    """Draw a rounded rectangle (compatible helper)."""
    draw.rounded_rectangle(bbox, radius=radius, fill=fill)


# === Icon Drawing Functions ===

def draw_isic_base():
    """Foundation diamond with layered blue facets."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = CANVAS // 2, CANVAS // 2

    # Large diamond - Deep Blue
    size1 = s(38)
    d.polygon([
        (cx, cy - size1),
        (cx + size1, cy),
        (cx, cy + size1),
        (cx - size1, cy),
    ], fill=DEEP_BLUE)

    # Medium diamond offset - Navy (semi-transparent layer)
    layer = new_canvas()
    dl = ImageDraw.Draw(layer)
    size2 = s(28)
    off = s(6)
    dl.polygon([
        (cx + off, cy - size2),
        (cx + off + size2, cy),
        (cx + off, cy + size2),
        (cx + off - size2, cy),
    ], fill=(*NAVY[:3], 180))
    img = Image.alpha_composite(img, layer)

    # Small highlight diamond - Sky Blue
    layer2 = new_canvas()
    dl2 = ImageDraw.Draw(layer2)
    size3 = s(18)
    dl2.polygon([
        (cx - s(5), cy - size3 - s(5)),
        (cx - s(5) + size3, cy - s(5)),
        (cx - s(5), cy - s(5) + size3),
        (cx - s(5) - size3, cy - s(5)),
    ], fill=(*SKY_BLUE[:3], 200))
    img = Image.alpha_composite(img, layer2)

    return img


def draw_referentiel():
    """Three cascading rounded rectangles representing LMD hierarchy."""
    img = new_canvas()

    # Card 1 (back/largest) - Teal
    layer1 = new_canvas()
    d1 = ImageDraw.Draw(layer1)
    draw_rounded_rect(d1, [s(8), s(8), s(72), s(65)], s(8), TEAL)
    img = Image.alpha_composite(img, layer1)

    # Card 2 (middle) - Purple
    layer2 = new_canvas()
    d2 = ImageDraw.Draw(layer2)
    draw_rounded_rect(d2, [s(18), s(22), s(82), s(78)], s(8), PURPLE)
    img = Image.alpha_composite(img, layer2)

    # Card 3 (front/smallest) - Amber
    layer3 = new_canvas()
    d3 = ImageDraw.Draw(layer3)
    draw_rounded_rect(d3, [s(28), s(38), s(92), s(92)], s(8), AMBER)
    img = Image.alpha_composite(img, layer3)

    return img


def draw_admission():
    """Funnel shape representing selection/filtering process."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx = CANVAS // 2

    # Wide top trapezoid - Orange
    d.polygon([
        (s(10), s(15)),
        (s(90), s(15)),
        (s(70), s(45)),
        (s(30), s(45)),
    ], fill=ORANGE)

    # Middle section - Coral
    d.polygon([
        (s(30), s(45)),
        (s(70), s(45)),
        (s(58), s(68)),
        (s(42), s(68)),
    ], fill=CORAL)

    # Narrow bottom - Teal
    d.polygon([
        (s(42), s(68)),
        (s(58), s(68)),
        (s(54), s(85)),
        (s(46), s(85)),
    ], fill=TEAL)

    # Small circle at bottom (selected candidate)
    d.ellipse([s(42), s(85), s(58), s(97)], fill=TEAL)

    return img


def draw_scolarite():
    """Graduation cap (mortarboard) in geometric style."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = CANVAS // 2, CANVAS // 2

    # Cap top - large diamond (purple)
    d.polygon([
        (cx, s(15)),
        (s(90), s(42)),
        (cx, s(55)),
        (s(10), s(42)),
    ], fill=PURPLE)

    # Cap band - dark purple rectangle
    draw_rounded_rect(d, [s(22), s(48), s(78), s(62)], s(4), DARK_PURPLE)

    # Tassel string
    d.line([(s(68), s(42)), (s(75), s(65))], fill=AMBER, width=s(3))

    # Tassel ball - amber circle
    d.ellipse([s(70), s(65), s(82), s(77)], fill=AMBER)

    # Small book base
    draw_rounded_rect(d, [s(25), s(72), s(75), s(90)], s(4), (*PURPLE[:3], 160))

    return img


def draw_examen():
    """Score sheet with colored bars representing grades."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Paper background
    draw_rounded_rect(d, [s(15), s(8), s(85), s(92)], s(8), WHITE)

    # Header bar
    draw_rounded_rect(d, [s(22), s(16), s(78), s(28)], s(3), RED)

    # Grade bars (different lengths = different scores)
    draw_rounded_rect(d, [s(22), s(36), s(72), s(46)], s(3), DEEP_BLUE)
    draw_rounded_rect(d, [s(22), s(52), s(60), s(62)], s(3), SKY_BLUE)
    draw_rounded_rect(d, [s(22), s(68), s(68), s(78)], s(3), DEEP_BLUE)

    # Checkmark in corner
    layer = new_canvas()
    dl = ImageDraw.Draw(layer)
    dl.ellipse([s(62), s(72), s(82), s(90)], fill=(*TEAL[:3], 220))
    img = Image.alpha_composite(img, layer)

    return img


def draw_modelisation():
    """Clock face + grid representing timetabling."""
    img = new_canvas()

    # Clock circle - Coral
    layer1 = new_canvas()
    d1 = ImageDraw.Draw(layer1)
    d1.ellipse([s(5), s(5), s(65), s(65)], fill=CORAL)
    # Clock hands
    cx1, cy1 = s(35), s(35)
    d1.line([(cx1, cy1), (cx1, cy1 - s(18))], fill=WHITE, width=s(3))
    d1.line([(cx1, cy1), (cx1 + s(14), cy1)], fill=WHITE, width=s(3))
    # Center dot
    d1.ellipse([cx1 - s(3), cy1 - s(3), cx1 + s(3), cy1 + s(3)], fill=WHITE)
    img = Image.alpha_composite(img, layer1)

    # Grid overlay (bottom-right) - Deep Blue
    layer2 = new_canvas()
    d2 = ImageDraw.Draw(layer2)
    # 3x3 small grid squares
    for row in range(3):
        for col in range(3):
            x = s(48) + col * s(16)
            y = s(48) + row * s(16)
            color = DEEP_BLUE if (row + col) % 2 == 0 else (*AMBER[:3], 200)
            draw_rounded_rect(d2, [x, y, x + s(13), y + s(13)], s(2), color)
    img = Image.alpha_composite(img, layer2)

    return img


def draw_stage():
    """Briefcase with upward arrow representing internship growth."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Briefcase body - Teal
    draw_rounded_rect(d, [s(12), s(30), s(75), s(80)], s(8), TEAL)

    # Briefcase handle
    d.rounded_rectangle([s(32), s(18), s(55), s(35)], radius=s(6), fill=TRANSPARENT, outline=DARK_TEAL, width=s(4))

    # Briefcase clasp line
    d.line([(s(12), s(50)), (s(75), s(50))], fill=DARK_TEAL, width=s(3))

    # Arrow pointing up-right - Amber
    layer = new_canvas()
    dl = ImageDraw.Draw(layer)
    # Arrow shaft
    dl.line([(s(55), s(75)), (s(85), s(18))], fill=AMBER, width=s(5))
    # Arrow head
    dl.polygon([
        (s(85), s(8)),
        (s(92), s(25)),
        (s(78), s(22)),
    ], fill=AMBER)
    img = Image.alpha_composite(img, layer)

    return img


def draw_partenariat():
    """Two interlocking oval shapes representing partnership."""
    img = new_canvas()

    # Left shape - Teal
    layer1 = new_canvas()
    d1 = ImageDraw.Draw(layer1)
    d1.ellipse([s(5), s(18), s(58), s(82)], fill=TEAL)
    img = Image.alpha_composite(img, layer1)

    # Right shape - Purple (semi-transparent for blend)
    layer2 = new_canvas()
    d2 = ImageDraw.Draw(layer2)
    d2.ellipse([s(42), s(18), s(95), s(82)], fill=(*PURPLE[:3], 200))
    img = Image.alpha_composite(img, layer2)

    # Overlap accent - Dark Teal small circle
    layer3 = new_canvas()
    d3 = ImageDraw.Draw(layer3)
    d3.ellipse([s(38), s(35), s(62), s(65)], fill=(*DARK_TEAL[:3], 160))
    img = Image.alpha_composite(img, layer3)

    return img


def draw_isic_approvals():
    """Stamp circle with checkmark representing approval workflow."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = CANVAS // 2, CANVAS // 2

    # Outer ring - Teal
    d.ellipse([s(8), s(8), s(92), s(92)], fill=TEAL)
    # Inner ring - lighter
    d.ellipse([s(15), s(15), s(85), s(85)], fill=(*TEAL[:3], 100))
    # Inner circle - Amber accent
    d.ellipse([s(20), s(20), s(80), s(80)], fill=AMBER)
    # Center white circle
    d.ellipse([s(28), s(28), s(72), s(72)], fill=WHITE)

    # Checkmark - Teal
    d.line([
        (s(35), s(52)),
        (s(46), s(63)),
    ], fill=TEAL, width=s(5))
    d.line([
        (s(46), s(63)),
        (s(66), s(38)),
    ], fill=TEAL, width=s(5))

    return img


def draw_auth_cas():
    """Shield with keyhole representing authentication security."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx = CANVAS // 2

    # Shield shape - Deep Blue
    d.polygon([
        (cx, s(5)),         # top center
        (s(88), s(20)),     # top right
        (s(85), s(58)),     # mid right
        (cx, s(95)),        # bottom point
        (s(15), s(58)),     # mid left
        (s(12), s(20)),     # top left
    ], fill=DEEP_BLUE)

    # Inner shield - Navy
    d.polygon([
        (cx, s(14)),
        (s(78), s(26)),
        (s(76), s(55)),
        (cx, s(85)),
        (s(24), s(55)),
        (s(22), s(26)),
    ], fill=NAVY)

    # Keyhole circle
    d.ellipse([s(40), s(32), s(60), s(52)], fill=AMBER)
    # Keyhole slot
    draw_rounded_rect(d, [s(46), s(48), s(54), s(68)], s(2), AMBER)

    return img


def draw_openclaw_connector():
    """Chat bubble with lightning bolt for multi-channel AI assistant."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Main chat bubble - Orange
    draw_rounded_rect(d, [s(5), s(8), s(80), s(62)], s(12), ORANGE)
    # Bubble tail
    d.polygon([
        (s(18), s(58)),
        (s(8), s(78)),
        (s(35), s(58)),
    ], fill=ORANGE)

    # Lightning bolt - Amber
    d.polygon([
        (s(48), s(18)),
        (s(35), s(40)),
        (s(46), s(40)),
        (s(32), s(58)),
        (s(52), s(36)),
        (s(42), s(36)),
        (s(55), s(18)),
    ], fill=AMBER)

    # Small secondary bubble - Purple
    layer = new_canvas()
    dl = ImageDraw.Draw(layer)
    draw_rounded_rect(dl, [s(58), s(55), s(95), s(85)], s(8), (*PURPLE[:3], 220))
    # Small tail
    dl.polygon([
        (s(80), s(82)),
        (s(88), s(95)),
        (s(72), s(82)),
    ], fill=(*PURPLE[:3], 220))
    img = Image.alpha_composite(img, layer)

    return img


def draw_library_management():
    """Open book with colored pages."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx = CANVAS // 2

    # Left page - Teal
    d.polygon([
        (cx, s(20)),       # spine top
        (s(8), s(28)),     # top left
        (s(8), s(82)),     # bottom left
        (cx, s(88)),       # spine bottom
    ], fill=TEAL)

    # Right page - Dark Teal
    d.polygon([
        (cx, s(20)),       # spine top
        (s(92), s(28)),    # top right
        (s(92), s(82)),    # bottom right
        (cx, s(88)),       # spine bottom
    ], fill=DARK_TEAL)

    # Page lines (left)
    for i in range(4):
        y = s(38) + i * s(12)
        d.line([(s(18), y), (s(45), y)], fill=(*WHITE[:3], 140), width=s(2))

    # Page lines (right)
    for i in range(4):
        y = s(40) + i * s(12)
        d.line([(s(55), y), (s(82), y)], fill=(*WHITE[:3], 140), width=s(2))

    # Bookmark circle - Amber
    d.ellipse([s(40), s(8), s(60), s(28)], fill=AMBER)

    return img


def draw_todo_list():
    """Checklist with three colorful items."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    items = [
        (s(12), CORAL, True),
        (s(40), TEAL, True),
        (s(68), AMBER, False),
    ]

    for y_offset, color, checked in items:
        # Checkbox circle
        d.ellipse([s(12), y_offset, s(28), y_offset + s(16)], fill=color)
        if checked:
            # Checkmark
            d.line([
                (s(16), y_offset + s(8)),
                (s(19), y_offset + s(12)),
            ], fill=WHITE, width=s(2))
            d.line([
                (s(19), y_offset + s(12)),
                (s(25), y_offset + s(5)),
            ], fill=WHITE, width=s(2))

        # Line bar
        draw_rounded_rect(d, [s(35), y_offset + s(3), s(88), y_offset + s(13)], s(3), color)

    return img


def draw_isic_portal():
    """ISIC Portal: user dashboard with sidebar navigation."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Background - deep blue
    draw_rounded_rect(d, [0, 0, CANVAS, CANVAS], s(18), NAVY)

    # Sidebar stripe
    d.rectangle([0, 0, s(28), CANVAS], fill=(15, 50, 120, 255))

    # Sidebar dots (navigation items)
    for i, y_pos in enumerate([22, 36, 50, 64, 78]):
        dot_color = AMBER if i == 0 else (100, 140, 220, 255)
        d.ellipse([s(10), s(y_pos), s(18), s(y_pos + 6)], fill=dot_color)

    # User avatar circle
    d.ellipse([s(50), s(12), s(76), s(38)], fill=SKY_BLUE)
    # Head
    d.ellipse([s(58), s(16), s(68), s(26)], fill=WHITE)
    # Body
    d.arc([s(54), s(26), s(72), s(40)], start=0, end=180, fill=WHITE, width=s(2.5))

    # Dashboard cards
    draw_rounded_rect(d, [s(34), s(46), s(62), s(62)], s(4), SKY_BLUE)
    draw_rounded_rect(d, [s(66), s(46), s(94), s(62)], s(4), TEAL)
    draw_rounded_rect(d, [s(34), s(66), s(62), s(82)], s(4), AMBER)
    draw_rounded_rect(d, [s(66), s(66), s(94), s(82)], s(4), CORAL)

    # Card icons (small white shapes)
    # Calendar icon
    d.rectangle([s(44), s(50), s(52), s(58)], fill=WHITE)
    # Graduation cap
    d.polygon([s(76), s(50), s(84), s(54), s(76), s(58)], fill=WHITE)
    # Document
    d.rectangle([s(44), s(70), s(52), s(78)], fill=WHITE)
    # Chat bubble
    d.ellipse([s(76), s(70), s(84), s(78)], fill=WHITE)

    return img


def draw_isic_ged():
    """ISIC GED: file cabinet with categorized document folders."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Background - dark teal
    draw_rounded_rect(d, [0, 0, CANVAS, CANVAS], s(18), DARK_TEAL)

    # File cabinet body (large rounded rect)
    draw_rounded_rect(d, [s(16), s(14), s(84), s(86)], s(6), (0, 120, 155, 255))

    # Drawer sections (3 rows)
    for i, color in enumerate([TEAL, SKY_BLUE, AMBER]):
        y_start = s(18 + i * 22)
        y_end = s(36 + i * 22)
        draw_rounded_rect(d, [s(20), y_start, s(80), y_end], s(3), color)

        # Drawer handle
        d.rectangle([s(44), y_start + s(5), s(56), y_start + s(8)], fill=WHITE)

    # Document peeking out of top drawer
    d.polygon([
        (s(62), s(14)),
        (s(74), s(14)),
        (s(74), s(8)),
        (s(68), s(4)),
        (s(62), s(8)),
    ], fill=WHITE)

    # Small lines on document
    d.rectangle([s(64), s(6), s(72), s(7)], fill=DARK_TEAL)
    d.rectangle([s(64), s(9), s(70), s(10)], fill=DARK_TEAL)

    # Magnifying glass (search) overlay in bottom-right
    glass_cx, glass_cy = s(72), s(74)
    d.ellipse([glass_cx - s(8), glass_cy - s(8), glass_cx + s(8), glass_cy + s(8)],
              outline=WHITE, width=s(2.5))
    # Handle
    d.line([glass_cx + s(6), glass_cy + s(6), glass_cx + s(12), glass_cy + s(12)],
           fill=WHITE, width=s(3))

    return img


def draw_isic_rfid():
    """ISIC RFID: contactless card with signal waves for kiosk attendance."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # Background - navy blue
    draw_rounded_rect(d, [0, 0, CANVAS, CANVAS], s(18), NAVY)

    # RFID card body (tilted slightly) - white rounded rect
    card_color = (240, 248, 255, 255)
    draw_rounded_rect(d, [s(12), s(28), s(68), s(72)], s(8), card_color)

    # Card chip (gold square)
    chip_color = (218, 175, 58, 255)
    draw_rounded_rect(d, [s(22), s(40), s(38), s(54)], s(3), chip_color)
    # Chip lines
    d.line([s(26), s(44), s(34), s(44)], fill=NAVY, width=s(1))
    d.line([s(26), s(47), s(34), s(47)], fill=NAVY, width=s(1))
    d.line([s(26), s(50), s(34), s(50)], fill=NAVY, width=s(1))
    d.line([s(30), s(42), s(30), s(52)], fill=NAVY, width=s(1))

    # Card magnetic stripe
    d.rectangle([s(12), s(58), s(68), s(64)], fill=(180, 200, 220, 255))

    # Signal waves (3 arcs emanating from card) - Teal
    cx_wave, cy_wave = s(68), s(35)
    for i, (sz, alpha) in enumerate([(12, 255), (20, 200), (28, 140)]):
        wave_layer = new_canvas()
        wd = ImageDraw.Draw(wave_layer)
        wd.arc(
            [cx_wave - s(sz), cy_wave - s(sz), cx_wave + s(sz), cy_wave + s(sz)],
            start=-55, end=55,
            fill=(*TEAL[:3], alpha),
            width=s(3),
        )
        img = Image.alpha_composite(img, wave_layer)

    # Small user icon at bottom right (represents student)
    user_cx, user_cy = s(78), s(74)
    d.ellipse([user_cx - s(7), user_cy - s(7), user_cx + s(7), user_cy + s(7)],
              fill=SKY_BLUE)
    # Head
    d.ellipse([user_cx - s(3), user_cy - s(5), user_cx + s(3), user_cy - s(1)],
              fill=WHITE)
    # Body
    d.arc([user_cx - s(5), user_cy, user_cx + s(5), user_cy + s(7)],
          start=180, end=0, fill=WHITE, width=s(2))

    # Checkmark in bottom-left corner (success)
    check_cx, check_cy = s(22), s(82)
    d.ellipse([check_cx - s(8), check_cy - s(8), check_cx + s(8), check_cy + s(8)],
              fill=TEAL)
    d.line([check_cx - s(4), check_cy, check_cx - s(1), check_cy + s(3)],
           fill=WHITE, width=s(2.5))
    d.line([check_cx - s(1), check_cy + s(3), check_cx + s(5), check_cy - s(4)],
           fill=WHITE, width=s(2.5))

    return img


# === Main ===

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    custom_dir = os.path.join(base_dir, "custom-addons")

    modules = {
        "isic_base": draw_isic_base,
        "referentiel": draw_referentiel,
        "admission": draw_admission,
        "scolarite": draw_scolarite,
        "examen": draw_examen,
        "modelisation": draw_modelisation,
        "stage": draw_stage,
        "partenariat": draw_partenariat,
        "isic_approvals": draw_isic_approvals,
        "isic_approbation": draw_isic_approvals,
        "auth_cas": draw_auth_cas,
        "openclaw_connector": draw_openclaw_connector,
        "library_management": draw_library_management,
        "todo_list": draw_todo_list,
        "isic_portal": draw_isic_portal,
        "isic_ged": draw_isic_ged,
        "isic_rfid": draw_isic_rfid,
    }

    print(f"Generating {len(modules)} icons...")
    for module_name, draw_fn in modules.items():
        path = os.path.join(custom_dir, module_name, "static", "description", "icon.png")
        img = draw_fn()
        finalize(img, path)

    print(f"\nDone! {len(modules)} icons generated.")


if __name__ == "__main__":
    main()
