def get_payload(custom_text=""):
    # --- Configuration ---
    width = 44  # Width of the flag

    # ANSI Background Colors (256-color mode)
    colors = [
        "\033[48;5;196m",  # Red
        "\033[48;5;208m",  # Orange
        "\033[48;5;226m",  # Yellow
        "\033[48;5;46m",  # Green
        "\033[48;5;21m",  # Blue
        "\033[48;5;93m",  # Purple
    ]

    # Text color (White bold) and Reset
    txt_color = "\033[38;5;255;1m"
    reset = "\033[0m"

    # The content for each stripe. 
    # We map the 6 stripes to these characters.
    # Top and bottom are empty space.
    content_map = ["", "L", "O", "V", "E", ""]

    # --- Build the Flag ---
    rows = []

    for i, bg_code in enumerate(colors):
        letter = content_map[i]

        if letter:
            # Calculate padding to center the letter
            # We add spaces around the letter for the colored background
            text_part = f"{letter}"
            pad_total = width - len(text_part)
            pad_left = pad_total // 2
            pad_right = pad_total - pad_left

            # Construct the row: BG Color + Padding + White Text + Letter + Padding + Reset
            row = f"{bg_code}{' ' * pad_left}{txt_color}{letter}{bg_code}{' ' * pad_right}{reset}"
        else:
            # Just a solid color bar
            row = f"{bg_code}{' ' * width}{reset}"

        rows.append(row)

    # --- Assemble Payload ---
    # Join rows with newlines. 
    # Start with a newline to clear the shell prompt.
    art = "\n" + "\n".join(rows)

    # Append custom text if provided
    if custom_text:
        art += f"\n{custom_text}\n"
    else:
        art += "\n"

    return art
