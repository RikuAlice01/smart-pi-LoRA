import secrets
key = secrets.token_bytes(32)
with open("keyfile.bin", "wb") as f:
    f.write(key)
print("Key file generated.")
