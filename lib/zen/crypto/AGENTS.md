# Purpose

The Zenlang Cryptography and Security standard library (`zen.crypto`). Provides a comprehensive, production-grade cryptographic toolkit implemented in 100% pure Zenlang with zero external C dependencies.

# Ownership

Standard library maintainers. Owned under `lib/zen/` as the security and cryptographic foundation for scripts, network servers, and standalone binaries.

# Local Contracts

- **100% Pure Zenlang:** All algorithms are implemented directly in Zenlang without runtime C bindings or external shared libraries.
- **Dual Execution Parity:** Every cipher, hash, padding scheme, and encoding must execute with identical output and behavior on both the AST Interpreter (`python3 bootstrap/Zen.py`) and Native AOT compiler (`./bin/zen run`, `-g`).
- **Mathematical Safety & Limb Decomposition:**
  - Standard 32-bit arithmetic must mask results using `& 0xffffffff`.
  - 64-bit algorithms (SHA-512, SHA-384, FNV-1a 64-bit) must decompose 64-bit words into pairs of 32-bit limbs `[hi, lo]` to avoid signed integer arithmetic right shift (`>>`) sign-extension issues in generated C code.
- **Bitwise Syntax:** Bitwise XOR must strictly use `^^` (since `^` is not valid in Zenlang). Bitwise AND (`&`), OR (`|`), shifts (`<<`, `>>`).
- **Constant-Time Verification:** Message authentication verification (`Crypto.HMAC.verify`, Poly1305 MAC check) must use constant-time accumulator comparisons to protect against timing side-channel attacks.
- **Modular Hash Structure:** Each hash algorithm resides in its own focused module (`sha256.zl` for SHA-256/224, `sha512.zl` for SHA-512/384, `sha1.zl` for SHA-1, `md5.zl` for MD5, `fnv.zl` for FNV-1a 32/64-bit), aggregated cleanly by `hash.zl` and `crypto.zl`.
- **Standard Binary-to-Text Encodings:** Full RFC and Web3 base encoding suites: `base16.zl` (RFC 4648 §8), `base32.zl` (RFC 4648 §6, §7 Base32Hex, and Crockford), `base58.zl` (Bitcoin/IPFS Base58 and Base58Check), `base64.zl` (RFC 4648 §4 and Base64URL), `base85.zl` (Ascii85 Adobe and ZeroMQ Z85), and `hex.zl` (Unix hexdump).
- **Merkle Trees & Audit Proofs (`merkle.zl`):** Pure Zenlang cryptographic binary hash tree implementation. Supports leaf hashing, pair concatenation hashing, layered tree computation, inclusion audit path generation (`get_proof`), and constant-time verification (`verify_proof`).
- **Distributed Ledger & Blockchain (`blockchain.zl`):** Pure Zenlang Proof-of-Work blockchain ledger. Features deterministic transaction serialization, SHA-256 header hashing, customizable target difficulty mining, coinbase reward and transaction fee aggregation, account balance tracking, full chain validation, Merkle root verification, Base58Check wallet address generation, and import/export serialization.
- **Unified Package Root:** `zen.crypto.crypto` (`zen.crypto`) exports convenient namespaces (`ChaCha20`, `RC4`, `XOR`, `AES`, `XTEA`, `PBKDF2`, `Poly1305`, `AEAD`, `DH`, `Classical`, `CRC32`, `Hash`, `HMAC`, `JWT`, `UUID`, `Base16`, `Base32`, `Base58`, `Base64`, `Base85`, `Hex`, `Merkle`, `Blockchain`) and top-level convenience functions (`sha256`, `sha512`, `sha384`, `sha224`, `sha1`, `md5`, `fnv1a`, `fnv1a64`, `crc32`, `crc32_hex`, `uuid`).

# Work Guidance

- Standard test vectors: every module must include official test vectors from RFCs or NIST FIPS specifications.
- Memory: avoid unbounded buffer reallocations in tight inner loops.
- Strings: Zenlang strings strictly use backticks (``` `...` ```); double quotes (`"`) are forbidden.

# Verification

- Pure interpreter test: `python3 bootstrap/Zen.py tests/lib/test_crypto_ciphers.zl`
- Native AOT test: `./bin/zen run tests/lib/test_crypto_ciphers.zl`
- Full showcase demo: `./bin/zen run examples/crypto_ciphers_showcase.zl`
- Standard library interpreter suite: `./scripts/zen test-lib`
- Standard library native suite: `./scripts/zen test-lib-native`

# Child DOX Index

None (leaf package).
