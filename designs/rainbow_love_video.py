import math
import re


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

RESET = "\033[0m"

# Video parameters
_FLAG_W = 52
_FLAG_H = 18
_STEP_COUNT = 2048
_FRAMES_PER_STEP = 8

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Match Rich DEFAULT_STYLES / progress_bar characters.
_BAR_WIDTH = 49
_BAR_BACK = "\033[38;5;237m"          # grey23 -> 8-bit color(237)
_BAR_COMPLETE = "\033[38;2;249;38;114m"  # rgb(249,38,114)
_BAR_FINISHED = "\033[38;2;114;156;31m"  # rgb(114,156,31)
_SPINNER_STYLE = "\033[32m"           # green
_PERCENT_STYLE = "\033[35m"           # magenta

_BAR_CHAR = "━"
_HALF_BAR_RIGHT = "╸"
_HALF_BAR_LEFT = "╺"

_PRIDE_RGB = [
    (228, 3, 3),
    (255, 140, 0),
    (255, 237, 0),
    (0, 128, 38),
    (0, 77, 255),
    (117, 7, 135),
]

# Wave parameters (now applied vertically to create top/bottom ripples).
_WAVE_AMPLITUDE = 2    # max edge ripple (rows)
_WAVE_PERIOD = 480.0   # smaller = faster wave
# Spatial wavelength of the edge wave, in character columns.
# Larger = fewer (wider) waves across the width.
_WAVE_WAVELENGTH = 50
_SHIMMER_PERIOD = 640.0
_GRADIENT_SEGMENTS = 8
_BOTTOM_WAVE_PHASE = 0.0  # phase offset (radians) for the bottom edge

# Horizontal scrolling speed (columns per time unit; negative = leftward)
_SCROLL_SPEED = -0.08

# Internal stripe wave amplitude (makes every stripe boundary wavy).
# Wavelength/period are shared with the silhouette wave to keep phases aligned.
_STRIPE_WAVE_AMPLITUDE = 1.25  # rows; 0 disables internal waviness


def _strip_ansi(s: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", s)


def _boxed_lines(lines: list[str], *, pad: int = 1, rounded: bool = True, reset: str = "") -> list[str]:
    """Wrap `lines` in a Unicode box (visible width ignores ANSI escapes)."""
    if not lines:
        return []

    tl, tr, bl, br = ("╭", "╮", "╰", "╯") if rounded else ("┌", "┐", "└", "┘")
    h, v = "─", "│"
    vis_len = lambda s: len(_strip_ansi(s))  # noqa: E731

    visible_width = max(vis_len(line) for line in lines)
    inner_width = visible_width + 2 * pad

    out = [f"{reset}{tl}{h * inner_width}{tr}{reset}\n"]
    for line in lines:
        right_pad = " " * max(0, visible_width - vis_len(line))
        out.append(f"{reset}{v}{' ' * pad}{line}{right_pad}{' ' * pad}{v}{reset}\n")
    out.append(f"{reset}{bl}{h * inner_width}{br}{reset}\n")
    return out


def _cup(row, col):
    # Cursor position (1-indexed): similar to `tput cup row col`
    return f"\033[{row};{col}H"


def _color_256_fg(n: int) -> str:
    return f"\033[38;5;{n}m"


def _bg_truecolor(r: int, g: int, b: int) -> str:
    return f"\033[48;2;{r};{g};{b}m"


def _fg_truecolor(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _shade_rgb(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    r, g, b = rgb
    f = max(0.0, min(1.35, factor))
    return (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))


def _anim_time(t: int) -> float:
    """Convert frame index -> animation time units.

    The renderer outputs frames as fast as the terminal can handle (no sleep),
    so we intentionally scale time by `_FRAMES_PER_STEP` to keep motion from
    looking excessively fast and to make `_FRAMES_PER_STEP` meaningfully slow
    down the animation.
    """

    denom = max(1, int(_FRAMES_PER_STEP))
    return float(t) / float(denom)


def _wave_unit(x: int, t: int, *, phase_offset: float = 0.0) -> float:
    """Standing wave value in [-1, 1] shared by silhouette + stripes."""

    wavelength = max(1.0, float(_WAVE_WAVELENGTH))
    spatial = (2.0 * math.pi) * (x / wavelength) + float(phase_offset)
    time_phase = (2.0 * math.pi) * (_anim_time(t) / max(1.0, float(_WAVE_PERIOD)))
    return math.sin(spatial) * math.sin(time_phase)


def _stripe_displacement(x: int, t: int) -> float:
    """Vertical displacement (in rows) applied per column.

    This is what makes *all* internal stripe boundaries wave in place.
    """

    amp = float(_STRIPE_WAVE_AMPLITUDE)
    if amp <= 0.0:
        return 0.0

    return _wave_unit(x, t) * amp


def _stripe_index_at(yf: float) -> int:
    n = len(_PRIDE_RGB)
    if n <= 1:
        return 0
    # Clamp into the flag vertical extent, then map to stripe index.
    yf = max(0.0, min(float(_FLAG_H) - 1e-6, yf))
    idx = int((yf / float(_FLAG_H)) * n)
    return max(0, min(n - 1, idx))


def _edge_wave(x: int, t: int, *, phase_offset: float = 0.0) -> float:
    # Signed displacement (rows) for the silhouette edge.
    # This keeps motion consistent with the internal stripe waviness.
    return _wave_unit(x, t, phase_offset=phase_offset) * float(_WAVE_AMPLITUDE)


def _render_flag_row(
    *,
    y: int,
    t: int,
    scroll_offset: float,
    top_offsets: list[float],
    bottom_offsets: list[float],
    reset: str,
) -> str:
    """Render one row of the flag.

    - Keeps the wavy *silhouette* (top/bottom mask).
    - Adds a per-column vertical displacement so every internal stripe boundary is wavy.
    - Applies horizontal scrolling via scroll_offset.
    """

    width = _FLAG_W
    height = _FLAG_H
    if width <= 0 or height <= 0:
        return ""

    seg_count = min(_GRADIENT_SEGMENTS, width)
    base = _intensity(y, t)

    # Precompute per-stripe color styles per segment to reduce ANSI payload.
    stripe_seg_bg: list[list[str]] = []
    stripe_seg_fg: list[list[str]] = []

    for stripe_rgb in _PRIDE_RGB:
        seg_bg: list[str] = []
        seg_fg: list[str] = []
        for seg in range(seg_count):
            x01 = seg / (seg_count - 1) if seg_count > 1 else 0.0
            f = base * _gradient_intensity(x01, y, t)
            r, g, b = _shade_rgb(stripe_rgb, f)
            seg_bg.append(_bg_truecolor(r, g, b))
            seg_fg.append(_fg_truecolor(r, g, b))
        stripe_seg_bg.append(seg_bg)
        stripe_seg_fg.append(seg_fg)

    # Map x -> segment index
    seg_for_x: list[int] = []
    for seg in range(seg_count):
        seg_w = (width // seg_count) + (1 if seg < (width % seg_count) else 0)
        seg_for_x.extend([seg] * seg_w)
    if len(seg_for_x) > width:
        seg_for_x = seg_for_x[:width]
    elif len(seg_for_x) < width:
        seg_for_x.extend([seg_count - 1] * (width - len(seg_for_x)))

    parts: list[str] = []
    last_style: str | None = None

    for x in range(width):
        # Apply horizontal scroll with wrapping for seamless motion
        x_scrolled = (x + scroll_offset) % width
        x_sample = int(x_scrolled) % width

        # No clamping here: allowing edges to go slightly outside the flag
        # avoids flattening artifacts and looks more cloth-like.
        #
        # NOTE: Internal stripes use a texture displacement (sampling y+disp),
        # which makes the pattern appear to move opposite the sampling offset.
        # The silhouette is a geometric mask, so to match perceived motion we
        # flip the displacement sign for the edges.
        top_edge = -float(top_offsets[x_sample])
        bottom_edge = float(height) - float(bottom_offsets[x_sample])
        if bottom_edge < top_edge:
            top_edge, bottom_edge = bottom_edge, top_edge

        # Row cell spans [y, y+1). Compute overlap with [top_edge, bottom_edge).
        lo = max(float(y), top_edge)
        hi = min(float(y + 1), bottom_edge)
        inside_frac = max(0.0, hi - lo)

        seg_idx = seg_for_x[x_sample]
        disp = _stripe_displacement(x_sample, t)

        if inside_frac <= 0.125:
            style = ""
            ch = " "
        elif inside_frac >= 0.875:
            # Decide stripe at top/bottom of the cell to render crisp wavy boundaries.
            top_i = _stripe_index_at((y + 0.25) + disp)
            bot_i = _stripe_index_at((y + 0.75) + disp)
            if top_i == bot_i:
                style = stripe_seg_bg[top_i][seg_idx]
                ch = " "
            else:
                # Upper stripe in FG, lower stripe in BG.
                style = stripe_seg_fg[top_i][seg_idx] + stripe_seg_bg[bot_i][seg_idx]
                ch = "▀"
        else:
            # Near silhouette edges, keep the existing half-block approach.
            i = _stripe_index_at((y + 0.5) + disp)
            style = stripe_seg_fg[i][seg_idx]
            mid = (lo + hi) * 0.5
            ch = "▀" if mid < (y + 0.5) else "▄"

        if style != last_style:
            if last_style:
                parts.append(reset)
            if style:
                parts.append(style)
            last_style = style

        parts.append(ch)

    if last_style:
        parts.append(reset)

    return "".join(parts)


def _intensity(y: int, t: int) -> float:
    # Subtle shimmer (brightness) that doesn't change the stripe hues.
    phase = ((2.0 * math.pi) * (_anim_time(t) / _SHIMMER_PERIOD)) + (y * 0.22)
    return 0.78 + 0.22 * ((math.sin(phase) + 1.0) * 0.5)


def _gradient_intensity(x01: float, y: int, t: int) -> float:
    # Moving highlight across the stripe, anchored to the same shimmer period.
    phase = ((2.0 * math.pi) * (_anim_time(t) / _SHIMMER_PERIOD)) + (y * 0.18) + (x01 * 4.0)
    return 0.82 + 0.28 * ((math.sin(phase) + 1.0) * 0.5)


def _render_stripe_fill(width: int, *, base_rgb: tuple[int, int, int], y: int, t: int, reset: str) -> str:
    if width <= 0:
        return ""

    seg_count = min(_GRADIENT_SEGMENTS, width)
    base = _intensity(y, t)
    parts: list[str] = []

    # Render in coarse segments to keep payload size reasonable.
    for seg in range(seg_count):
        seg_w = (width // seg_count) + (1 if seg < (width % seg_count) else 0)
        if seg_w <= 0:
            continue

        x01 = seg / (seg_count - 1) if seg_count > 1 else 0.0
        f = base * _gradient_intensity(x01, y, t)
        r, g, b = _shade_rgb(base_rgb, f)
        parts.append(_bg_truecolor(r, g, b) + (" " * seg_w))

    return "".join(parts) + reset


def _render_flag_lines(*, t: int, reset: str) -> list[str]:
    lines: list[str] = []

    # Horizontal scroll offset (wraps around flag width)
    scroll_offset = _anim_time(t) * _SCROLL_SPEED

    # Precompute edge displacements per-column so all rows share the same silhouette.
    top_offsets = [_edge_wave(x, t) for x in range(_FLAG_W)]
    bottom_offsets = [_edge_wave(x, t, phase_offset=_BOTTOM_WAVE_PHASE) for x in range(_FLAG_W)]

    for y in range(_FLAG_H):
        lines.append(
            _render_flag_row(
                y=y,
                t=t,
                scroll_offset=scroll_offset,
                top_offsets=top_offsets,
                bottom_offsets=bottom_offsets,
                reset=reset,
            )
        )
    return lines


def _render_loader_line(t: int, *, frames: int, reset: str) -> str:
    spinner = _SPINNER_FRAMES[t % len(_SPINNER_FRAMES)]

    completed = t + 1
    total = frames
    is_finished = completed >= total
    complete_style = _BAR_FINISHED if is_finished else _BAR_COMPLETE

    complete_halves = (_BAR_WIDTH * 2 * completed) // total if total else _BAR_WIDTH * 2
    complete_halves = min(_BAR_WIDTH * 2, max(0, complete_halves))
    bar_count, half_bar_count = divmod(complete_halves, 2)
    remaining_bars = _BAR_WIDTH - bar_count - half_bar_count

    bar_parts: list[str] = []
    if bar_count:
        bar_parts.append(complete_style + (_BAR_CHAR * bar_count) + reset)
    if half_bar_count:
        bar_parts.append(complete_style + _HALF_BAR_RIGHT + reset)
    if remaining_bars:
        if not half_bar_count and bar_count:
            bar_parts.append(_BAR_BACK + _HALF_BAR_LEFT + reset)
            remaining_bars -= 1
        if remaining_bars:
            bar_parts.append(_BAR_BACK + (_BAR_CHAR * remaining_bars) + reset)

    percent = min(100, max(0, (completed * 100) // total)) if total else 100
    return (
        _SPINNER_STYLE
        + spinner
        + reset
        + " "
        + "".join(bar_parts)
        + " "
        + _PERCENT_STYLE
        + f"{percent:>3d}%"
        + reset
        + "\n"
    )


def get_payload(custom_text=""):
    # Video-ish effect: precompute frames and redraw in-place.
    frames = _STEP_COUNT * _FRAMES_PER_STEP
    reset = RESET

    out: list[str] = [
        "\n",
        "\033[?25l",  # civis: hide cursor
        "\033[2J",    # clear screen
    ]

    for t in range(frames):
        out.append(_cup(1, 1))
        out.append(reset + "\n")
        out.extend(
            _boxed_lines(
                _render_flag_lines(t=t, reset=reset),
                pad=1,
                rounded=True,
                reset=reset,
            )
        )
        out.append(_render_loader_line(t, frames=frames, reset=reset))

    out.append(
        (_color_256_fg(255) + "\n" + custom_text + reset + "\n") if custom_text else "\n"
    )
    out.append("\033[?25h")  # show cursor
    out.append(RESET)
    if not out[-1].endswith("\n"):
        out.append("\n")

    return "".join(out)

print(get_payload())