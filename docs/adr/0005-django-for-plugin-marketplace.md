# Use Django for the plugin marketplace

Status: accepted
Date: 2026-08-30

## Context

boskoll includes a plugin marketplace where developers can publish, download, rate, and monetize agents and workflows. The marketplace needs user authentication, file uploads, search, payment processing, and an admin interface.

## Decision

Use Django as the framework for the plugin marketplace backend.

## Consequences

- Positive: Built-in ORM, admin interface, authentication, and file upload handling. Mature ecosystem with extensive documentation. Django REST Framework for API endpoints. Excellent for rapid development of content-heavy applications.
- Negative: Heavier than micro-frameworks (Flask, FastAPI) for simple APIs. Monolithic architecture may be overkill for initial MVP. Template engine adds complexity if not needed.
- Follow-up: Use Django REST Framework for API-only endpoints; consider Django Ninja for more modern API development if needed.

## Considered Options

- **Django**: Most complete Python web framework, built-in admin, ORM, auth. Best for content-heavy applications.
- **FastAPI**: More modern, faster for APIs, but lacks built-in admin and ORM. Better for microservices.
- **Flask**: Simpler and lighter, but requires more third-party packages for features Django includes.
