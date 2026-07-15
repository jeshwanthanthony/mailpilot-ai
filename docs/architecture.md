# MailPilot AI architecture

This document records the architectural boundaries and tradeoffs behind the portfolio implementation.

## Design goals

- Make the product reviewable without credentials while keeping a real connected path.
- Keep credentials and provider-specific logic behind the API boundary.
- Use generative models only for language tasks and deterministic code for business rules.
- Isolate every persisted record and vector lookup by the internal account identifier.
- Allow optional integrations to fail without taking down basic inbox access.

## Service boundaries

### Next.js web application

The frontend owns display state and user interactions. It does not possess Gmail tokens or call OpenAI directly. Shared response shapes are represented as TypeScript types, and all connected requests use credentialed cookies.

### FastAPI orchestration service

The Python API is the trust boundary. It validates sessions, exchanges and refreshes OAuth credentials, sanitizes messages, coordinates retrieval, and composes downstream services. FastAPI generates an inspectable OpenAPI contract from Pydantic models.

### Spring Boot intelligence service

The Java service owns high-volume deterministic scoring. The FastAPI service batches up to 50 message summaries into one request, avoiding per-message network calls. Every score includes human-readable signals, and an unavailable scorer simply leaves messages unscored.

### Postgres and pgvector

Supabase stores users, encrypted Gmail credentials, source documents, chunks, and embeddings. Knowledge chunks duplicate `user_id` intentionally: it makes the tenant predicate explicit in the hot vector-search path. Documents cascade to chunks on deletion.

The HNSW cosine index favors low-latency approximate nearest-neighbor retrieval. At this portfolio scale, indexing cost and recall are preferable to a separate vector database and its additional operational surface.

## RAG request lifecycle

1. The user submits verified reference content.
2. FastAPI normalizes and chunks it into bounded, overlapping passages.
3. OpenAI returns embeddings in input order.
4. The API stores the source and vectors in Postgres.
5. During drafting, the email subject, body, and user direction form a retrieval query.
6. A tenant-scoped SQL function returns the closest chunks above the configured similarity threshold.
7. Retrieved text is labeled as untrusted reference data in the generation prompt.
8. The draft response includes source titles and similarity scores for UI attribution.

## Failure behavior

| Failure | Behavior |
| --- | --- |
| Java service unavailable | Inbox loads without priority metadata; a warning is logged |
| Vector lookup unavailable | Drafting continues without retrieved context |
| OpenAI unavailable | Draft and indexing endpoints return a service error; Gmail remains usable |
| Gmail API error | Provider details stay server-side; the client receives a stable gateway error |
| Partial knowledge insert | The repository deletes the new document, cascading any stored chunks |

## Security boundaries

- Session state contains only the internal user ID.
- Gmail tokens are encrypted at the application layer.
- Supabase's service key stays server-side; RPC functions are revoked from public roles.
- Vector RPCs require an explicit user ID and apply that tenant predicate before ordering.
- HTML sanitization and iframe sandboxing are independent defense layers.
- Generation instructions explicitly separate system behavior from untrusted email and knowledge text.

## Scaling path

The current synchronous indexing flow is appropriate for pasted portfolio documents. Larger files would move chunking and embeddings to a queue-backed worker, keep document status in Postgres, and batch embedding calls. Gmail synchronization would similarly become incremental and event-driven. The Java API is already batch-shaped, so it can scale horizontally without shared state.
