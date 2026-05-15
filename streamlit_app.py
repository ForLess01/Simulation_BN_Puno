from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from atm_simulator.runner import run_scenario
from atm_simulator.scenarios import scenario_matrix


ROOT = Path(__file__).resolve().parent


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def render_kpis(kpi_df: pd.DataFrame) -> None:
    if kpi_df.empty:
        st.warning("No hay KPIs disponibles para esta corrida.")
        return
    row = kpi_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Llegadas totales", int(row.get("arrivals_total", 0)))
    c2.metric("Wq promedio (s)", round(float(row.get("wq_mean_sec", 0)), 2))
    c3.metric("Loss rate", round(float(row.get("loss_rate", 0)), 4))
    c4.metric("Cola máxima", int(row.get("queue_max", 0)))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Arribos pico/hora", int(row.get("arrivals_by_hour_peak", 0)))
    c6.metric("Arribos máx/min", int(row.get("arrivals_per_minute_max", 0)))
    c7.metric("Capacidad reducida (min)", int(row.get("minutes_capacity_reduced", 0)))
    c8.metric("Utilización ATM media", round(float(row.get("atm_utilization_exact_mean", 0)), 4))


def render_atm_status(atm_df: pd.DataFrame) -> None:
    st.subheader("Estado ATM")
    if atm_df.empty:
        st.info("No hay registros ATM disponibles.")
        return

    latest = atm_df.groupby("atm_id").tail(1).copy()
    cols = st.columns(max(1, len(latest)))

    def color_for_state(state: str) -> str:
        return {
            "idle": "#d1fae5",
            "busy": "#fde68a",
            "cashout": "#fecaca",
            "down_failure": "#fca5a5",
            "down_maintenance": "#c7d2fe",
            "offline": "#e5e7eb",
        }.get(state, "#f3f4f6")

    for col, (_, row) in zip(cols, latest.iterrows()):
        state = row["atm_state"]
        bg = color_for_state(state)
        col.markdown(
            f"""
<div style="background:{bg}; padding:12px; border-radius:10px; border:1px solid #bbb; min-height:170px;">
  <h4 style="margin-top:0;">ATM {int(row['atm_id'])}</h4>
  <p><b>Estado:</b> {state}</p>
  <p><b>Efectivo:</b> {row['cash_available']}</p>
  <p><b>Falla:</b> {row['failure_flag']}</p>
  <p><b>Mantenimiento:</b> {row['maintenance_flag']}</p>
  <p><b>Red:</b> {row['network_outage_flag']}</p>
</div>
""",
            unsafe_allow_html=True,
        )


def render_pseudo_random_explanation(seed: int, scenario_id: str) -> None:
    st.subheader("Pseudoaleatoriedad y motor estocástico")
    st.markdown(
        f"""
**Semilla de ejecución:** `{seed}`  
**Escenario:** `{scenario_id}`

El simulador usa números pseudoaleatorios para muestrear:

- interarribos por franja horaria
- tiempos de servicio
- decisiones de abandono
- fallas, cashout y mantenimiento

La semilla fija permite reproducibilidad: una misma corrida con igual escenario y semilla debe generar la misma secuencia lógica de eventos.
"""
    )


def render_pseudo_random_panel(seed: int, scenario) -> None:
    st.subheader("Pseudoazar visible")
    col1, col2, col3 = st.columns(3)
    col1.metric("Seed", seed)
    col2.metric("Multiplicador λ", scenario.pressure_lambda_multiplier)
    col3.metric("Interarribo base (s)", scenario.distributions.interarrival_mean_sec)

    st.markdown(
        """
**Cómo leer este panel**

- La **seed** fija hace reproducible la corrida.
- El **multiplicador λ** modifica la intensidad de llegadas del escenario.
- El **interarribo base** es el punto de partida sobre el cual actúa el pseudoazar.

En esta versión, la UI muestra de forma pedagógica el contexto estocástico de la corrida. En una extensión futura podría exponer también la secuencia exacta de muestras uniformes y transformadas por distribución.
"""
    )


def render_recent_events(customer_df: pd.DataFrame) -> None:
    st.subheader("Eventos recientes de clientes")
    if customer_df.empty:
        st.info("No hay eventos de cliente disponibles.")
        return
    preview_cols = [
        "event_id",
        "arrival_ts",
        "transaction_type",
        "queue_entered",
        "queue_position_at_arrival",
        "abandoned",
        "abandon_reason",
        "atm_id",
        "peak_intraday_band",
    ]
    preview_cols = [c for c in preview_cols if c in customer_df.columns]
    st.dataframe(customer_df[preview_cols].tail(20), use_container_width=True)


def render_snapshots(snapshot_df: pd.DataFrame) -> None:
    st.subheader("Snapshots del sistema")
    if snapshot_df.empty:
        st.info("No hay snapshots disponibles.")
        return
    preview_cols = [
        "snapshot_ts",
        "hour_block",
        "queue_length_total",
        "active_atm_count",
        "busy_atm_count",
        "idle_atm_count",
        "failed_atm_count",
        "cashout_atm_count",
        "peak_operational_type",
        "peak_composite_level",
    ]
    preview_cols = [c for c in preview_cols if c in snapshot_df.columns]
    st.dataframe(snapshot_df[preview_cols].tail(20), use_container_width=True)


def render_charts(kpi_df: pd.DataFrame, customer_df: pd.DataFrame, snapshot_df: pd.DataFrame, seed: int) -> None:
    st.subheader("Gráficos de apoyo")

    if not customer_df.empty:
        arrivals_by_band = customer_df.groupby("peak_intraday_band").size().reset_index(name="arrivals")
        st.markdown("**Llegadas por banda intradía**")
        st.bar_chart(arrivals_by_band.set_index("peak_intraday_band"))

    if not snapshot_df.empty and "queue_length_total" in snapshot_df.columns:
        snap_df = snapshot_df.copy()
        snap_df["snapshot_ts"] = pd.to_datetime(snap_df["snapshot_ts"])
        st.markdown("**Evolución temporal de la cola**")
        st.line_chart(snap_df.set_index("snapshot_ts")["queue_length_total"])

    rows = []
    for scenario_id, scenario in scenario_matrix(seed).items():
        outdir = ROOT / "outputs" / scenario_id / f"seed{seed}" / "kpis.csv"
        if outdir.exists():
            df = pd.read_csv(outdir)
            if not df.empty:
                row = df.iloc[0].to_dict()
                row["scenario_id"] = scenario_id
                rows.append(row)
    if rows:
        comp = pd.DataFrame(rows)
        for metric in ["wq_mean_sec", "loss_rate", "arrivals_total"]:
            if metric in comp.columns:
                st.markdown(f"**Comparativa por escenario: {metric}**")
                st.bar_chart(comp.set_index("scenario_id")[[metric]])


def render_scenario_comparison(seed: int) -> None:
    st.subheader("Comparativa rápida de escenarios")
    rows = []
    for scenario_id, scenario in scenario_matrix(seed).items():
        outdir = ROOT / "outputs" / scenario_id / f"seed{seed}" / "kpis.csv"
        if outdir.exists():
            df = pd.read_csv(outdir)
            if not df.empty:
                row = df.iloc[0].to_dict()
                row["scenario_id"] = scenario_id
                rows.append(row)
    if not rows:
        st.info("Todavía no hay corridas previas para comparar con esta seed.")
        return
    df = pd.DataFrame(rows)
    cols = [
        "scenario_id",
        "arrivals_total",
        "wq_mean_sec",
        "loss_rate",
        "queue_max",
        "minutes_capacity_reduced",
    ]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].sort_values("scenario_id"), use_container_width=True)


def render_event_timeline(customer_df: pd.DataFrame, snapshot_df: pd.DataFrame) -> None:
    st.subheader("Timeline de la corrida")
    if customer_df.empty:
        st.info("No hay datos suficientes para construir timeline.")
        return

    customer_timeline = customer_df[["arrival_ts", "event_id", "transaction_type", "abandoned", "atm_id"]].copy()
    customer_timeline["timestamp"] = pd.to_datetime(customer_timeline["arrival_ts"])
    customer_timeline["kind"] = "customer_arrival"
    customer_timeline["detail"] = customer_timeline.apply(
        lambda r: f"{r['event_id']} | op={r['transaction_type']} | atm={r['atm_id']} | abandon={r['abandoned']}",
        axis=1,
    )
    timeline_frames = [customer_timeline[["timestamp", "kind", "detail"]]]

    if not snapshot_df.empty:
        snap_timeline = snapshot_df[["snapshot_ts", "queue_length_total", "peak_operational_type", "peak_composite_level"]].copy()
        snap_timeline["timestamp"] = pd.to_datetime(snap_timeline["snapshot_ts"])
        snap_timeline["kind"] = "snapshot"
        snap_timeline["detail"] = snap_timeline.apply(
            lambda r: f"queue={r['queue_length_total']} | oper={r['peak_operational_type']} | pressure={r['peak_composite_level']}",
            axis=1,
        )
        timeline_frames.append(snap_timeline[["timestamp", "kind", "detail"]])

    timeline = pd.concat(timeline_frames).sort_values("timestamp").tail(40)
    st.dataframe(timeline, use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="ATM SimPy Simulator", layout="wide")
    st.title("Simulación ATM BN Puno — Visualización operativa")
    st.caption("Interfaz de apoyo para observar la corrida, sus parámetros y sus salidas estructuradas.")

    st.sidebar.header("Control de simulación")
    seed = st.sidebar.number_input("Seed", min_value=1, value=42, step=1)
    scenario_id = st.sidebar.selectbox("Escenario", options=list(scenario_matrix(seed).keys()))
    run_button = st.sidebar.button("Ejecutar simulación")

    scenario_map = scenario_matrix(seed)
    scenario = scenario_map[scenario_id]

    st.sidebar.markdown("### Resumen del escenario")
    st.sidebar.write(f"ID: `{scenario.scenario_id}`")
    st.sidebar.write(f"Duración (s): `{scenario.duration_sec}`")
    st.sidebar.write(f"Branch: `{scenario.branch_id}`")
    st.sidebar.write(f"Payroll: `{scenario.payroll_cycle_type}`")
    st.sidebar.write(f"Social transfer: `{scenario.social_transfer_program}`")

    if run_button:
        with st.spinner("Ejecutando simulación..."):
            result = run_scenario(scenario)

        st.success(f"Escenario ejecutado: {result.scenario_id}")
        st.code(str(result.output_dir))

        render_pseudo_random_explanation(seed, result.scenario_id)
        render_pseudo_random_panel(seed, scenario)

        kpi_df = load_csv(result.kpi_path)
        cust_df = load_csv(result.customer_log)
        atm_df = load_csv(result.atm_log)
        snap_df = load_csv(result.snapshot_log)

        st.subheader("KPIs de la corrida")
        render_kpis(kpi_df)

        render_atm_status(atm_df)

        render_scenario_comparison(seed)
        render_charts(kpi_df, cust_df, snap_df, seed)
        render_event_timeline(cust_df, snap_df)

        col1, col2 = st.columns(2)
        with col1:
            render_recent_events(cust_df)
        with col2:
            render_snapshots(snap_df)

        st.subheader("Archivos generados")
        st.markdown(
            f"""
- Customer log: `{result.customer_log}`
- ATM log: `{result.atm_log}`
- Snapshot log: `{result.snapshot_log}`
- KPIs: `{result.kpi_path}`
- Event hash: `{result.event_hash}`
"""
        )
    else:
        st.info("Seleccioná un escenario y ejecutá la simulación para ver resultados.")


if __name__ == "__main__":
    main()
