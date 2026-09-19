# Privacy Shield

Default posture:

- Raw video: temporary processing only
- Face identification: disabled and unsupported
- Continuous audio storage: disabled
- Event metadata: encrypted in deployed environments
- Sensitive modes: opt-in only
- Automatic emergency calls: disabled

The preferred transformation is `video -> local/approved CV -> structured event -> discard raw frame`. Data minimization takes precedence over richer model context.
