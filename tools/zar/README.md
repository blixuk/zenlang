# Zen Archive Tool (`zar`)

Next-generation Unix archive creation, extraction, auditing, and packaging utility in 100% pure Zenlang.

## Features

- **Opt-in Compression**: Fast uncompressed stored archives by default, or opt-in RFC 1951 Deflate (`--compress` / `-c [1..9]`).
- **Opt-in Authenticated Encryption**: ChaCha20-Poly1305 AEAD + PBKDF2-HMAC-SHA256 (`--encrypt` / `-e`). Zero metadata leakage (filenames, counts, and directory paths completely hidden).
- **Tamperproof Cryptographic Seals**: IEEE 802.3 CRC-32 + SHA-256 digests per entry with a global Merkle tree root seal (`zen.crypto.merkle`).
- **Single-File Inclusion Proofs**: Prove that an individual file belongs to an authentic archive without unpacking.
- **Content-Addressable Deduplication**: Stores duplicate files only once in the payload block automatically.
- **Self-Extracting Executables (`sfx`)**: Bundle an archive into an executable runnable directly in Unix environments.
- **Passkey QR Codes**: Render terminal ANSI half-block or SVG QR codes for quick passkey sharing and cold storage backup.

## Usage

### 1. Create an Archive (`pack`)
```bash
# Basic uncompressed archive
zar pack ./src app.zar

# With Deflate compression (level 6)
zar pack ./src app.zar --compress

# With Authenticated Encryption & password
zar pack ./src app.zar --compress --encrypt "secret-key"

# Show QR code for passkey during creation
zar pack ./src app.zar --encrypt "secret-key" --qr
```

### 2. List Contents (`list`)
```bash
zar list app.zar
zar list app.zar --password "secret-key"
```

### 3. Extract Archive (`unpack`)
```bash
zar unpack app.zar
zar unpack app.zar ./output_dir
zar unpack app.zar ./output_dir --password "secret-key"
```

### 4. Verify Cryptographic Integrity (`verify`)
```bash
zar verify app.zar
```

### 5. Mutable Container Edits (`add` / `rm`)
```bash
zar add app.zar extra_file.txt
zar rm app.zar old_notes.txt
```

### 6. Create Self-Extracting Executable (`sfx`)
```bash
zar sfx ./src myapp --entry=main.zl
./myapp
```

### 7. Render QR Code for Passkey (`qr`)
```bash
zar qr "my-secret-vault-passkey"
```
