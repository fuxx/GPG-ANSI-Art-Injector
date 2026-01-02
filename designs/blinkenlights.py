def get_payload(custom_text=""):
    """
    Returns the 'Haus des Lehrers' Blinkenlights ANSI art.
    Refined for pixel-perfect alignment and strict 34-char width.
    """
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

    res = "\033[0m"

    def line(content):
        return f"{content}{res}\n"

    # --- Geometry Helpers ---
    # Window: 2 chars color + 1 char pillar (background)
    # Total width per window unit = 3 chars
    def win(state):
        c = w_off
        if state == 1: c = w_lit
        if state == 2: c = w_dim
        return f"{c}  {c_void} "

    # Floor: 1 space + │ + 30 chars (windows) + │ = 34 chars total width
    def floor(states):
        row = "".join([win(s) for s in states])
        return line(f" {c_frame}│{c_void}{row}{c_frame}│")

    # Spandrel: Separator lines between floors
    # Matches the 30-char interior exactly
    div = line(f" {c_frame}├{'─' * 30}┤")

    # --- The Art ---
    lines = []

    # 1. Roof (Centered Antennas)
    # Interior is 30 chars. Center is 15.
    # Antenna '││  ││' is 6 chars wide. Padding = 12.
    lines.append(line(f" {' ' * 3}{c_frame}┌──────┐{' ' * 10}{c_frame}┌──────┐"))
    lines.append(line(f" {c_frame}┌──┴──────┴──────────┴──────┴──┐"))

    # 2. The Matrix (10 x 12 grid)
    # 0=Off, 1=Yellow, 2=Orange
    matrix = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Padding Top
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],  # C Top
        [0, 0, 1, 1, 2, 0, 1, 1, 0, 0],  # C Top-Curve
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # C Left
        [0, 1, 2, 0, 0, 0, 0, 1, 0, 0],  # C Left + Noise
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0],  # C Left
        [0, 1, 1, 0, 0, 0, 0, 0, 2, 0],  # C Left + Noise
        [0, 1, 2, 0, 0, 0, 0, 0, 0, 0],  # C Left
        [0, 0, 1, 1, 2, 0, 1, 1, 0, 0],  # C Bot-Curve
        [0, 0, 0, 1, 1, 1, 1, 0, 0, 0],  # C Bot
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Padding Bot
        [2, 0, 1, 0, 0, 0, 0, 1, 0, 2],  # Ground Noise
    ]

    for row_data in matrix:
        lines.append(floor(row_data))
        lines.append(div)

    # 3. The Lobby / Label
    # Label text: "HAUS DES LEHRERS" (16 chars)
    # Styled: "[ HAUS DES LEHRERS ]" (20 chars)
    # Interior: 30 chars. Padding needed: 5 left, 5 right.

    pad = c_void + (" " * 5)
    label_text = " HAUS DES LEHRERS "  # 18 chars

    # Construction: Border | Pad | YellowBox | Pad | Border
    lines.append(line(f" {c_frame}│{pad}{l_bg}{l_fg}[{label_text}]{c_void}{pad}{c_frame}│"))
    lines.append(line(f" {c_frame}└{'─' * 30}┘"))

    # Assemble
    art = "\n" + "".join(lines)

    if custom_text:
        art += f"{custom_text}\n"
    else:
        art += "\n"

    return art