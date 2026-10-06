# Security

v0.1.x is the only supported release line. This is local single-user software, not a multi-tenant service or security sandbox. Anyone with filesystem access can read mission data; the producer CLI flag is an explicit workflow acknowledgement, not identity verification.

Keep credentials, local databases, exports and logs out of Git. Attach only files you intend to copy into your local workspace. Evidence hashes detect changes, not the truth of an agent's claims. The generic assignment parser consumes untrusted text and never executes commands.

No provider calls or shell execution are enabled. Future adapters require review and cost controls. For vulnerabilities, use the repository's private vulnerability reporting facility when enabled; otherwise contact the maintainer privately through their GitHub profile. Do not post secrets or personal documents in a public issue.
