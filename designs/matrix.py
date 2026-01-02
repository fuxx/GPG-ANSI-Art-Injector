def get_payload(custom_text=""):
    # --- Configuration ---
    # Matrix Green text (color 46 is standard bright green)
    matrix_green = "\033[38;5;46m"
    # Deep Black background
    black_bg = "\033[48;5;16m"
    reset = "\033[0m"

    width = 44
    
    # A static "snapshot" of digital rain
    # Using 0s, 1s, and spacing to create the vertical rain effect
    matrix_lines = [
        " 0  1  0  1  0  1  1  0  1  0  1  0  1  1 ",
        " 1  0  1  1  0  0  1  0  1  1  0  0  1  0 ",
        " 0  1  0  0  1  0  1  0  0  1  0  1  0  1 ",
        " 1  0  1  1  0  1  0  1  1  0  1  0  1  0 ",
        " 0  1  0  1  0  0  1  0  1  0  0  1  0  1 "
    ]

    # --- Build the Payload ---
    rows = []
    
    # Optional: Add a "System Header" line
    header_text = " [ SYSTEM ENCRYPTED ] "
    pad_len = (width - len(header_text)) // 2
    header_line = f"{black_bg}{matrix_green}{' '*pad_len}{header_text}{' '*pad_len}{reset}"
    rows.append(header_line)

    for line in matrix_lines:
        # Center the binary block
        pad_total = width - len(line)
        pad_left = pad_total // 2
        pad_right = pad_total - pad_left
        
        # Construct row: Black BG + Green Text + Padding + Binary + Padding + Reset
        row = f"{black_bg}{matrix_green}{' ' * pad_left}{line}{' ' * pad_right}{reset}"
        rows.append(row)

    # --- Assemble ---
    art = "\n" + "\n".join(rows)

    if custom_text:
        # For the Matrix theme, let's force the custom text to be green too
        art += f"\n{black_bg}{matrix_green} > {custom_text} {reset}\n"
    else:
        art += "\n"

    return art
