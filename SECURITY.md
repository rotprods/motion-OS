# Security Policy

MOTION.OS is in active private-development mode even if repository visibility has not yet been migrated.

- Never commit credentials, API keys, private user data, proprietary media, or large generated artifacts.
- Generated media and heavy reference assets live in the Drive artifact plane and are referenced by immutable IDs/hashes.
- Treat renderer/tool inputs as untrusted and validate paths, URLs, licenses and provenance.
- Report suspected security defects through a private channel rather than a public issue when disclosure could increase risk.
