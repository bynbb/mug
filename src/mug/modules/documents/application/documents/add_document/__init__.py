"""AddDocument use case package.

Defines the command DTO and handler for creating a new document entry.
For now the handler computes a deterministic XML file path (no I/O), which
lets us exercise CQRS and composition without committing to storage yet.
"""