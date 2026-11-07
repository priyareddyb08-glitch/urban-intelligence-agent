
import pandas as pd


def analyze_incident(current, dataset, recalled_memories=None):
    """Analyze incidents using local history and Hindsight memories."""

    area = str(current.get("area", "")).strip().lower()
    kind = str(current.get("incident_type", "Road obstruction")).strip()
    severity = str(current.get("severity", "Medium")).strip()

    # Ignore error messages: they are not actual memories.
    valid_memories = [
        str(memory)
        for memory in (recalled_memories or [])
        if memory
        and "hindsight recall error" not in str(memory).lower()
        and "error:" not in str(memory).lower()
    ]

    # Find earlier incidents of the same type in the same area.
    if dataset is not None and not dataset.empty:
        matches = dataset[
            (dataset["area"].astype(str).str.lower() == area)
            & (
                dataset["incident_type"].astype(str).str.lower()
                == kind.lower()
            )
        ]
    else:
        matches = pd.DataFrame()

    repeated_count = len(matches)
    recalled_count = len(valid_memories)
    repeat_flag = repeated_count > 0 or recalled_count > 0

    if kind.lower() == "waterlogging":
        action = (
            "Alert approaching buses immediately. Request a road inspection "
            "and verify water depth and road passability. Use a verified "
            "alternate route if the stretch is unsafe."
        )
    elif kind.lower() == "pothole":
        action = (
            "Warn approaching drivers, mark the affected road section "
            "and forward the location to the road-maintenance team."
        )
    elif kind.lower() == "traffic congestion":
        action = (
            "Alert approaching buses and check alternate roads, traffic "
            "conditions and restrictions before rerouting."
        )
    else:
        action = (
            "Notify fleet control and request a road-condition inspection "
            "before sending additional vehicles through the location."
        )

    if severity in ["High", "Critical"]:
        action = (
            "HIGH-PRIORITY ALERT: Notify fleet control immediately. "
            "Ask drivers to slow down or avoid the affected stretch. "
            + action
        )

    if repeat_flag:
        summary = (
            f"Possible recurring issue: {repeated_count} matching "
            f"local dataset records and {recalled_count} valid "
            "Hindsight memories were found."
        )

        action += (
            " Prioritize this location for follow-up and verify whether "
            "earlier incidents were resolved."
        )

        note = (
            "Historical context considered. Sample dataset records "
            "are demonstration data, not verified live statistics."
        )

    else:
        summary = (
            "No matching earlier incident was found in the available "
            "local dataset or valid Hindsight memories."
        )

        note = (
            "This incident can serve as a baseline for future "
            "recurring-risk analysis."
        )

    return {
        "summary": summary,
        "action": action,
        "memory_note": note
    }


def recommend_action(current, dataset, recalled_memories=None):
    return analyze_incident(current, dataset, recalled_memories)
