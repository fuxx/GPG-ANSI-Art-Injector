import re


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

RESET = "\033[0m"

# Animation parameters
# - The message scrolls exactly once (no looping).
# - Slowdown is achieved by holding each scroll position for multiple frames.
_SCROLL_HOLD_FRAMES = 100

# Window grid inside the building (matches `blinkenlights.py`)
_GRID_W = 10
_GRID_H = 12

# Where the 7px-tall text sits within the 12-row grid
_TEXT_TOP = 2
_TEXT_H = 7


_FONT_5X7: dict[str, list[str]] = {
    "A": [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "B": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10001",
        "10001",
        "11110",
    ],
    "C": [
        "01111",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "01111",
    ],
    "E": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
    "H": [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "L": [
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ],
    "M": [
        "10001",
        "11011",
        "10101",
        "10001",
        "10001",
        "10001",
        "10001",
    ],
    "O": [
        "01110",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    "P": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    "R": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    "S": [
        "01111",
        "10000",
        "10000",
        "01110",
        "00001",
        "00001",
        "11110",
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "U": [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    " ": [
        "000",
        "000",
        "000",
        "000",
        "000",
        "000",
        "000",
    ],
}


def _strip_ansi(s: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", s)


def _cup(row: int, col: int) -> str:
    # Cursor position (1-indexed)
    return f"\033[{row};{col}H"


def _columns_for_char(ch: str) -> list[list[int]]:
    rows = _FONT_5X7.get(ch)
    if rows is None:
        rows = _FONT_5X7[" "]

    width = len(rows[0]) if rows else 0
    cols: list[list[int]] = []
    for x in range(width):
        col: list[int] = []
        for y in range(_TEXT_H):
            col.append(1 if rows[y][x] == "1" else 0)
        cols.append(col)

    # Inter-character spacing (1 blank col)
    cols.append([0] * _TEXT_H)
    return cols


def _message_columns(msg: str) -> list[list[int]]:
    msg = (msg or "").upper()
    cols: list[list[int]] = []
    for ch in msg:
        cols.extend(_columns_for_char(ch))
    # Some trailing gap so the scroll breathes between loops
    cols.extend([[0] * _TEXT_H for _ in range(_GRID_W)])
    return cols


def _twinkle_state(t: int, x: int, y: int) -> int:
    """Deterministic 'random-ish' dim windows."""
    v = (t * 17 + x * 29 + y * 43) & 0xFFFFFFFF
    # Very sparse dim pixels
    return 2 if (v % 97) == 0 else 0


def _build_matrix(
    t: int,
    *,
    msg_cols: list[list[int]],
    scroll_t: int | None = None,
) -> list[list[int]]:
    # 0=Off, 1=Yellow (text), 2=Orange (dim)
    matrix: list[list[int]] = [[0 for _ in range(_GRID_W)] for _ in range(_GRID_H)]

    # Ambient twinkle everywhere
    for y in range(_GRID_H):
        for x in range(_GRID_W):
            matrix[y][x] = _twinkle_state(t, x, y)

    # Keep the very top/bottom padding mostly dark
    for x in range(_GRID_W):
        matrix[0][x] = 0
        matrix[_GRID_H - 2][x] = 0

    # Add a little ground noise like the static version
    ground = _GRID_H - 1
    for x in range(_GRID_W):
        matrix[ground][x] = 2 if ((t + x * 7) % 31) == 0 else 0

    # Scroll the message from right -> left across the 10-column display.
    # This is intentionally non-looping: shift advances linearly and the caller
    # controls the total number of frames.
    if scroll_t is None:
        scroll_t = t
    shift = scroll_t - _GRID_W

    for dx in range(_GRID_W):
        sx = shift + dx
        if 0 <= sx < len(msg_cols):
            col = msg_cols[sx]
            for dy in range(_TEXT_H):
                if col[dy]:
                    matrix[_TEXT_TOP + dy][dx] = 1

    return matrix


def _render_building(matrix: list[list[int]], *, custom_text: str = "") -> str:
    """Render the building with the given 10x12 window state matrix."""
    # --- Color Palette (Night Mode) ---
    c_frame = "\033[38;5;238m"  # Dark Grey (Structure)
    c_void = "\033[48;5;234m"  # Dark Grey (Background)

    # Window States
    w_off = "\033[48;5;232m"  # Black (Off)
    w_dim = "\033[48;5;214m"  # Orange (Dim)
    w_lit = "\033[48;5;226m"  # Yellow (Bright)

    # Label Colors
    l_bg = "\033[48;5;226m"  # Yellow BG
    l_fg = "\033[38;5;16m"  # Black Text

    res = RESET

    def line(content: str) -> str:
        return f"{content}{res}\n"

    # Window: 2 chars color + 1 char pillar (background) => 3 chars per window
    def win(state: int) -> str:
        c = w_off
        if state == 1:
            c = w_lit
        elif state == 2:
            c = w_dim
        return f"{c}  {c_void} "

    # Floor: 1 space + │ + 30 chars (windows) + │ = 34 chars total width
    def floor(states: list[int]) -> str:
        row = "".join([win(s) for s in states])
        return line(f" {c_frame}│{c_void}{row}{c_frame}│")

    # Separator lines between floors
    div = line(f" {c_frame}├{'─' * 30}┤")

    # --- Assemble ---
    out: list[str] = []

    # Roof (static)
    out.append(line(f" {' ' * 3}{c_frame}┌──────┐{' ' * 10}{c_frame}┌──────┐"))
    out.append(line(f" {c_frame}┌──┴──────┴──────────┴──────┴──┐"))

    for row_data in matrix:
        out.append(floor(row_data))
        out.append(div)

    # Lobby label (kept as in the original)
    pad = c_void + (" " * 5)
    label_text = " HAUS DES LEHRERS "  # 18 chars
    out.append(line(f" {c_frame}│{pad}{l_bg}{l_fg}[{label_text}]{c_void}{pad}{c_frame}│"))
    out.append(line(f" {c_frame}└{'─' * 30}┘"))

    art = "\n" + "".join(out)

    if custom_text:
        art += f"{custom_text}\n"
    else:
        art += "\n"

    return art


def get_payload(custom_text: str = "") -> str:
    """Animated Blinkenlights: scrolls 'CHAOS COMPUTER CLUB' once in yellow windows."""
    msg_cols = _message_columns("CHAOS COMPUTER CLUB")

    # Total scroll steps to go from fully-offscreen-right to fully-offscreen-left.
    # shift = scroll_t - _GRID_W
    # scroll_t=0  => shift=-_GRID_W (blank)
    # scroll_t=N  => shift=len(msg_cols) (blank)
    total_scroll_steps = len(msg_cols) + _GRID_W + 1
    total_frames = total_scroll_steps * _SCROLL_HOLD_FRAMES

    out: list[str] = [
        "\n",
        "\033[?25l",  # hide cursor
        "\033[2J",  # clear screen
    ]

    for frame in range(total_frames):
        scroll_step = frame // _SCROLL_HOLD_FRAMES
        matrix = _build_matrix(frame, msg_cols=msg_cols, scroll_t=scroll_step)
        out.append(_cup(1, 1))
        out.append(_render_building(matrix))

    # Final note below the art (once)
    if custom_text:
        out.append(f"{custom_text}{RESET}\n")
    else:
        out.append("\n")

    out.append("\033[?25h")  # show cursor
    out.append(RESET)
    if not out[-1].endswith("\n"):
        out.append("\n")

    return "".join(out)
