import base64
import struct
import argparse
import sys
import importlib.util
import os

# --- GPG PACKET LOGIC (Unchanged) ---
def crc24(data):
    crc = 0xB704CE
    for byte in data:
        crc ^= (byte << 16)
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF

def create_literal_packet(content_bytes):
    body = bytearray()
    body.append(0x75) # 'u' mode (text)
    body.append(0)    # Filename length 0
    body.extend(b'\x00\x00\x00\x00') # Timestamp 0
    body.extend(content_bytes)
    
    header = bytearray([0xCB]) # Tag 11
    length = len(body)
    
    if length < 192:
        header.append(length)
    elif length < 8384:
        length -= 192
        header.append((length >> 8) + 192)
        header.append(length & 0xFF)
    else:
        header.append(0xFF)
        header.extend(struct.pack('>I', length))
        
    return header + body

# --- MODULE LOADER ---
def load_module(path):
    module_name = os.path.basename(path).replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    parser = argparse.ArgumentParser(description="Inject modular ANSI art into a PGP key.")
    
    # NEW: Clearly defined named arguments
    parser.add_argument("-i", "--input", required=True, help="Path to your clean public key (e.g., original.asc)")
    parser.add_argument("-s", "--script", required=True, help="Path to the python design script (e.g., rainbow_love.py)")
    parser.add_argument("-o", "--output", required=True, help="Path where the new key will be saved (e.g., result.asc)")
    parser.add_argument("-t", "--text", help="Optional text message to display below the art", default="")
    
    args = parser.parse_args()

    # 1. Load the Art Module
    try:
        art_module = load_module(args.script)
        ansi_string = art_module.get_payload(args.text)
    except Exception as e:
        print(f"Error loading script '{args.script}': {e}")
        sys.exit(1)

    # 2. Process Key
    try:
        with open(args.input, "r") as f:
            key_content = f.read()
            
        pem_lines = key_content.strip().splitlines()
        base64_data = "".join([x for x in pem_lines if not x.startswith("-----") and not x.startswith("=")])
        original_key_bytes = base64.b64decode(base64_data)
    except Exception as e:
        print(f"Error reading input key '{args.input}': {e}")
        sys.exit(1)

    # 3. Combine & Armor
    payload_packet = create_literal_packet(ansi_string.encode('utf-8'))
    final_blob = payload_packet + original_key_bytes

    final_b64 = base64.b64encode(final_blob).decode('ascii')
    final_crc = crc24(final_blob)
    crc_bytes = struct.pack('>I', final_crc)[1:]
    crc_b64 = base64.b64encode(crc_bytes).decode('ascii')
    chunked_b64 = '\n'.join(final_b64[i:i+64] for i in range(0, len(final_b64), 64))

    output_pem = f"-----BEGIN PGP PUBLIC KEY BLOCK-----\n\n{chunked_b64}\n={crc_b64}\n-----END PGP PUBLIC KEY BLOCK-----"

    with open(args.output, "w") as f:
        f.write(output_pem)

    print(f"Success! Saved to: {args.output}")

if __name__ == "__main__":
    main()
