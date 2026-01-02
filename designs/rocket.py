def get_payload(custom_text=""):
    """
    Returns an ANSI art of the 'Fairy Dust' Rocket.
    Refined: Smoother nose cone and better fuselage proportions.
    """
    # --- Palette ---
    c_body = "\033[38;5;255m"  # White
    c_acc = "\033[38;5;196m"  # Red (Fins/Nose)
    c_fire = "\033[38;5;208m"  # Orange/Yellow Fire
    c_gry = "\033[38;5;240m"  # Grey smoke/text
    res = "\033[0m"

    pad = "   "
    lines = []

    # 1. Nose Cone (Smoothed)
    # Replaced the floating '^' with a joined tip
    lines.append(f"{pad}      {c_acc}/{c_acc}\\{res}")
    lines.append(f"{pad}     {c_body}/{c_acc}__\\{res}")

    # 2. Fuselage
    # Slightly wider feel with double pipes
    lines.append(f"{pad}     {c_body}|  |{res}")
    lines.append(f"{pad}     {c_body}|{c_acc}C{c_body} |{res}")
    lines.append(f"{pad}     {c_body}|{c_acc}C{c_body} |{res}")
    lines.append(f"{pad}     {c_body}|{c_acc}C{c_body} |{res}")
    lines.append(f"{pad}     {c_body}|__|{res}")

    # 3. Fins & Thrusters
    # Fins extend wider to ground it
    lines.append(f"{pad}    {c_acc}/{c_body}|  |{c_acc}\\{res}")
    lines.append(f"{pad}   {c_acc}/{c_acc}_|  |_{c_acc}\\{res}")
    lines.append(f"{pad}     {c_gry}/  \\{res}")

    # 4. Engine Exhaust (Fairy Dust)
    lines.append(f"{pad}     {c_fire}vvvv{res}")
    lines.append(f"{pad}     {c_fire}(  ){res}")
    lines.append(f"{pad}     {c_fire} \\/{res}")
    lines.append(f"{pad}      {c_fire}||{res}")

    # 5. Mission Label
    lines.append(f"{pad} {c_gry}[ FAIRY DUST ]{res}")

    # Assembly
    art = "\n" + "\n".join(lines)

    if custom_text:
        art += f"{pad} {c_acc}>> {custom_text}{res}\n"
    else:
        art += "\n"

    return art