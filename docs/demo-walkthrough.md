# Local demonstration

Run FastAPI on 127.0.0.1:8000 and open the dashboard at localhost:3000.
Ring credentials are not needed for the Local demo controls. Ring may show
unavailable while the local simulation remains usable.

1. Run Late Resident: cold start reports score 46. Resolve it as `Resident`.
2. Repeat Late Resident and resolve it as `Resident` until three confirmed patterns exist.
3. Run Late Resident once more: adaptive mode reports score 7 and shows the
   familiarity adjustment while retaining person evidence.
4. Resolve it, then run Intrusion: the unfamiliar entrance, prolonged activity,
   and rare sequence keep the score at 78 even after learning.
5. In Current assessment, select the Simulation: Intrusion card, acknowledge it,
   then resolve it with a note such as "Reviewed synthetic intrusion demo".
6. Show Recent activity: new demo events are explicitly labeled as simulations.

Routine remains score 0 and Delivery remains score 19 for shorter walkthroughs.

## Evolving situation demonstration

Run Evolving Intrusion to create three signals through the normal ingestion
pipeline. GuardianMesh keeps one incident ID and increases its assessment as
motion, person presence, prolonged activity, and a rare sequence accumulate.
The final dashboard card shows three correlated signals and their ordered types.

Run Expected Delivery to show the other direction: doorbell followed by person
receives an explicit expected-sequence adjustment while retaining the evidence.

Each click creates a new event and incident; existing Ring history is never cleared.
Repeated demos add records. Resolve prior high-score simulations before repeating
the walkthrough. The main score is the highest unresolved assessment in the fetched
window, not necessarily the last scenario. Demo timestamps use a fixed UTC hour
on the current date, so timeline order may differ from click order.

This demonstrates local ingestion, feedback-trained metadata baselines, adaptive
scoring, incident actions, and audit recording. It does not demonstrate a trained
neural model, physical Ring hardware, emergency response, or production security.
No physical actions are sent.
The existing history importer has been exercised with Playground on-demand events.

Keep the service local. The demo route accepts only the three named scenarios;
the dashboard proxy restricts the host and browser origin to local access.
