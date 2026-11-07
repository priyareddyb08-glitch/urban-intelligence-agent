
import os
import asyncio

from hindsight_client import Hindsight


class MemoryManager:
    """Reliable Hindsight integration for the Urban Incident Response Agent."""

    def __init__(self):
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()

        self.base_url = os.getenv(
            "HINDSIGHT_BASE_URL",
            "https://api.hindsight.vectorize.io"
        ).strip()

        self.bank_id = os.getenv(
            "HINDSIGHT_BANK_ID",
            "urban-incident-response"
        ).strip()

        self.client = None
        self.error = None

        if not self.api_key:
            self.error = "HINDSIGHT_API_KEY is missing."
            return

        try:
            self.client = Hindsight(
                base_url=self.base_url,
                api_key=self.api_key
            )

            # Create the memory bank if it does not already exist.
            try:
                self._run_async(
                    lambda: self.client.acreate_bank(
                        bank_id=self.bank_id,
                        name="Urban Incident Response Agent",
                        background=(
                            "Memory bank for public transport road incidents, "
                            "recurring hazards and response recommendations "
                            "in Hyderabad."
                        )
                    )
                )
            except Exception:
                # An existing bank is acceptable.
                pass

        except Exception as exc:
            self.error = str(exc)
            self.client = None

    @staticmethod
    def _run_async(coroutine_factory):
        """Run an async Hindsight operation safely in its own event loop."""
        return asyncio.run(coroutine_factory())

    @property
    def is_hindsight_enabled(self):
        return self.client is not None

    def store_incident(self, item):
        """Store a reported road incident in Hindsight."""

        content = (
            f"Public transport road incident. "
            f"Incident ID: {item.get('incident_id')}. "
            f"Reported at: {item.get('reported_at')}. "
            f"Area: {item.get('area')}. "
            f"Road: {item.get('road')}. "
            f"Incident type: {item.get('incident_type')}. "
            f"Severity: {item.get('severity')}. "
            f"Vehicle: {item.get('vehicle_id')}. "
            f"Observation: {item.get('description')}."
        )

        if not self.client:
            return "Stored in local demo history. Hindsight is not connected."

        try:
            self._run_async(
                lambda: self.client.aretain(
                    bank_id=self.bank_id,
                    content=content,
                    context="Urban fleet incident report",
                    metadata={
                        "incident_id": str(item.get("incident_id", "")),
                        "area": str(item.get("area", "")),
                        "incident_type": str(item.get("incident_type", ""))
                    }
                )
            )

            return "Stored successfully in Hindsight memory."

        except Exception as exc:
            self.error = str(exc)
            return f"Hindsight storage error: {exc}"

    def recall_incidents(self, query):
        """Recall relevant historical road incidents."""

        if not self.client:
            return []

        try:
            result = self._run_async(
                lambda: self.client.arecall(
                    bank_id=self.bank_id,
                    query=query,
                    budget="low"
                )
            )

            if not result or not result.results:
                return []

            return [
                memory.text
                for memory in result.results
                if getattr(memory, "text", None)
            ]

        except Exception as exc:
            self.error = str(exc)
            return [f"Hindsight recall error: {exc}"]

    def seed_from_dataframe(self, df):
        """Store the sample incident dataset in Hindsight."""

        if not self.client:
            return 0

        count = 0

        for _, row in df.iterrows():
            item = row.to_dict()
            status = self.store_incident(item)

            if status == "Stored successfully in Hindsight memory.":
                count += 1

        return count
