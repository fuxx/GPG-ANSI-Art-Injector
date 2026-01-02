def get_payload(custom_text=""):
    """
    Returns an ANSI art of a Microchip (IC).
    FIXED: Strict 20-char internal width for pixel-perfect border alignment.
    """
    # --- Palette ---
    c_sil = "\033[38;5;236m"  # Dark Silicon Grey (Body background feel)
    c_pin = "\033[38;5;250m"  # Silver (Pins/Borders)
    c_trc = "\033[38;5;46m"  # PCB Green (Text/Traces)
    c_lbl = "\033[38;5;255m"  # White (Main Label)
    res = "\033[0m"

    # Left padding to separate from shell prompt
    pad = "  "

    # --- Geometry Logic ---
    # The chip internal body is exactly 20 characters wide.
    # We must center all content within this 20-char block.

    def chip_row(content):
        # 1. Strip ANSI codes to get visual length
        plain = content.replace(c_sil, "").replace(c_pin, "").replace(c_trc, "").replace(c_lbl, "").replace(res, "")

        # 2. Calculate centering padding for exactly 20 chars
        target_w = 20
        if len(plain) > target_w:
            # Truncate if too long (prevents layout break)
            content = content[:target_w]
            plain = plain[:target_w]

        needed = target_w - len(plain)
        left = needed // 2
        right = needed - left

        # 3. Construct the line: Pin | Space Content Space | Pin
        # Note: We use c_sil (Dark Grey) for the empty space to make it look solid
        return f"{pad}   {c_pin}|{c_sil}{' ' * left}{content}{c_sil}{' ' * right}{c_pin}|{res}"

    # --- Content Preparation ---
    # Static Labels
    l_moto = f"{c_lbl}M O T O R O L A"
    l_chip = f"{c_trc}MC68000L8"
    l_hex = f"{c_trc}0xDEADBEEF"

    # Custom Text Logic
    # Default to "PGP SECURE" if empty
    txt_val = custom_text[:20] if custom_text else "PGP SECURE"
    l_cust = f"{c_lbl}{txt_val}"

    # --- Assembly ---
    lines = []

    # 1. Upper Traces
    lines.append(f"{pad}      {c_trc}|  |  |  |  |  |{res}")

    # 2. Chip Cap (Top)
    # The cap defines the width: 20 underscores
    lines.append(f"{pad}    {c_pin}__H__H__H__H__H__H__{res}")
    lines.append(
        f"{pad}   {c_pin}|{c_sil}____________________{c_pin}|{res}")  # +1 underscore to cover right edge corner

    # 3. Chip Body (The Rows)
    lines.append(chip_row(""))
    lines.append(chip_row(l_moto))
    lines.append(chip_row(l_chip))
    lines.append(chip_row(""))
    lines.append(chip_row(l_cust))
    lines.append(chip_row(l_hex))
    lines.append(chip_row(""))

    # 4. Chip Cap (Bottom)
    lines.append(f"{pad}   {c_pin}|{c_sil}____________________{c_pin}|{res}")
    lines.append(f"{pad}      {c_pin}T  T  T  {c_sil}U{c_pin}  T  T{res}")
    lines.append(f"{pad}      {c_trc}|  |  |  |  |  |{res}")

    # Final string construction
    art = "\n" + "\n".join(lines) + "\n"

    return art