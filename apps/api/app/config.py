import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("GUARDIANMESH_DB_PATH", "./guardianmesh.db")
    webhook_secret: str = os.getenv("GUARDIANMESH_RING_WEBHOOK_SECRET", "change-me")
    allow_unsigned_simulator: bool = os.getenv(
        "GUARDIANMESH_ALLOW_UNSIGNED_SIMULATOR", "false"
    ).lower() == "true"


settings = Settings()
