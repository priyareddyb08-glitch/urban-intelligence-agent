
import os
import streamlit as st
from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()


class MemoryManager:
    """Hindsight memory manager for urban incident response."""

    def __init__(self):
        try:
            secrets = st.secrets
        except Exception:
            secrets = {}

        self.api_key = (
            secrets.get("HINDSIGHT_API_KEY", "")
            or os.getenv("HINDSIGHT_API_KEY", "")
        ).strip()

        self.base_url = (
            secrets.get("HINDSIGHT_BASE_URL", "")
            or os.getenv(
                "HINDSIGHT_BASE_URL",
                "https://api.hindsight.vectorize.io"
            )
        ).strip()

        self.bank_id = (
            secrets.get("HINDSIGHT_BANK_ID", "")
            or os.getenv(
                "HINDSIGHT_BANK_ID",
                "urban-incident-response"
            )
        ).strip()

        self.client = None
        self.error = None

        if self.api_key:
            try:
                self.client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key
                )

            except Exception as exc:
                self.error = str(exc)
                self.client = None
        else:
            self.error = "HINDSIGHT_API_KEY is missing."

    @property
    def is_hindsight_enabled(self):
        return self.client is not None

    def store_incident(self, item):
        if not self.client:
            return "Hindsight not connected: " + str(self.error)

        content = (
            f"Public transport road incident. "
            f"ID: {item.get('incident_id')}. "
            f"Reported at: {item.get('reported_at')}. "
            f"Area: {item.get('area')}. "
            f"Road: {item.get('road')}. "
            f"Type: {item.get('incident_type')}. "
            f"Severity: {item.get('severity')}. "
            f"Vehicle: {item.get('vehicle_id')}. "
            f"Observation: {item.get('description')}."
        )

        try:
            self.client.retain(
                bank_id=self.bank_id,
                content=content,
                context="Urban fleet incident report",
                metadata={
                    "incident_id": str(item.get("incident_id", "")),
                    "area": str(item.get("area", "")),
                    "incident_type": str(item.get("incident_type", ""))
                }
            )
            return "Stored in Hindsight memory."

        except Exception as exc:
            self.error = str(exc)
            return f"Hindsight retain failed: {exc}"

    def recall_incidents(self, query):
        if not self.client:
            return []

        try:
            result = self.client.recall(
                bank_id=self.bank_id,
                query=query,
                budget="low"
            )

            return [
                memory.text
                for memory in result.results
            ]

        except Exception as exc:
            self.error = str(exc)
            return [f"Hindsight recall error: {exc}"]

    def seed_from_dataframe(self, df):
        if not self.client:
            return 0

        count = 0

        for _, row in df.iterrows():
            status = self.store_incident(row.to_dict())

            if status == "Stored in Hindsight memory.":
                count += 1

        return count
