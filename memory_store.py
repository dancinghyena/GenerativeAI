"""Simple in-memory long-term memory for customer music preferences."""

from typing import Dict


class PreferenceMemory:
    """Stores per-customer preference text in memory for the session lifetime."""

    def __init__(self):
        self._store: Dict[str, str] = {}

    def load(self, customer_id: str) -> str:
        if not customer_id:
            return ""
        return self._store.get(str(customer_id), "")

    def save(self, customer_id: str, preferences: str) -> None:
        if not customer_id or not preferences:
            return
        existing = self.load(customer_id)
        if existing and preferences not in existing:
            self._store[str(customer_id)] = f"{existing}; {preferences}"
        else:
            self._store[str(customer_id)] = preferences or existing

    def clear(self) -> None:
        self._store.clear()


# Shared process-wide store (simulates long-term memory for demos)
preference_memory = PreferenceMemory()
