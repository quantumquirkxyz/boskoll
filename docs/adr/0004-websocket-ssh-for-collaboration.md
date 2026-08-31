# Use WebSocket + SSH for real-time collaboration

Status: accepted
Date: 2026-08-30

## Context

boskoll supports real-time collaborative sessions where 5+ users can work on the same prompt, review code together, and discuss in a shared chat. The collaboration protocol must support multiple simultaneous users, work across different network conditions, and provide security for enterprise use cases.

## Decision

Use WebSocket as the primary collaboration protocol, with SSH as a secondary protocol for secure enterprise sessions.

## Consequences

- Positive: WebSocket is widely supported, works from any client (TUI, browser, CLI), and supports bidirectional real-time communication. SSH provides enterprise-grade security for sensitive environments. Pub/sub architecture scales to 5+ users from MVP.
- Negative: WebSocket requires server infrastructure for session management. SSH adds complexity for key management and authentication. Pub/sub architecture requires careful state reconciliation.
- Follow-up: Implement session persistence and reconnection logic; evaluate WebRTC for peer-to-peer collaboration in Phase 3.

## Considered Options

- **WebSocket**: Industry standard for real-time web communication, works from any client, bidirectional.
- **SSH**: Most secure option, but requires key management and server access; better for enterprise.
- **WebRTC**: Peer-to-peer, no server needed, but more complex to implement and troubleshoot.
- **gRPC**: Fast and efficient, but less suitable for interactive real-time collaboration.
