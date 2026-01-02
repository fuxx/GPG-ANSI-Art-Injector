def get_payload(custom_text=""):
    red_bg = "\033[41m"
    white_fg = "\033[97m"
    reset = "\033[0m"
    
    msg = " DANGER: UNAUTHORIZED ACCESS "
    
    # Simple box logic
    line = f"{red_bg}{white_fg}{msg}{reset}"
    
    art = f"\n{line}\n"
    
    if custom_text:
        art += f"{custom_text}\n"
    else:
        art += "\n"
        
    return art
