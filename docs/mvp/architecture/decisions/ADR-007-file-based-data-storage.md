# ADR-007: File-Based Data Storage

**Status:** Accepted - 2025-01-15

## Context

Need data storage for configuration and results. Full version will use database, but MVP needs simplest approach.

## Decision

Use **file-based storage** with JSON/CSV formats.

## Rationale

- **Local deployment**: No server infrastructure needed
- **Small data volume**: Typical scenarios have <1000 wagons
- **Simple installation**: No database setup required
- **Transparency**: Human-readable formats
- **Version control**: Git-friendly text files
- **Portability**: Easy to share and backup

## Alternatives Considered

- **Files (JSON/CSV)** ✅ Chosen
- **SQLite**: Overkill for MVP data volume
- **PostgreSQL**: Requires installation and setup
- **In-memory only**: No persistence

## Consequences

- **Positive**: Zero installation complexity, transparent data
- **Negative**: Limited scalability (acceptable for MVP)
- **Migration**: Repository pattern prepared for database transition