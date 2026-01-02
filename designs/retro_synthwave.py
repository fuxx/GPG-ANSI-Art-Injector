def get_payload(custom_text=""):
    """
    Returns a 60-character wide synthwave sunset ANSI art.
    Ensures exact character counts to prevent padding/wrapping issues.
    """
    # Color definitions (256-color palette)
    sky_bg = "\033[48;5;232m"  # Deep Black sky
    sun_1 = "\033[48;5;226m"  # Yellow
    sun_2 = "\033[48;5;214m"  # Orange
    sun_3 = "\033[48;5;202m"  # Red-Orange
    sun_4 = "\033[48;5;196m"  # Red
    neon_p = "\033[48;5;201m"  # Hot Pink
    neon_c = "\033[48;5;51m"  # Cyan
    grid_b = "\033[48;5;18m"  # Deep Blue
    reset = "\033[0m"

    def line(content):
        # Ensures every line is exactly 60 chars and reset
        return f"{content}{reset}\n"

    # Sun components with exact widths
    # Format: sky + sun + sky = 60
    s1 = line(f"{sky_bg}{' ' * 22}{sun_1}{' ' * 16}{sky_bg}{' ' * 22}")
    s2 = line(f"{sky_bg}{' ' * 18}{sun_2}{' ' * 24}{sky_bg}{' ' * 18}")
    s3 = line(f"{sky_bg}{' ' * 15}{sun_2}{' ' * 30}{sky_bg}{' ' * 15}")
    # Thin slice
    gap = line(f"{sky_bg}{' ' * 60}")
    s4 = line(f"{sky_bg}{' ' * 13}{sun_3}{' ' * 34}{sky_bg}{' ' * 13}")
    s5 = line(f"{sky_bg}{' ' * 12}{sun_4}{' ' * 36}{sky_bg}{' ' * 12}")

    # Horizon and Grid
    horiz = line(f"{neon_p}{' ' * 60}")

    # Grid logic: exactly 60 chars
    # [12 blue][2 cyan][10 blue][2 cyan][10 blue][2 cyan][10 blue][2 cyan][10 blue] = 60
    g1 = line(
        f"{grid_b}{' ' * 12}{neon_c}  {grid_b}{' ' * 10}{neon_c}  {grid_b}{' ' * 10}{neon_c}  {grid_b}{' ' * 10}{neon_c}  {grid_b}{' ' * 10}")
    g2 = line(f"{neon_c}{' ' * 60}")
    # [8 blue][2 cyan][12 blue][2 cyan][16 blue][2 cyan][12 blue][2 cyan][4 blue] = 60
    g3 = line(
        f"{grid_b}{' ' * 8}{neon_c}  {grid_b}{' ' * 12}{neon_c}  {grid_b}{' ' * 16}{neon_c}  {grid_b}{' ' * 12}{neon_c}  {grid_b}{' ' * 4}")

    art = f"\n{s1}{s2}{s3}{gap}{s4}{s5}{horiz}{g1}{g2}{g3}"

    if custom_text:
        art += f"{custom_text}\n"
    else:
        art += "\n"

    return art