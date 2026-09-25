# Local demonstration

Run FastAPI on 127.0.0.1:8000 and open the dashboard at localhost:3000.
Ring credentials are not needed for the Local demo controls. Ring may show
unavailable while the local simulation remains usable.

1. Run Routine: the per-run message reports score 0.
2. Run Delivery: the message reports score 19 from simulated person evidence.
3. Run Intrusion: the message reports score 78 from the existing deterministic rules.
4. In Current assessment, select the Simulation: Intrusion card, acknowledge it,
   then resolve it with a note such as "Reviewed synthetic intrusion demo".
5. Show Recent activity: new demo events are explicitly labeled as simulations.

Each click creates a new event and incident; existing Ring history is never cleared.
Repeated demos add records. Resolve prior high-score simulations before repeating
the walkthrough. The main score is the highest unresolved assessment in the fetched
window, not necessarily the last scenario. Demo timestamps use a fixed UTC hour
on the current date, so timeline order may differ from click order.

This demonstrates local ingestion, deterministic scoring, incident actions, and
audit recording. It does not demonstrate trained anomaly detection, physical Ring
hardware, emergency response, or production security. No physical actions are sent.
The existing history importer has been exercised with Playground on-demand events.

Keep the service local. The demo route accepts only the three named scenarios;
the dashboard proxy restricts the host and browser origin to local access.
