import pandas as pd
import os

base = "/Users/rendoaltar/Unap/VIII Semester/Simulation/Project I/data"

customer = pd.read_csv(os.path.join(base, "customer_event_log.csv"))
system = pd.read_csv(os.path.join(base, "system_snapshot_log.csv"))
atm = pd.read_csv(os.path.join(base, "atm_state_log.csv"))

print("=== CUSTOMER EVENT LOG ===")
print(f"Rows: {len(customer)}")
print(f"Cols: {list(customer.columns)}")
print(f"Avg waiting_time_sec: {customer['waiting_time_sec'].mean():.2f}")
print(f"Max waiting_time_sec: {customer['waiting_time_sec'].max()}")
print(f"queue_entered=True: {customer['queue_entered'].sum()} ({customer['queue_entered'].mean()*100:.1f}%)")
print(f"abandoned=True: {customer['abandoned'].sum()} ({customer['abandoned'].mean()*100:.1f}%)")
print(f"Avg queue_position (when entered): {customer.loc[customer['queue_entered']==True, 'queue_position_at_arrival'].mean():.2f}")
print(f"Peak flag true: {customer['peak_flag'].sum()} ({customer['peak_flag'].mean()*100:.1f}%)")
print("Hour block dist:\n", customer['hour_block'].value_counts().sort_index())
print("Peak intraday band dist:\n", customer['peak_intraday_band'].value_counts())
print("Peak operational type dist:\n", customer['peak_operational_type'].value_counts())
print("Peak composite level dist:\n", customer['peak_composite_level'].value_counts())
print("Abandon reasons:\n", customer['abandon_reason'].value_counts(dropna=False))

print("\n=== SYSTEM SNAPSHOT LOG ===")
print(f"Rows: {len(system)}")
print(f"Cols: {list(system.columns)}")
print("Peak operational type dist:\n", system['peak_operational_type'].value_counts())
print("Peak composite level dist:\n", system['peak_composite_level'].value_counts())
print(f"Avg queue_length_total: {system['queue_length_total'].mean():.2f}")
print(f"Max queue_length_total: {system['queue_length_total'].max()}")
print(f"Avg failed_atm_count: {system['failed_atm_count'].mean():.2f}")
print(f"Avg cashout_atm_count: {system['cashout_atm_count'].mean():.2f}")
print(f"Avg blocked_arrivals_count: {system['blocked_arrivals_count'].mean():.2f}")

print("\n=== ATM STATE LOG ===")
print(f"Rows: {len(atm)}")
print(f"Cols: {list(atm.columns)}")
print("ATM state dist:\n", atm['atm_state'].value_counts())
print(f"failure_flag=True: {atm['failure_flag'].sum()} ({atm['failure_flag'].mean()*100:.1f}%)")
print(f"maintenance_flag=True: {atm['maintenance_flag'].sum()} ({atm['maintenance_flag'].mean()*100:.1f}%)")
print(f"network_outage_flag=True: {atm['network_outage_flag'].sum()} ({atm['network_outage_flag'].mean()*100:.1f}%)")
print("Failure types:\n", atm['failure_type'].value_counts(dropna=False))
print("Maintenance types:\n", atm['maintenance_type'].value_counts(dropna=False))
