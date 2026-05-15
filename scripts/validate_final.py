import pandas as pd
import os

base = "/Users/rendoaltar/Unap/VIII Semester/Simulation/Project I/data"

customer = pd.read_csv(f"{base}/customer_event_log.csv")
system = pd.read_csv(f"{base}/system_snapshot_log.csv")
atm = pd.read_csv(f"{base}/atm_state_log.csv")

print("=== VALIDACIÓN DE DOMINIOS ===")

# Dominios esperados
valid_intraday = {'morning_transition','midday_peak','afternoon_peak','evening_peak','night_low'}
valid_payroll = {'inicio_mes','quincena','fin_mes','ninguno'}
valid_operational = {'atm_failure','cashout','maintenance','network_issue','reduced_service_window','none'}
valid_composite = {'normal','moderado','alto','critico'}

c1 = set(customer['peak_intraday_band'].unique()).issubset(valid_intraday)
c2 = set(customer['payroll_cycle_type'].unique()).issubset(valid_payroll)
c3 = set(customer['peak_operational_type'].unique()).issubset(valid_operational)
c4 = set(customer['peak_composite_level'].unique()).issubset(valid_composite)
print(f"Customer intraday OK: {c1} -> {customer['peak_intraday_band'].unique()}")
print(f"Customer payroll OK: {c2} -> {customer['payroll_cycle_type'].unique()}")
print(f"Customer operational OK: {c3} -> {customer['peak_operational_type'].unique()}")
print(f"Customer composite OK: {c4} -> {customer['peak_composite_level'].unique()}")

s1 = set(system['peak_intraday_band'].unique()).issubset(valid_intraday)
s2 = set(system['payroll_cycle_type'].unique()).issubset(valid_payroll)
s3 = set(system['peak_operational_type'].unique()).issubset(valid_operational)
s4 = set(system['peak_composite_level'].unique()).issubset(valid_composite)
print(f"System intraday OK: {s1} -> {system['peak_intraday_band'].unique()}")
print(f"System payroll OK: {s2} -> {system['payroll_cycle_type'].unique()}")
print(f"System operational OK: {s3} -> {system['peak_operational_type'].unique()}")
print(f"System composite OK: {s4} -> {system['peak_composite_level'].unique()}")

# Verificar coherencia de timestamps (no negativos)
customer['arrival_dt'] = pd.to_datetime(customer['arrival_ts'])
customer['service_start_dt'] = pd.to_datetime(customer['service_start_ts'], errors='coerce')
customer['departure_dt'] = pd.to_datetime(customer['departure_ts'], errors='coerce')
customer['abandon_dt'] = pd.to_datetime(customer['abandon_ts'], errors='coerce')

# time_in_system coherente para servidos
served = customer[customer['served_flag']==True].copy()
served['calc_tis'] = (served['departure_dt'] - served['arrival_dt']).dt.total_seconds()
diff_served = (served['time_in_system_sec'] - served['calc_tis']).abs().mean()
print(f"\nAvg diff time_in_system vs departure-arrival (served): {diff_served:.2f}s")

# abandonados: abandon_ts > arrival_ts
aband = customer[customer['abandoned']==True].copy()
aband['calc_tis'] = (aband['abandon_dt'] - aband['arrival_dt']).dt.total_seconds()
diff_aband = (aband['time_in_system_sec'] - aband['calc_tis']).abs().mean()
print(f"Avg diff time_in_system vs abandon-arrival (abandoned): {diff_aband:.2f}s")

# Días de semana
valid_days = {'monday','tuesday','friday'}
days_c = set(customer['day_of_week'].unique())
days_s = set(system['day_of_week'].unique()) if 'day_of_week' in system.columns else set()
print(f"\nCustomer days: {days_c} (valid subset: {days_c.issubset(valid_days)})")
if days_s:
    print(f"System days: {days_s} (valid subset: {days_s.issubset(valid_days)})")

# Volumen
print(f"\nVolumen mantenido: customer={len(customer)}, system={len(system)}, atm={len(atm)}")

# Chequeo cruzado básico: cuando system dice atm_failure, ¿hay fallas en ATM log en esa fecha/hora?
system['snapshot_dt'] = pd.to_datetime(system['snapshot_ts'])
atm['state_start_dt'] = pd.to_datetime(atm['state_start_ts'])
atm['state_end_dt'] = pd.to_datetime(atm['state_end_ts'])

# Tomar una muestra de snapshots con contingencia y verificar overlap con atm log
sample = system[system['peak_operational_type'] != 'none'].sample(5, random_state=42)
print("\n=== MUESTRA DE COHERENCIA CRUZADA ===")
for _, s in sample.iterrows():
    dt = s['snapshot_dt']
    op = s['peak_operational_type']
    # buscar si hay un ATM en ese estado en ese momento
    mask = (atm['state_start_dt'] <= dt) & (atm['state_end_dt'] > dt)
    estados = atm[mask]['atm_state'].unique()
    print(f"Snapshot {s['snapshot_id']} @ {s['snapshot_ts']} type={op} -> ATM states now: {estados}")

print("\nTodo OK.")
