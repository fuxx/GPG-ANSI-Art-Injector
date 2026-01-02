def get_payload(custom_text=""):
    """
    Returns a 60-character wide Hacker Terminal HUD.
    Uses box-drawing characters for precision and a CCC-themed layout.
    """
    # 256-Color Palette (Foregrounds)
    cyan = "\033[38;5;51m"
    pink = "\033[38;5;201m"
    green = "\033[38;5;46m"
    gray = "\033[38;5;244m"
    res = "\033[0m"

    # Helper for consistent borders
    def wrap(content):
        # Interior is 58 chars wide
        return f"{gray}│{res} {content}{' ' * (57 - len(content.replace(cyan, '').replace(pink, '').replace(green, '').replace(gray, '').replace(res, '')))}{gray}│{res}\n"

    # Frame construction
    top = f"{gray}┌─── {pink}[ CHAOS COMPUTER CLUB ]{gray} {'─' * 30}┐{res}\n"
    mid = f"{gray}├{'─' * 58}┤{res}\n"
    bot = f"{gray}└{'─' * 58}┘{res}\n"

    # Lines
    l1 = wrap(f"{cyan}STATUS:{res} EXPLOIT_ACTIVE    {cyan}NODE:{res} HAMBURG_C3")
    l2 = wrap(f"{cyan}TARGET:{res} PGP_KEY_INJECT    {cyan}AUTH:{res} ROOT")

    # The Glider (using dots and half-blocks for a cleaner look)
    # . ▄ .
    # . . ▄
    # ▄ ▄ ▄
    g1 = wrap(f"{pink}[ GLIDER.EXE ]{res}          {pink}[ BINARY_STREAM ]{res}")
    g2 = wrap(f"    {green}· ▄ ·{res}               01000011  (C)")
    g3 = wrap(f"    {green}· · ▄{res}               01000011  (C)")
    g4 = wrap(f"    {green}▄ ▄ ▄{res}               01000011  (C)")

    # Footer info
    l3 = wrap(f"{gray}>> Packet injection successful...{res}")

    # Assemble
    art = f"\n{top}{l1}{l2}{mid}{g1}{g2}{g3}{g4}{l3}{bot}"

    if custom_text:
        art += f"{custom_text}\n"
    else:
        art += "\n"

    return art

# To test: print(get_payload("Welcome back, hacker."))