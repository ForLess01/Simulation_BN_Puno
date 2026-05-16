from __future__ import annotations

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from atm_simulator.runner import run_scenario
from atm_simulator.scenarios import scenario_matrix


ROOT = Path(__file__).resolve().parent

CUSTOM_CSS = """
<style>
    .main .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1500px;}
    .hero-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 1.25rem 1.5rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        border: 1px solid #334155;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    }
    .hero-title {font-size: 2rem; font-weight: 800; margin-bottom: 0.25rem;}
    .hero-subtitle {font-size: 1rem; color: #cbd5e1;}
    .mini-kpi {
        background:#f8fafc;
        border:1px solid #e2e8f0;
        border-radius:16px;
        padding:0.85rem 1rem;
        min-height:100px;
    }
    .mini-kpi-title {font-size:0.86rem; color:#64748b; margin-bottom:0.25rem;}
    .mini-kpi-value {font-size:1.45rem; font-weight:800; color:#0f172a;}
</style>
"""


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_bool_text(value) -> str:
    text = str(value).strip().lower()
    if text == "true":
        return "Sí"
    if text == "false":
        return "No"
    return str(value)


def render_live_header(result, scenario, seed: int) -> None:
    st.markdown(
        f"""
<div class="hero-box">
  <div class="hero-title">Simulación ATM BN Puno — {result.scenario_id}</div>
  <div class="hero-subtitle">Seed {seed} · SimPy DES · Visualización operativa, explicativa y comparativa</div>
</div>
""",
        unsafe_allow_html=True,
    )
    cols = st.columns(5)
    info = [
        ("Escenario", result.scenario_id),
        ("Seed", seed),
        ("Branch", scenario.branch_id),
        ("Payroll", scenario.payroll_cycle_type),
        ("Social", scenario.social_transfer_program),
    ]
    for col, (title, value) in zip(cols, info):
        col.markdown(
            f"<div class='mini-kpi'><div class='mini-kpi-title'>{title}</div><div class='mini-kpi-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )


def render_kpis(kpi_df: pd.DataFrame) -> None:
    st.subheader("KPIs de la corrida")
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
            "idle": "#dcfce7",
            "busy": "#fef3c7",
            "cashout": "#fecaca",
            "down_failure": "#fca5a5",
            "down_maintenance": "#c7d2fe",
            "offline": "#e5e7eb",
        }.get(state, "#f3f4f6")

    for col, (_, row) in zip(cols, latest.iterrows()):
        state = row["atm_state"]
        col.markdown(
            f"""
<div style="background:{color_for_state(state)}; padding:14px; border-radius:14px; border:1px solid #cbd5e1; min-height:180px;">
  <h4 style="margin-top:0;">ATM {int(row['atm_id'])}</h4>
  <p><b>Estado:</b> {state}</p>
  <p><b>Efectivo:</b> {row['cash_available']}</p>
  <p><b>Falla:</b> {normalize_bool_text(row['failure_flag'])}</p>
  <p><b>Mantenimiento:</b> {normalize_bool_text(row['maintenance_flag'])}</p>
  <p><b>Red:</b> {normalize_bool_text(row['network_outage_flag'])}</p>
</div>
""",
            unsafe_allow_html=True,
        )


def render_methods_panel(scenario) -> None:
    st.subheader("Métodos aplicados en la corrida")
    method_rows = pd.DataFrame(
        [
            ["Llegadas", "Proceso de Poisson / interarribos exponenciales", f"λ ajustada por franja y multiplicador {scenario.pressure_lambda_multiplier}"],
            ["Servicio", "Distribución positiva (base exponencial / referencia M/G/4)", f"media base {scenario.distributions.service_mean_sec} s"],
            ["Abandono", "Umbral + componente probabilística", f"umbral {scenario.distributions.abandonment_threshold_sec} s"],
            ["Contingencias", "Activación pseudoaleatoria + overrides de escenario", str(scenario.contingency_overrides or {})],
            ["Snapshots", "Monitoreo discreto periódico", "intervalo por configuración del simulador"],
        ],
        columns=["Componente", "Método", "Parámetro/interpretación"],
    )
    st.dataframe(method_rows, width="stretch", hide_index=True)


def render_recent_events(customer_df: pd.DataFrame) -> None:
    st.subheader("Eventos recientes de clientes")
    if customer_df.empty:
        st.info("No hay eventos de cliente disponibles.")
        return

    preview_cols = [
        c for c in [
            "event_id", "arrival_ts", "transaction_type", "queue_entered",
            "queue_position_at_arrival", "abandoned", "abandon_reason",
            "atm_id", "peak_intraday_band", "waiting_time_sec", "service_time_sec"
        ] if c in customer_df.columns
    ]
    preview = customer_df[preview_cols].tail(20).copy()
    if "atm_id" in preview.columns:
        preview["atm_id"] = preview["atm_id"].fillna("").apply(lambda x: "" if x == "" else str(int(float(x))) if str(x).replace('.', '', 1).isdigit() else str(x))
    for col in ["queue_entered", "abandoned"]:
        if col in preview.columns:
            preview[col] = preview[col].apply(normalize_bool_text)
    st.dataframe(preview, width="stretch", hide_index=True)


def render_snapshots(snapshot_df: pd.DataFrame) -> None:
    st.subheader("Snapshots del sistema")
    if snapshot_df.empty:
        st.info("No hay snapshots disponibles.")
        return
    preview_cols = [
        c for c in [
            "snapshot_ts", "hour_block", "queue_length_total", "active_atm_count",
            "busy_atm_count", "idle_atm_count", "failed_atm_count", "cashout_atm_count",
            "peak_operational_type", "peak_composite_level"
        ] if c in snapshot_df.columns
    ]
    preview = snapshot_df[preview_cols].tail(20).copy()
    st.dataframe(preview, width="stretch", hide_index=True)


def render_pseudo_random_panel(seed: int, scenario) -> None:
    st.subheader("Pseudoazar visible y aplicado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Seed", seed)
    c2.metric("Multiplicador λ", scenario.pressure_lambda_multiplier)
    c3.metric("Interarribo base (s)", scenario.distributions.interarrival_mean_sec)

    rng = np.random.default_rng(seed)
    uniform_arrival = float(rng.uniform(0, 1))
    interarrival_mean = scenario.distributions.interarrival_mean_sec / max(scenario.pressure_lambda_multiplier, 0.1)
    exp_example = -interarrival_mean * np.log(1 - uniform_arrival)

    uniform_abandon = float(rng.uniform(0, 1))
    abandon_p = min(0.95, scenario.distributions.abandonment_base_probability + 0.15)
    decision = "abandona" if uniform_abandon < abandon_p else "permanece"

    left, right = st.columns(2)
    left.markdown("**Ejemplo de interarribo**")
    left.code(f"U = {uniform_arrival:.4f}\nmedia ajustada = {interarrival_mean:.2f} s\nT = -media * ln(1-U) = {exp_example:.2f} s")
    right.markdown("**Ejemplo de decisión de abandono**")
    right.code(f"U = {uniform_abandon:.4f}\np = {abandon_p:.4f}\nResultado: el cliente {decision}")

    st.markdown(
        "Este panel muestra cómo un número pseudoaleatorio puede transformarse en un interarribo o en una decisión de abandono dentro del modelo estocástico."
    )


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
    cols = ["scenario_id", "arrivals_total", "wq_mean_sec", "loss_rate", "queue_max", "minutes_capacity_reduced"]
    st.dataframe(df[[c for c in cols if c in df.columns]].sort_values("scenario_id"), width="stretch", hide_index=True)


def render_charts(customer_df: pd.DataFrame, snapshot_df: pd.DataFrame, seed: int) -> None:
    st.subheader("Gráficos analíticos")
    if not customer_df.empty:
        arrivals_by_band = customer_df.groupby("peak_intraday_band").size().reset_index(name="arrivals")
        band_chart = alt.Chart(arrivals_by_band).mark_bar().encode(
            x=alt.X("peak_intraday_band:N", title="Banda intradía"),
            y=alt.Y("arrivals:Q", title="Llegadas"),
            color=alt.Color("peak_intraday_band:N", legend=None,
                            scale=alt.Scale(range=["#60a5fa", "#2563eb", "#0ea5e9", "#f59e0b", "#6b7280"]))
        )
        st.markdown("**Llegadas por banda intradía**")
        st.altair_chart(band_chart, width="stretch")

        if "arrival_minute_of_day" in customer_df.columns:
            minute_series = customer_df.groupby("arrival_minute_of_day").size().reset_index(name="arrivals")
            minute_chart = alt.Chart(minute_series).mark_line(color="#7c3aed").encode(
                x=alt.X("arrival_minute_of_day:Q", title="Minuto del día"),
                y=alt.Y("arrivals:Q", title="Llegadas por minuto")
            )
            st.markdown("**Intensidad de llegadas por minuto del día**")
            st.altair_chart(minute_chart, width="stretch")

    if not snapshot_df.empty and "queue_length_total" in snapshot_df.columns:
        snap_df = snapshot_df.copy()
        snap_df["snapshot_ts"] = pd.to_datetime(snap_df["snapshot_ts"])
        queue_chart = alt.Chart(snap_df).mark_line(point=True, color="#dc2626").encode(
            x=alt.X("snapshot_ts:T", title="Tiempo"),
            y=alt.Y("queue_length_total:Q", title="Longitud de cola")
        )
        st.markdown("**Evolución temporal de la cola**")
        st.altair_chart(queue_chart, width="stretch")

        capacity_chart = alt.Chart(snap_df).mark_line(point=True, color="#059669").encode(
            x=alt.X("snapshot_ts:T", title="Tiempo"),
            y=alt.Y("active_atm_count:Q", title="ATM activos")
        )
        st.markdown("**Evolución temporal de la capacidad activa**")
        st.altair_chart(capacity_chart, width="stretch")

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
                chart = alt.Chart(comp).mark_bar().encode(
                    x=alt.X("scenario_id:N", title="Escenario"),
                    y=alt.Y(f"{metric}:Q", title=metric),
                    color=alt.Color("scenario_id:N", legend=None, scale=alt.Scale(scheme="tableau20")),
                )
                st.markdown(f"**Comparativa por escenario: {metric}**")
                st.altair_chart(chart, width="stretch")

        if all(m in comp.columns for m in ["queue_max", "minutes_capacity_reduced"]):
            comp_long = comp[["scenario_id", "queue_max", "minutes_capacity_reduced"]].melt(id_vars="scenario_id", var_name="metric", value_name="value")
            combo = alt.Chart(comp_long).mark_bar().encode(
                x=alt.X("scenario_id:N", title="Escenario"),
                y=alt.Y("value:Q", title="Valor"),
                color=alt.Color("metric:N", scale=alt.Scale(range=["#059669", "#ef4444"])),
                xOffset="metric:N",
            )
            st.markdown("**Comparativa de cola máxima y reducción de capacidad**")
            st.altair_chart(combo, width="stretch")


def render_event_timeline(customer_df: pd.DataFrame, snapshot_df: pd.DataFrame) -> None:
    st.subheader("Timeline de la corrida")
    if customer_df.empty:
        st.info("No hay datos suficientes para construir timeline.")
        return

    customer_timeline = customer_df[["arrival_ts", "event_id", "transaction_type", "abandoned", "atm_id", "queue_position_at_arrival", "waiting_time_sec"]].copy()
    customer_timeline["timestamp"] = pd.to_datetime(customer_timeline["arrival_ts"])
    customer_timeline["kind"] = "arrival"
    customer_timeline["detail"] = customer_timeline.apply(
        lambda r: f"{r['event_id']} | op={r['transaction_type']} | ATM={'' if pd.isna(r['atm_id']) else int(float(r['atm_id']))} | cola={int(r['queue_position_at_arrival']) if not pd.isna(r['queue_position_at_arrival']) else 0} | espera={int(float(r['waiting_time_sec'])) if not pd.isna(r['waiting_time_sec']) else 0}s | abandono={normalize_bool_text(r['abandoned'])}",
        axis=1,
    )
    frames = [customer_timeline[["timestamp", "kind", "detail"]]]

    if not snapshot_df.empty:
        snap_timeline = snapshot_df[["snapshot_ts", "queue_length_total", "peak_operational_type", "peak_composite_level"]].copy()
        snap_timeline["timestamp"] = pd.to_datetime(snap_timeline["snapshot_ts"])
        snap_timeline["kind"] = "snapshot"
        snap_timeline["detail"] = snap_timeline.apply(
            lambda r: f"queue={r['queue_length_total']} | oper={r['peak_operational_type']} | presión={r['peak_composite_level']}",
            axis=1,
        )
        frames.append(snap_timeline[["timestamp", "kind", "detail"]])

    timeline = pd.concat(frames).sort_values("timestamp").tail(60).copy()
    st.dataframe(timeline, width="stretch", hide_index=True)


def render_active_simulation_view(customer_df: pd.DataFrame, snapshot_df: pd.DataFrame, atm_df: pd.DataFrame) -> None:
    st.subheader("Simulación activa")
    if customer_df.empty or snapshot_df.empty:
        st.info("No hay datos suficientes para construir la vista activa.")
        return

    snap_df = snapshot_df.copy()
    snap_df["snapshot_ts"] = pd.to_datetime(snap_df["snapshot_ts"])
    options = snap_df["snapshot_ts"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()

    if "timeline_index" not in st.session_state:
        st.session_state.timeline_index = min(len(options) - 1, len(options) // 2)

    cprev, cslider, cnext = st.columns([1, 6, 1])
    with cprev:
        if st.button("⏮", key="prev_ts"):
            st.session_state.timeline_index = max(0, st.session_state.timeline_index - 1)
    with cnext:
        if st.button("⏭", key="next_ts"):
            st.session_state.timeline_index = min(len(options) - 1, st.session_state.timeline_index + 1)
    with cslider:
        selected = st.select_slider("Explorar instante de simulación", options=options, value=options[st.session_state.timeline_index], key="timeline_slider")
        st.session_state.timeline_index = options.index(selected)

    selected_ts = pd.to_datetime(selected)
    current_snap = snap_df[snap_df["snapshot_ts"] == selected_ts].iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cola actual", int(current_snap["queue_length_total"]))
    c2.metric("ATM activos", int(current_snap["active_atm_count"]))
    c3.metric("ATM ocupados", int(current_snap["busy_atm_count"]))
    c4.metric("Capacidad reducida", int(current_snap["failed_atm_count"]) + int(current_snap["cashout_atm_count"]))

    st.markdown(
        f"""
**Instante seleccionado:** `{selected}`  
**Presión operativa:** `{current_snap['peak_operational_type']}`  
**Presión compuesta:** `{current_snap['peak_composite_level']}`
"""
    )

    col_events, col_atm = st.columns(2)
    with col_events:
        st.markdown("**Eventos de cliente cercanos**")
        cust = customer_df.copy()
        cust["arrival_ts_dt"] = pd.to_datetime(cust["arrival_ts"])
        near = cust[(cust["arrival_ts_dt"] <= selected_ts)].sort_values("arrival_ts_dt").tail(10).copy()
        if not near.empty:
            if "atm_id" in near.columns:
                near["atm_id"] = near["atm_id"].fillna("").apply(lambda x: "" if x == "" else str(int(float(x))) if str(x).replace('.', '', 1).isdigit() else str(x))
            near["abandoned"] = near["abandoned"].apply(normalize_bool_text)
            st.dataframe(near[[c for c in ["event_id", "arrival_ts", "transaction_type", "atm_id", "queue_position_at_arrival", "waiting_time_sec", "abandoned"] if c in near.columns]], width="stretch", hide_index=True)
    with col_atm:
        st.markdown("**Segmentos ATM cercanos**")
        if not atm_df.empty and "state_start_ts" in atm_df.columns:
            at = atm_df.copy()
            at["state_start_ts_dt"] = pd.to_datetime(at["state_start_ts"])
            near_atm = at[(at["state_start_ts_dt"] <= selected_ts)].sort_values("state_start_ts_dt").tail(12)
            st.dataframe(near_atm[[c for c in ["atm_id", "state_start_ts", "state_end_ts", "atm_state", "failure_type", "maintenance_type"] if c in near_atm.columns]], width="stretch", hide_index=True)


def render_interpretation_panel(kpi_df: pd.DataFrame, scenario_id: str) -> None:
    st.subheader("Interpretación automática de la corrida")
    if kpi_df.empty:
        return
    row = kpi_df.iloc[0]
    arrivals = int(row.get("arrivals_total", 0))
    wait = float(row.get("wq_mean_sec", 0))
    loss = float(row.get("loss_rate", 0))
    reduced = int(row.get("minutes_capacity_reduced", 0))

    notes = []
    if wait > 35:
        notes.append("La corrida presenta tiempos de espera relativamente altos, lo que sugiere presión significativa sobre la capacidad del sistema.")
    elif wait > 15:
        notes.append("La espera promedio es moderada, compatible con una operación cargada pero aún funcional.")
    else:
        notes.append("La espera promedio es baja, lo que indica una corrida con menor fricción de cola.")

    if loss > 0.4:
        notes.append("La tasa de pérdida es elevada, lo que sugiere saturación o restricciones operativas fuertes.")
    elif loss > 0.2:
        notes.append("La pérdida es relevante y debe analizarse junto con la cola y la capacidad reducida.")
    else:
        notes.append("La pérdida es relativamente contenida dentro de la corrida simulada.")

    if reduced > 0:
        notes.append(f"Se registraron {reduced} minutos con capacidad reducida, lo que indica impacto operativo explícito del escenario.")

    st.markdown(
        f"""
**Escenario:** `{scenario_id}`  
**Llegadas simuladas:** `{arrivals}`
"""
    )
    for note in notes:
        st.markdown(f"- {note}")


def main() -> None:
    st.set_page_config(page_title="ATM SimPy Simulator", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.title("Simulación ATM BN Puno — Dashboard explicativo")
    st.caption("Interfaz visual de la corrida, sus métodos estocásticos, sus eventos y sus resultados operativos.")

    st.sidebar.header("Control de simulación")
    seed = st.sidebar.number_input("Seed", min_value=1, value=42, step=1)
    scenario_id = st.sidebar.selectbox("Escenario", options=list(scenario_matrix(seed).keys()))
    run_button = st.sidebar.button("Ejecutar simulación")

    scenario_map = scenario_matrix(seed)
    scenario = scenario_map[scenario_id]

    if "simulation_result" not in st.session_state:
        st.session_state.simulation_result = None
        st.session_state.simulation_seed = None
        st.session_state.simulation_scenario = None

    st.sidebar.markdown("### Resumen del escenario")
    st.sidebar.write(f"ID: `{scenario.scenario_id}`")
    st.sidebar.write(f"Duración (s): `{scenario.duration_sec}`")
    st.sidebar.write(f"Branch: `{scenario.branch_id}`")
    st.sidebar.write(f"Payroll: `{scenario.payroll_cycle_type}`")
    st.sidebar.write(f"Social transfer: `{scenario.social_transfer_program}`")

    if run_button:
        with st.spinner("Ejecutando simulación..."):
            result = run_scenario(scenario)
        st.session_state.simulation_result = {
            "scenario_id": result.scenario_id,
            "output_dir": str(result.output_dir),
            "customer_log": str(result.customer_log),
            "atm_log": str(result.atm_log),
            "snapshot_log": str(result.snapshot_log),
            "kpi_path": str(result.kpi_path),
            "event_hash": result.event_hash,
        }
        st.session_state.simulation_seed = seed
        st.session_state.simulation_scenario = scenario_id

    stored = st.session_state.simulation_result
    if stored is not None:
        current_seed = st.session_state.simulation_seed
        current_scenario_id = st.session_state.simulation_scenario
        current_scenario = scenario_matrix(current_seed)[current_scenario_id]

        class _Result:
            pass

        result = _Result()
        result.scenario_id = stored["scenario_id"]
        result.output_dir = Path(stored["output_dir"])
        result.customer_log = Path(stored["customer_log"])
        result.atm_log = Path(stored["atm_log"])
        result.snapshot_log = Path(stored["snapshot_log"])
        result.kpi_path = Path(stored["kpi_path"])
        result.event_hash = stored["event_hash"]

        render_live_header(result, current_scenario, current_seed)
        st.success(f"Escenario ejecutado: {result.scenario_id}")
        st.code(str(result.output_dir))

        kpi_df = load_csv(result.kpi_path)
        cust_df = load_csv(result.customer_log)
        atm_df = load_csv(result.atm_log)
        snap_df = load_csv(result.snapshot_log)

        render_kpis(kpi_df)
        render_methods_panel(current_scenario)
        render_pseudo_random_panel(current_seed, current_scenario)
        render_atm_status(atm_df)
        render_active_simulation_view(cust_df, snap_df, atm_df)
        render_scenario_comparison(current_seed)
        render_charts(cust_df, snap_df, current_seed)
        render_event_timeline(cust_df, snap_df)
        render_interpretation_panel(kpi_df, result.scenario_id)

        c1, c2 = st.columns(2)
        with c1:
            render_recent_events(cust_df)
        with c2:
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
        st.info("Seleccioná un escenario y ejecutá la simulación para visualizar la corrida.")


if __name__ == "__main__":
    main()
