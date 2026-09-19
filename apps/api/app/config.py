import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("GUARDIANMESH_DB_PATH", "./guardianmesh.db")
    webhook_secret: str = os.getenv("GUARDIANMESH_RING_WEBHOOK_SECRET", "change-me")
    ring_access_token: str = os.getenv("GUARDIANMESH_RING_ACCESS_TOKEN", "")
    ring_api_base_url: str = os.getenv(
        "GUARDIANMESH_RING_API_BASE_URL", "https://api.amazonvision.com"
    )
    allow_unsigned_simulator: bool = os.getenv(
        "GUARDIANMESH_ALLOW_UNSIGNED_SIMULATOR", "false"
    ).lower() == "true"


settings = Settings()
