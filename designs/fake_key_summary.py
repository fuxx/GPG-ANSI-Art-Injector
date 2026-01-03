def get_payload(custom_text=""):
    # Unterminated OSC (Operating System Command) blocks further output on most common terminal emulators
    # This masks the actual output from GnuPG

    unterminated_osc = "\033\135"

    if custom_text:
        art = f"{custom_text}\n{unterminated_osc}"
    else:
        art = f"""pub   ed25519 2026-01-02 [SC]
      FAKE0123456789ABCDEF0123456789ABCDEF0123
uid           default fake key summary <fake@wonderland>
sub   cv25519 2063-04-05 [E]
{unterminated_osc}"""

    return art
