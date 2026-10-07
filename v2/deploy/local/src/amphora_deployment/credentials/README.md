# Local credential protection

Owner BP-09.02/B1.02. This module creates a bounded current-user Windows DPAPI
credential file, bound to deployment identity through optional entropy. It does
not use machine-wide protection, interactive prompts, a shared application key,
plaintext credential files or automatic replacement on failure.

CredentialVault.create exclusively creates the encrypted file and flushes it.
Existing files are never overwritten. A truncated/unreadable file fails closed;
operators must recover it deliberately, not silently regenerate credentials and
lose access to existing data. SecretBundle.environment selects explicit names for
one child process; repr and installation manifests must not expose values.

Windows user protection is an at-rest boundary, not a sandbox against the same
user or privileged process/container administrators. Child environments hold
plaintext while running; managed-container configuration is visible to Docker
administrators. Python object copies cannot guarantee complete memory erasure.
Neither tokens nor database URLs with passwords belong in arguments or logs.

Implementation follows Microsoft's [CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)
and [CryptUnprotectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptunprotectdata)
contracts: UI forbidden, current-user scope, identical optional entropy, bounded
result and LocalFree cleanup. Decryption/profile errors are safe named reasons.
Tests under deploy/local/tests/credentials include actual DPAPI and fresh-process
recovery, wrong context, malformed ciphertext and create-once behavior.
