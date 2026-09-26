# Ring developer experience friction log

This log records genuine issues encountered while building GuardianMesh for the
Ring track. It intentionally excludes speculative feedback and contains no
credentials, access tokens, or raw device identifiers.

## 1. Finding the local-development authorization path

- **Task attempted:** Connect a private Ring application to a local backend.
- **Steps taken:** Created the application, saved its one-time credentials,
  opened account-linking configuration, and reviewed the required service URLs
  before discovering the temporary Playground-token workflow.
- **Expected:** A clearly signposted path from app creation to the first local,
  authenticated API request.
- **Actual:** Account linking appeared to require production-style public URLs,
  although Playground provided the appropriate temporary testing path.
- **Severity:** Medium.
- **Workaround:** Used a temporary Ring Playground OAuth token stored only in
  the backend `.env` file.
- **Actionable suggestion:** After app creation, offer a choice between **Local
  Playground testing** and **Production account linking**, with a short guided
  checklist for each.

## 2. Temporary token expiry during development

- **Task attempted:** Maintain device discovery and event synchronization while
  repeatedly testing the dashboard.
- **Steps taken:** Generated a Playground token, stored it locally, restarted
  FastAPI, and called the device and history endpoints.
- **Expected:** A visible expiry time or warning before authenticated requests
  began failing.
- **Actual:** After expiry, Ring access became unavailable and the token had to
  be regenerated manually.
- **Severity:** Medium.
- **Workaround:** Added explicit expired-token handling, safe dashboard status
  messaging, and a recording preflight that verifies Ring access without
  printing the token.
- **Actionable suggestion:** Display the exact expiry time, warn before expiry,
  and provide a development-only renewal action.

## 3. Understanding an empty Event History response

- **Task attempted:** Verify end-to-end synchronization from Ring Playground
  into GuardianMesh.
- **Steps taken:** Generated a token, confirmed device discovery, invoked Event
  History, and initially received an empty `data` array.
- **Expected:** A sample event or clear instructions describing which Playground
  interaction would create each history-event type.
- **Actual:** Device access worked, but Event History remained empty until a
  live-view simulation was started and completed.
- **Severity:** Medium.
- **Workaround:** Completed a Playground live-view simulation, queried history
  again, and synchronized the resulting `on_demand` event.
- **Actionable suggestion:** Place a **Generate test history event** action beside
  the Event History explorer and document the expected delay and resulting
  `event_type`.

## 4. Mapping device relationships to follow-up endpoints

- **Task attempted:** Move from device discovery to device-specific history
  retrieval.
- **Steps taken:** Inspected Device List JSON, located the directed device ID and
  relationship links, and constructed the device-history request.
- **Expected:** A copyable end-to-end example connecting Device List,
  capabilities, status, and Event History.
- **Actual:** Individual responses were structured clearly, but discovering the
  intended request sequence required manual inspection.
- **Severity:** Low.
- **Workaround:** Implemented a backend Ring client that discovers devices and
  safely performs device-specific history requests.
- **Actionable suggestion:** Add a complete **List device → select ID → retrieve
  history** tutorial using one consistent sample response, with credentials and
  sensitive identifiers automatically redacted.

## Resulting product safeguards

These issues directly shaped GuardianMesh:

- explicit expired-token and unavailable-service states;
- provenance labels separating Ring history, simulations, and legacy events;
- idempotent event synchronization;
- a strict pre-recording readiness check; and
- documentation that never asks users to paste secrets into the browser.
