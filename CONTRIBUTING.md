# Contributing

MailPilot AI uses small, reviewable changes and requires automated checks before merge.

## Development workflow

1. Create a feature branch from `main`.
2. Install dependencies with `make install`.
3. Run the relevant services using `make dev-web`, `make dev-api`, and `make dev-intelligence`.
4. Add tests for changed behavior.
5. Run `make lint`, `make test`, and `make build` before opening a pull request.

Never commit OAuth credentials, Supabase service keys, session secrets, or `.env` files. New database changes belong in an additive, timestamped migration under `supabase/migrations`.

## Commit and review expectations

- Explain the user impact and any rollout risk in the pull request.
- Keep API contracts typed in both Pydantic and TypeScript.
- Prefer deterministic logic for business rules and reserve model calls for tasks that need language understanding.
- Preserve the demo path so reviewers can evaluate the interface without external credentials.
