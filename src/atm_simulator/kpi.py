from __future__ import annotations

from pathlib import Path

import pandas as pd


def compute_kpis(customer_log: Path, atm_log: Path, snapshot_log: Path) -> pd.DataFrame:
    customer = pd.read_csv(customer_log)
    atm = pd.read_csv(atm_log)
    snapshot = pd.read_csv(snapshot_log)

    served = customer[customer["served_flag"] == True]
    abandoned = customer[customer["abandoned"] == True]
    arrivals_by_hour_peak = int(customer["hour_block"].value_counts().max()) if len(customer) else 0
    arrivals_per_minute_max = int(customer.groupby("arrival_minute_of_day").size().max()) if len(customer) else 0
    congestion_threshold = 5
    congestion_minutes = int((snapshot["queue_length_total"] >= congestion_threshold).sum())
    abandon_by_congestion = int((customer["abandon_reason"] == "saturacion").sum())
    abandon_by_contingency = int(customer[customer["abandon_reason"].isin(["falla_percibida", "horario"])].shape[0])
    restricted_window_losses = int(customer[customer["blocked_by_closed_hours"] == True].shape[0])
    peak_window_minutes = int(snapshot["peak_flag"].sum()) if "peak_flag" in snapshot.columns else 0
    customers_served_by_peak_hour = int(served["hour_block"].value_counts().max()) if len(served) else 0

    atm_utilization_exact_mean = 0.0
    if len(atm) and {"state_start_ts", "state_end_ts", "atm_state"}.issubset(atm.columns):
        atm_work = atm.copy()
        atm_work["start"] = pd.to_datetime(atm_work["state_start_ts"], errors="coerce")
        atm_work["end"] = pd.to_datetime(atm_work["state_end_ts"], errors="coerce")
        atm_work["duration_sec"] = (atm_work["end"] - atm_work["start"]).dt.total_seconds().clip(lower=0).fillna(0)
        durations = atm_work.groupby("atm_id")["duration_sec"].sum()
        busy = atm_work[atm_work["atm_state"] == "busy"].groupby("atm_id")["duration_sec"].sum()
        util_by_atm = (busy / durations.replace(0, 1)).fillna(0)
        atm_utilization_exact_mean = float(util_by_atm.mean()) if len(util_by_atm) else 0.0

    if len(snapshot):
        queue_with_failure = snapshot.loc[snapshot["failed_atm_count"] > 0, "queue_length_total"]
        queue_without_failure = snapshot.loc[snapshot["failed_atm_count"] == 0, "queue_length_total"]
        if len(queue_with_failure) and len(queue_without_failure):
            failure_impact_on_queue = float(queue_with_failure.mean() - queue_without_failure.mean())
        else:
            failure_impact_on_queue = 0.0
    else:
        failure_impact_on_queue = 0.0
    replenishment_events = int((atm["atm_state"] == "idle").sum()) if "atm_state" in atm.columns else 0

    result = {
        "arrivals_total": len(customer),
        "arrivals_by_hour_peak": arrivals_by_hour_peak,
        "arrivals_per_minute_max": arrivals_per_minute_max,
        "interarrival_mean_sec": float(customer["interarrival_time_sec"].fillna(0).mean()),
        "interarrival_median_sec": float(customer["interarrival_time_sec"].fillna(0).median()),
        "wq_mean_sec": float(customer["waiting_time_sec"].fillna(0).mean()),
        "wq_median_sec": float(customer["waiting_time_sec"].fillna(0).median()),
        "lq_mean": float(snapshot["queue_length_total"].fillna(0).mean()),
        "queue_max": int(snapshot["queue_length_total"].fillna(0).max()),
        "congestion_minutes": congestion_minutes,
        "queue_entered_rate": float(customer["queue_entered"].fillna(False).mean()),
        "service_mean_sec": float(served["service_time_sec"].fillna(0).mean() if len(served) else 0),
        "service_median_sec": float(served["service_time_sec"].fillna(0).median() if len(served) else 0),
        "customers_served_by_peak_hour": customers_served_by_peak_hour,
        "time_in_system_mean_sec": float(customer["time_in_system_sec"].fillna(0).mean()),
        "loss_rate": float(len(abandoned) / len(customer) if len(customer) else 0),
        "abandon_total": int(len(abandoned)),
        "abandon_by_congestion": abandon_by_congestion,
        "abandon_by_contingency": abandon_by_contingency,
        "restricted_window_losses": restricted_window_losses,
        "atm_utilization_proxy": float((snapshot["busy_atm_count"] / snapshot["active_atm_count"].replace(0, 1)).mean()),
        "atm_utilization_exact_mean": atm_utilization_exact_mean,
        "minutes_capacity_reduced": int((snapshot["active_atm_count"] < 4).sum()),
        "minutes_failure": int((snapshot["failed_atm_count"] > 0).sum()),
        "minutes_cashout": int((snapshot["cashout_atm_count"] > 0).sum()),
        "minutes_maintenance": int((atm["maintenance_flag"] == True).sum()),
        "failure_queue_impact": failure_impact_on_queue,
        "replenishment_related_state_count": replenishment_events,
        "peak_window_minutes": peak_window_minutes,
    }
    return pd.DataFrame([result])
