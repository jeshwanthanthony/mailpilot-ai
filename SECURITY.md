# Security policy

Please report vulnerabilities privately through GitHub's security advisory feature. Do not open a public issue containing credentials, exploit details, or private email data.

MailPilot AI is a portfolio application and does not currently publish supported release branches. Security-sensitive dependencies are monitored with Dependabot, and the CI pipeline validates all three application services.

## Data-handling guarantees

- OAuth tokens are encrypted before storage and never sent to the browser.
- Email HTML is allowlist-sanitized and rendered in a sandboxed iframe.
- Knowledge vectors are scoped to the connected internal user ID.
- Prompt content is treated as untrusted data; model calls use `store=False`.
- Destructive mailbox actions require explicit user interaction.
