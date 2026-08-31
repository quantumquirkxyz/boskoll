# Use SQLite + JSON for local storage

Status: accepted
Date: 2026-08-30

## Context

boskoll needs to persist conversation history, project decisions, architecture choices, and configuration locally. The storage must work offline, support complex queries (e.g., "show all architecture decisions from the last month"), and be simple to set up without external dependencies.

## Decision

Use SQLite for structured data (history, decisions, project memory) and JSON for configuration files.

## Consequences

- Positive: SQLite is zero-config, works offline, supports complex SQL queries, and is battle-tested. JSON is human-readable and easy to edit for configuration. Both are file-based and portable.
- Negative: SQLite has limited concurrent write support (acceptable for single-user CLI). JSON files require manual parsing for complex queries. No built-in replication or backup.
- Follow-up: Implement automatic SQLite backups; consider PostgreSQL for cloud-hosted boskoll Cloud in Phase 4.

## Considered Options

- **SQLite + JSON**: Zero-config, offline-capable, complex queries for structured data, human-readable config.
- **JSON only**: Simpler, but harder to query and maintain at scale.
- **PostgreSQL**: More powerful, but requires external database server; overkill for local storage.
- **Redis**: Fast in-memory store, but not persistent by default; better for caching than primary storage.
