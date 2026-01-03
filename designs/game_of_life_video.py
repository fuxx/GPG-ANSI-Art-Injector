import re


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

RESET = "\033[0m"

# Video parameters
_GRID_W = 26
_GRID_H = 14
_STEP_COUNT = 64
_FRAMES_PER_STEP = 256

_ALIVE_CELL = "\u2588\u2588"
_DEAD_CELL = "  "

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

_NEIGHBOR_OFFSETS = [
    (dy, dx)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if (dy, dx) != (0, 0)
]

_AGE_PALETTE_256 = [
    196, 202, 208, 214, 220, 226, 190, 154, 118, 82, 46, 47, 51, 45, 39, 33, 27,
    21, 57, 93, 129, 165,
]


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


def _step_toroidal(grid: list[list[bool]]) -> list[list[bool]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return []

    def neighbor_count(y: int, x: int) -> int:
        return sum(grid[(y + dy) % height][(x + dx) % width] for dy, dx in _NEIGHBOR_OFFSETS)

    nxt = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            n = neighbor_count(y, x)
            nxt[y][x] = (n in (2, 3)) if grid[y][x] else (n == 3)
    return nxt


def _seed_grid(width: int, height: int) -> list[list[bool]]:
    grid = [[False] * width for _ in range(height)]

    pi_heptomino = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2))
    oy, ox = (height - 3) // 2, (width - 3) // 2
    for dy, dx in pi_heptomino:
        y, x = oy + dy, ox + dx
        if 0 <= y < height and 0 <= x < width:
            grid[y][x] = True

    return grid


def _cup(row, col):
    # Cursor position (1-indexed): similar to `tput cup row col`
    return f"\033[{row};{col}H"


def _color_256_fg(n):
    return f"\033[38;5;{n}m"


def _pick_color(age: int, t: int) -> str:
    if age <= 0:
        return ""
    # Age-based palette with a gentle time wobble to keep motion visible.
    idx = (min(age, len(_AGE_PALETTE_256)) - 1 + (t // 3)) % len(_AGE_PALETTE_256)
    return _color_256_fg(_AGE_PALETTE_256[idx])


def _render_grid_lines(ages, *, tick: int, reset: str) -> list[str]:
    lines: list[str] = []
    for row in ages:
        lines.append(
            "".join(
                (_pick_color(age, tick) + _ALIVE_CELL + reset) if age > 0 else _DEAD_CELL
                for age in row
            )
            + reset
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


def _advance_ages_and_grid(grid, ages):
    next_grid = _step_toroidal(grid)
    for y in range(len(next_grid)):
        for x in range(len(next_grid[0])):
            if next_grid[y][x]:
                ages[y][x] = min(ages[y][x] + 1, 24)
            else:
                # Fast fade-out for a subtle trailing effect.
                ages[y][x] = max(ages[y][x] - 2, 0)
    return next_grid


def get_payload(custom_text=""):
    # Video-ish effect: precompute frames and redraw in-place.
    frames = _STEP_COUNT * _FRAMES_PER_STEP
    reset = RESET

    grid = _seed_grid(_GRID_W, _GRID_H)
    ages = [[1 if cell else 0 for cell in row] for row in grid]

    out: list[str] = [
        "\n",
        "\033[?25l",  # civis: hide cursor
        "\033[2J",    # clear screen
    ]

    for t in range(frames):
        tick = t // _FRAMES_PER_STEP  # 0.._STEP_COUNT-1
        out.append(_cup(1, 1))
        out.append(reset + "\n")
        out.extend(
            _boxed_lines(
                _render_grid_lines(ages, tick=tick, reset=reset),
                pad=1,
                rounded=True,
                reset=reset,
            )
        )
        out.append(_render_loader_line(t, frames=frames, reset=reset))

        if t % _FRAMES_PER_STEP == 0:
            grid = _advance_ages_and_grid(grid, ages)

    out.append(
        (_color_256_fg(214) + "\n" + custom_text + reset + "\n") if custom_text else "\n"
    )
    out.append("\033[?25h")  # show cursor
    out.append(RESET)
    if not out[-1].endswith("\n"):
        out.append("\n")

    return "".join(out)
