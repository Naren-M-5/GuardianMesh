# ADR-001: Start as a modular monolith

Status: accepted.

GuardianMesh begins as one deployable API with strict package boundaries. This preserves event-driven concepts and allows later extraction while minimizing solo-developer operations work.
