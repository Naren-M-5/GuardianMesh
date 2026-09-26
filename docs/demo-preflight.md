# Demo recording preflight

Run this immediately before every rehearsal and final recording:

```powershell
.\.venv\Scripts\python.exe scripts\demo_preflight.py --recording
```

The command checks:

- FastAPI on port 8000.
- Next.js on port 3000.
- All labeled synthetic benchmark cases still pass.
- A Ring token is configured locally without printing it.
- The Ring device API accepts the token and returns a device.
- A successful Ring event sync is recorded.

`READY FOR RECORDING` means every blocking check passed. Warnings still require review. The script does not refresh or transmit credentials.

## Expired-token recovery

1. Generate a fresh temporary token in Ring Playground.
2. Replace only `GUARDIANMESH_RING_ACCESS_TOKEN` in `.env`.
3. Restart Terminal 1 so FastAPI reloads the environment.
4. Open the dashboard and use **Sync Ring events** once.
5. Run preflight again and begin recording only after it reports ready.

Never paste the token into a screenshot, terminal recording, issue, commit, or Devpost description.
