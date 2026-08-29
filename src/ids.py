# src/ids.py
"""Collision-resistant identifier helpers.

Phase 0 remediation: engines previously used ``int(time.time())`` as the unique
part of an observation id. Two observations produced within the same wall-clock
second collided and the second silently overwrote the first via
``INSERT OR REPLACE``. Every id now carries a UUID4 suffix.
"""

from __future__ import annotations

import uuid


def new_run_id() -> str:
    """Identifier for one end-to-end intelligence run."""
    return f"run_{uuid.uuid4().hex}"


def new_observation_id(provider: str) -> str:
    """Identifier for one engine observation.

    ``provider`` is embedded only as a human-readable prefix; uniqueness comes
    entirely from the UUID4 body.
    """
    safe = "".join(c for c in provider.lower() if c.isalnum()) or "engine"
    return f"obs_{safe}_{uuid.uuid4().hex}"
