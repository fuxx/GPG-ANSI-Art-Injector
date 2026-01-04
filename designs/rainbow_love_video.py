import math


# ANSI / terminal control sequences
ESC = "\x1b"
CSI = ESC + "["

RESET_ALL = CSI + "0m"
RESET_FG = CSI + "39m"  # reset foreground only
RESET_BG = CSI + "49m"  # reset background only

REVERSE_VIDEO = CSI + "7m"

CURSOR_HOME = CSI + "H"
CLEAR_SCREEN = CSI + "2J"
HIDE_CURSOR = CSI + "?25l"
SHOW_CURSOR = CSI + "?25h"
ENTER_ALTERNATE_SCREEN = CSI + "?1049h"  # smcup (save main screen)
LEAVE_ALTERNATE_SCREEN = CSI + "?1049l"  # rmcup (restore main screen)

CUP = CSI + "{row};{col}H"
BG_RGB = CSI + "48;2;{r};{g};{b}m"
FG_RGB = CSI + "38;2;{r};{g};{b}m"

# 1/8-height block elements for smoother partial coverage.
_V_BLOCKS_1_8 = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]


def _block_level_1_8(frac: float) -> int:
    # Map [0,1] -> {0..8}, rounded.
    frac = _clamp(frac, 0.0, 1.0)
    return int(frac * 8.0 + 0.5)


_PRIDE_FLAG_6 = [
    (228, 3, 3),     # Red   (#E40303)
    (255, 140, 0),   # Orange(#FF8C00)
    (255, 237, 0),   # Yellow(#FFED00)
    (0, 128, 38),    # Green (#008026)
    (0, 77, 255),    # Blue  (#004DFF)
    (117, 7, 135),   # Violet(#750787)
]


def _palette(n: int) -> list[tuple[int, int, int]]:
    n = max(1, int(n))
    # Hardcoded Pride flag colors (no HSV generation).
    # If n != 6, repeat/truncate deterministically.
    base = _PRIDE_FLAG_6
    if n <= len(base):
        return base[:n]
    return [base[i % len(base)] for i in range(n)]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _norm3(x: float, y: float, z: float) -> tuple[float, float, float]:
    m = math.sqrt((x * x) + (y * y) + (z * z))
    if m <= 1e-9:
        return (0.0, 0.0, 1.0)
    return (x / m, y / m, z / m)


def _shade(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    r, g, b = rgb
    # Shading factor: <1 darkens, >1 brightens.
    # Keep highlights close to the original color to avoid blowouts.
    f = max(0.0, min(1.2, factor))
    return (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))


def _render_flag_lines(*, t: int, width: int, height: int, reset: str) -> list[str]:
    stripes = 6
    colors = _palette(stripes)

    # A simple “physics-respecting” cloth model:
    # - anchored at the left edge (flagpole) -> wave amplitude grows with x
    # - traveling wave downwind with a secondary harmonic
    # - slight y-dependent phase to simulate twist / coupling
    # - lighting computed from heightfield normals (derivatives)

    # Dimensions are used to scale the effect (no hard-coded flag size).
    edge_amp = max(1.0, height * 0.18)
    stripe_amp = max(0.0, height * 0.12)
    depth_amp = 1.0

    wavelength = max(10.0, width * 0.85)
    omega = 0.22  # time speed
    ky = (2.0 * math.pi) / max(6.0, float(height) * 1.3)

    time = float(t)

    def amp_ramp(x: float) -> float:
        # 0 at the pole, 1 at the free edge (slightly eased).
        if width <= 1:
            return 1.0
        u = _clamp(x / float(width - 1), 0.0, 1.0)
        return u ** 1.6

    def gust(tt: float) -> float:
        # Slow modulation so the flag doesn't feel perfectly periodic.
        return 0.75 + 0.25 * math.sin(tt * 0.035)

    def base_wave(x: float, tt: float, phase: float = 0.0) -> float:
        # A traveling wave with a secondary harmonic. Normalized to [-1, 1].
        kx = (2.0 * math.pi) / wavelength
        w0 = math.sin((kx * x) - (omega * tt) + phase)
        w1 = 0.45 * math.sin((2.0 * kx * x) - (1.85 * omega * tt) + phase + 1.2)
        return _clamp((w0 + w1) / 1.45, -1.0, 1.0)


    def heightfield(x: float, y: float, tt: float) -> float:
        # Out-of-plane displacement (used only for shading).
        a = amp_ramp(x) * gust(tt)
        phase_y = y * ky
        w = base_wave(x, tt, phase=phase_y)
        return depth_amp * a * w

    # Precompute silhouette edges and a per-column stripe displacement.
    top_edge: list[float] = []
    bot_edge: list[float] = []
    disp: list[float] = []
    for x in range(width):
        xf = float(x)
        a = amp_ramp(xf) * gust(time)
        w_top = base_wave(xf, time, phase=0.0)
        w_bot = base_wave(xf, time, phase=0.35)

        # Keep silhouette strictly within [0, height]. Note: the stripe pattern
        # is sampled with a +disp_y offset (see `disp` below), which moves stripe
        # boundaries by -disp_y in screen-space. To keep the *top* stripe's
        # perceived motion consistent with the rest, the top edge must respond
        # with the opposite sign vs. the sampling displacement.
        top_edge.append(edge_amp * a * (0.5 - 0.5 * w_top))
        bot_edge.append(float(height) - (edge_amp * a * (0.5 + 0.5 * w_bot)))

        # Stripe sampling displacement aligned to the same wave as the silhouette.
        disp.append(stripe_amp * a * w_top)

    def stripe_at(yf: float) -> int:
        yf = max(0.0, min(float(height) - 1e-6, yf))
        return int((yf / float(height)) * stripes)

    def stripe_boundary_y(idx: int) -> float:
        # Boundary between stripe idx-1 and idx in flag-space coordinates.
        return (float(idx) / float(stripes)) * float(height)

    # Lighting from estimated surface normals (height derivatives).
    light_dir = _norm3(-0.65, -0.25, 1.0)  # from upper-left/front

    def light_at(x: int, y: int) -> float:
        h = heightfield(float(x), float(y), time)
        hx = heightfield(float(min(width - 1, x + 1)), float(y), time)
        hy = heightfield(float(x), float(min(height - 1, y + 1)), time)
        dhdx = hx - h
        dhdy = hy - h

        # Heightfield normal ~ (-dhdx, -dhdy, 1)
        nx, ny, nz = _norm3(-dhdx, -dhdy, 1.0)
        ndotl = (nx * light_dir[0]) + (ny * light_dir[1]) + (nz * light_dir[2])
        ndotl = _clamp(ndotl, -1.0, 1.0)

        # Stronger, symmetric shading: darker in folds, brighter on peaks.
        lit01 = 0.5 + 0.5 * ndotl  # [-1, 1] -> [0, 1]

        # Contrast curve around mid-gray.
        contrast = 3.40
        lit01 = _clamp((lit01 - 0.5) * contrast + 0.5, 0.0, 1.0)

        # Asymmetric mapping:
        # - allow strong darkening in shadows
        # - keep highlights only slightly brighter than the base color
        delta = (lit01 - 0.5) * 2.0  # [-1, 1]
        shadow_scale = 2.60
        highlight_scale = 0.08
        if delta >= 0.0:
            brightness = 1.0 + (highlight_scale * delta)
        else:
            brightness = 1.0 + (shadow_scale * delta)

        # Extra fold emphasis: higher slope => darker.
        slope = math.sqrt((dhdx * dhdx) + (dhdy * dhdy))
        brightness -= 0.72 * _clamp(slope * 3.6, 0.0, 1.0)

        # Tiny sparkle, clamped within range.
        sparkle = 0.015 * (0.5 + 0.5 * math.sin(0.15 * time + (x * 0.35) + (y * 0.22)))
        return _clamp(brightness + sparkle, 0.0, 1.12)

    lines: list[str] = []
    for y in range(height):
        parts: list[str] = []
        last_style: str | None = None
        for x in range(width):
            te = top_edge[x]
            be = bot_edge[x]
            if be < te:
                te, be = be, te

            cell_lo = float(y)
            cell_hi = float(y + 1)
            lo = max(cell_lo, te)
            hi = min(cell_hi, be)
            inside = max(0.0, hi - lo)

            if inside <= 0.0:
                style = ""
                ch = " "
            else:
                disp_y = disp[x]

                # Full coverage: we can spend the whole cell on smoothing stripe boundaries.
                if inside >= 0.999:
                    y_top = float(y) + 1e-6 + disp_y
                    y_bot = float(y + 1) - 1e-6 + disp_y
                    top_i = stripe_at(y_top)
                    bot_i = stripe_at(y_bot)

                    if top_i == bot_i:
                        rgb = _shade(colors[top_i], light_at(x, y))
                        r, g, b = rgb
                        style = BG_RGB.format(r=r, g=g, b=b)
                        ch = " "
                    else:
                        # One boundary crosses this cell. Blend with BG(top) and FG(bottom).
                        # Compute boundary position in *cell* coordinates.
                        boundary = stripe_boundary_y(max(top_i, bot_i)) - disp_y
                        boundary_in_cell = _clamp(boundary - float(y), 0.0, 1.0)
                        bottom_frac = 1.0 - boundary_in_cell

                        rgb_top = _shade(colors[top_i], light_at(x, y))
                        rgb_bot = _shade(colors[bot_i], light_at(x, y))
                        level = _block_level_1_8(bottom_frac)

                        # Ensure FG blocks draw over the chosen background.
                        tr, tg, tb = rgb_top
                        br, bg, bb = rgb_bot
                        style = BG_RGB.format(r=tr, g=tg, b=tb) + FG_RGB.format(r=br, g=bg, b=bb)
                        ch = _V_BLOCKS_1_8[level]

                else:
                    # Partial coverage (silhouette edge): prioritize the outer contour.
                    idx = stripe_at((y + 0.5) + disp_y)
                    rgb = _shade(colors[idx], light_at(x, y))

                    # Partial coverage -> use 1/8 blocks.
                    # If the cut is at the TOP (top edge passes through this cell),
                    # the filled portion is at the bottom.
                    # If the cut is at the BOTTOM, the filled portion is at the top.
                    fills_bottom = lo > cell_lo + 1e-9 and hi >= cell_hi - 1e-9
                    fills_top = hi < cell_hi - 1e-9 and lo <= cell_lo + 1e-9

                    if fills_bottom:
                        # Bottom-fill using foreground blocks over default background.
                        level = _block_level_1_8(inside)
                        r, g, b = rgb
                        style = RESET_BG + FG_RGB.format(r=r, g=g, b=b)
                        ch = _V_BLOCKS_1_8[level]
                    elif fills_top:
                        # Top-fill: paint the stripe as background, then draw the *empty*
                        # bottom portion using reverse-video (theme-dependent).
                        empty_level = _block_level_1_8(1.0 - inside)
                        if empty_level <= 0:
                            r, g, b = rgb
                            style = BG_RGB.format(r=r, g=g, b=b)
                            ch = " "
                        elif empty_level >= 8:
                            style = ""
                            ch = " "
                        else:
                            # Reverse-video swaps FG/BG. By setting FG=stripe first,
                            # the background becomes the stripe color and the block glyph
                            # itself renders in the terminal's default background.
                            r, g, b = rgb
                            style = FG_RGB.format(r=r, g=g, b=b) + REVERSE_VIDEO
                            ch = _V_BLOCKS_1_8[empty_level]
                    else:
                        # Very thin band through the middle (rare): fall back to half blocks.
                        mid = (lo + hi) * 0.5
                        r, g, b = rgb
                        style = RESET_BG + FG_RGB.format(r=r, g=g, b=b)
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

        lines.append("".join(parts))

    return lines


def get_payload(custom_text: str = "") -> str:
    """Return an ANSI animation payload string.

    The string starts with a leading newline and ends with a newline.
    If custom_text is provided, it is appended after the animation.
    """

    width = 52
    height = 16
    base_frames = 100
    frame_repeat = 50

    out: list[str] = [
        ENTER_ALTERNATE_SCREEN,
        HIDE_CURSOR,
        CLEAR_SCREEN,
        CURSOR_HOME,
    ]

    for t in range(base_frames):
        frame = [line + "\n" for line in _render_flag_lines(t=t, width=width, height=height, reset=RESET_ALL)]
        for _ in range(frame_repeat):
            out.append(CUP.format(row=1, col=1))
            out.append(RESET_ALL + "\n")
            out.extend(frame)

            if custom_text:
                out.append("\n" + custom_text + RESET_ALL + "\n")
            else:
                out.append("\n")

    out.append(SHOW_CURSOR)
    out.append(RESET_ALL)
    out.append(LEAVE_ALTERNATE_SCREEN)
    out.append(SHOW_CURSOR)

    return "".join(out)
