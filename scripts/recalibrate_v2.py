import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

base = "/Users/rendoaltar/Unap/VIII Semester/Simulation/Project I/data"

customer = pd.read_csv(f"{base}/customer_event_log.csv")
system = pd.read_csv(f"{base}/system_snapshot_log.csv")
atm = pd.read_csv(f"{base}/atm_state_log.csv")

# Parse timestamps
customer['arrival_dt'] = pd.to_datetime(customer['arrival_ts'])
for col in ['service_start_ts','service_end_ts','departure_ts','abandon_ts']:
    customer[col] = pd.to_datetime(customer[col], errors='coerce')

system['snapshot_dt'] = pd.to_datetime(system['snapshot_ts'])

atm['state_start_dt'] = pd.to_datetime(atm['state_start_ts'])
atm['state_end_dt'] = pd.to_datetime(atm['state_end_ts'])

# ============================================================
# 0. LIMPIEZA DE DOMINIOS INVÁLIDOS
# ============================================================
# Corregir moderado-alto -> alto (más conservador que eliminar)
customer['peak_composite_level'] = customer['peak_composite_level'].replace('moderado-alto', 'alto')
system['peak_composite_level'] = system['peak_composite_level'].replace('moderado-alto', 'alto')

# ============================================================
# 1. DEFINIR CONTINGENCIAS (más densas, todas representadas)
# ============================================================
dates = sorted(customer['observation_date'].unique())

contingency_types = ['atm_failure', 'cashout', 'maintenance', 'network_issue', 'reduced_service_window']

TYPE_TO_ATM_STATE = {
    'atm_failure': 'falla',
    'cashout': 'cashout',
    'maintenance': 'mantenimiento',
    'network_issue': 'network_issue',
    'reduced_service_window': 'mantenimiento'
}

def random_fail_type():
    return random.choice(['error_lectura_tarjeta','falla_impresion','error_conexion','falla_hardware'])

def random_maint_type():
    return random.choice(['mantenimiento_programado','mantenimiento_urgente','limpieza'])

def random_reduced_type():
    return random.choice(['ventana_reducida','cierre_temprano'])

contingencies = []
# Garantizar que cada tipo aparezca al menos una vez en el dataset
base_types = contingency_types[:]
random.shuffle(base_types)

for i, date in enumerate(dates):
    # Al menos 3, hasta 5 por día
    n_cont = random.randint(3, 5)
    used_starts = []
    day_types = []
    
    # Forzar uno de los tipos base rotativos
    forced = base_types[i % len(base_types)]
    day_types.append(forced)
    # El resto aleatorios
    for _ in range(n_cont - 1):
        day_types.append(random.choice(contingency_types))
    random.shuffle(day_types)
    
    for ctype in day_types:
        duration = random.randint(30, 90)  # minutos, más largas
        start_min = random.randint(480, 1200 - duration)
        attempts = 0
        while any(abs(start_min - s) < duration + 20 for s in used_starts) and attempts < 30:
            start_min = random.randint(480, 1200 - duration)
            attempts += 1
        used_starts.append(start_min)
        
        start_ts = pd.Timestamp(f"{date} 00:00:00") + timedelta(minutes=start_min)
        end_ts = start_ts + timedelta(minutes=duration)
        affected = random.sample([1,2,3,4], k=random.randint(1,2))
        
        contingencies.append({
            'date': date,
            'type': ctype,
            'start_ts': start_ts,
            'end_ts': end_ts,
            'affected_atms': affected,
            'duration_min': duration
        })

cont_df = pd.DataFrame(contingencies)

# ============================================================
# 2. RECALIBRAR SYSTEM SNAPSHOT
# ============================================================

def get_snapshot_contingency(row):
    dt = row['snapshot_dt']
    date = str(dt.date())
    conts = cont_df[(cont_df['date']==date) & (cont_df['start_ts'] <= dt) & (cont_df['end_ts'] > dt)]
    if len(conts) == 0:
        return None, []
    c = conts.iloc[0]
    return c['type'], c['affected_atms']

for idx, row in system.iterrows():
    ctype, affected = get_snapshot_contingency(row)
    
    active = 4
    failed = 0
    cashout = 0
    
    if ctype:
        active = 4 - len(affected)
        if ctype == 'atm_failure':
            failed = len(affected)
        elif ctype == 'cashout':
            cashout = len(affected)
        
        # busy casi siempre máximo en contingencia
        busy = min(active, random.randint(max(0, active-1), active))
        
        if row['peak_flag']:
            queue = random.randint(6, 14)
            blocked = random.randint(1, 6)
            comp_level = random.choice(['alto','critico','critico'])
        else:
            queue = random.randint(3, 9)
            blocked = random.randint(0, 4)
            comp_level = random.choice(['moderado','alto','alto'])
        
        op_type = ctype
    else:
        # Sin contingencia
        op_type = 'none'
        if row['peak_flag']:
            busy = random.randint(2, 4)
            queue = random.randint(1, 6)
            blocked = random.randint(0, 2)
            comp_level = random.choice(['normal','moderado','alto'])
        else:
            busy = random.randint(0, 2)
            queue = random.randint(0, 3)
            blocked = 0
            comp_level = random.choice(['normal','normal','moderado'])
    
    idle = active - busy
    if idle < 0: idle = 0
    
    system.at[idx, 'peak_operational_type'] = op_type
    system.at[idx, 'peak_composite_level'] = comp_level
    system.at[idx, 'active_atm_count'] = active
    system.at[idx, 'busy_atm_count'] = busy
    system.at[idx, 'idle_atm_count'] = idle
    system.at[idx, 'failed_atm_count'] = failed
    system.at[idx, 'cashout_atm_count'] = cashout
    system.at[idx, 'queue_length_total'] = queue
    system.at[idx, 'blocked_arrivals_count'] = blocked

# ============================================================
# 3. RECALIBRAR CUSTOMER EVENT LOG (fricción realista)
# ============================================================

def get_event_contingency(dt):
    date = str(dt.date())
    conts = cont_df[(cont_df['date']==date) & (cont_df['start_ts'] <= dt) & (cont_df['end_ts'] > dt)]
    if len(conts)==0:
        return None, 4
    c = conts.iloc[0]
    return c['type'], 4 - len(c['affected_atms'])

def is_peak_window(dt):
    m = dt.hour*60 + dt.minute
    return (690 <= m <= 839) or (1020 <= m <= 1139)

avg_service = customer['service_time_sec'].mean()

modified_rows = []

for idx, row in customer.iterrows():
    dt = row['arrival_dt']
    ctype, active_atms = get_event_contingency(dt)
    peak = is_peak_window(dt)
    
    # Corregir peak_operational_type inválido
    if row['peak_operational_type'] in ['midday_peak','evening_peak','morning_transition','afternoon_peak','night_low']:
        row['peak_operational_type'] = ctype if ctype else 'none'
    
    # Ajustar composite level
    if ctype:
        row['peak_composite_level'] = random.choice(['alto','critico']) if peak else random.choice(['moderado','alto'])
    else:
        if row['peak_composite_level'] not in ['normal','moderado','alto','critico']:
            row['peak_composite_level'] = 'normal'
    
    # --- Lógica de cola ---
    # En horario pico, la gran mayoría debería entrar a cola porque los ATMs están ocupados
    if peak:
        if not row['queue_entered']:
            # 75% de probabilidad de que entre a cola durante pico
            if random.random() < 0.75:
                row['queue_entered'] = True
    else:
        # Fuera de pico, solo contingencia genera cola significativa
        if ctype and not row['queue_entered']:
            if random.random() < 0.4:
                row['queue_entered'] = True
    
    if row['queue_entered']:
        qpos = row['queue_position_at_arrival']
        if pd.isna(qpos) or qpos < 1:
            qpos = 1
        
        if peak:
            # Aumentar posición de cola drásticamente en pico
            add = random.randint(2, 6)
            qpos = int(qpos) + add
        elif ctype:
            add = random.randint(1, 4)
            qpos = int(qpos) + add
        else:
            # Fuera de pico sin contingencia, cola moderada
            if random.random() < 0.3:
                qpos = int(qpos) + random.randint(1, 2)
        
        # Cap razonable
        if qpos > 12: qpos = 12
        row['queue_position_at_arrival'] = int(qpos)
        
        # Calcular waiting_time realista
        # Tiempo por persona = service_time / active_atms (aprox)
        time_per_person = avg_service / max(active_atms, 1)
        base_wait = qpos * time_per_person
        noise = random.uniform(0.8, 1.6)
        wait = int(base_wait * noise)
        
        # Mínimos de fricción
        if peak and wait < 45:
            wait = random.randint(45, 90)
        elif ctype and wait < 30:
            wait = random.randint(30, 70)
        elif wait < 0:
            wait = 0
        
        # --- Abandonos ---
        abandoned = False
        if peak:
            if qpos >= 7:
                abandoned = random.random() < 0.40
            elif qpos >= 5:
                abandoned = random.random() < 0.25
            elif qpos >= 3:
                abandoned = random.random() < 0.12
            elif wait > 180:
                abandoned = random.random() < 0.18
            elif wait > 90:
                abandoned = random.random() < 0.06
        else:
            if ctype and qpos >= 5:
                abandoned = random.random() < 0.20
            elif ctype and wait > 120:
                abandoned = random.random() < 0.10
            elif wait > 90:
                abandoned = random.random() < 0.04
        
        if abandoned:
            row['abandoned'] = True
            row['served_flag'] = False
            row['loss_flag'] = True
            row['queue_delay_flag'] = True
            row['abandon_reason'] = random.choice([
                'tiempo_espera_excesivo','cliente_impaciente','cola_larga','urgencia_personal'
            ])
            
            # El cliente abandonó antes de completar la espera teórica
            actual_wait = int(wait * random.uniform(0.2, 0.65))
            if actual_wait < 15: actual_wait = random.randint(20, 50)
            row['waiting_time_sec'] = actual_wait
            
            tis = actual_wait + random.randint(5, 30)
            row['time_in_system_sec'] = tis
            row['abandon_ts'] = dt + timedelta(seconds=tis)
            
            row['service_start_ts'] = pd.NaT
            row['service_end_ts'] = pd.NaT
            row['departure_ts'] = pd.NaT
        else:
            row['abandoned'] = False
            row['served_flag'] = True
            row['loss_flag'] = False
            row['abandon_reason'] = ''
            row['abandon_ts'] = pd.NaT
            
            row['waiting_time_sec'] = wait
            row['queue_delay_flag'] = wait > 0
            
            sstart = dt + timedelta(seconds=wait)
            send = sstart + timedelta(seconds=row['service_time_sec'])
            row['service_start_ts'] = sstart
            row['service_end_ts'] = send
            row['departure_ts'] = send
            row['time_in_system_sec'] = wait + row['service_time_sec']
    else:
        # No entró a cola
        row['queue_position_at_arrival'] = 0
        row['waiting_time_sec'] = 0
        row['queue_delay_flag'] = False
        row['time_in_system_sec'] = row['service_time_sec']
        row['service_start_ts'] = dt
        row['service_end_ts'] = dt + timedelta(seconds=row['service_time_sec'])
        row['departure_ts'] = row['service_end_ts']
        row['abandoned'] = False
        row['loss_flag'] = False
        row['abandon_reason'] = ''
        row['abandon_ts'] = pd.NaT
    
    modified_rows.append(row)

customer_rec = pd.DataFrame(modified_rows)

# ============================================================
# 4. RECALIBRAR ATM STATE LOG (división de intervalos)
# ============================================================

atm_records = atm.to_dict('records')

for cont in contingencies:
    ctype = cont['type']
    state = TYPE_TO_ATM_STATE[ctype]
    
    fail_type = random_fail_type() if ctype=='atm_failure' else ''
    maint_type = random_maint_type() if ctype=='maintenance' else (random_reduced_type() if ctype=='reduced_service_window' else '')
    
    for atm_id in cont['affected_atms']:
        c_start = cont['start_ts']
        c_end = cont['end_ts']
        
        to_remove = []
        to_add = []
        
        for i, rec in enumerate(atm_records):
            if rec['atm_id'] != atm_id:
                continue
            r_start = rec['state_start_dt']
            r_end = rec['state_end_dt']
            
            if r_start >= c_end or r_end <= c_start:
                continue
            
            to_remove.append(i)
            
            # Antes
            if r_start < c_start:
                new_rec = rec.copy()
                new_rec['state_end_dt'] = c_start
                new_rec['state_end_ts'] = c_start.strftime('%Y-%m-%d %H:%M:%S')
                to_add.append(new_rec)
            
            # Durante contingencia
            seg_start = max(r_start, c_start)
            seg_end = min(r_end, c_end)
            cont_rec = rec.copy()
            cont_rec['state_start_dt'] = seg_start
            cont_rec['state_start_ts'] = seg_start.strftime('%Y-%m-%d %H:%M:%S')
            cont_rec['state_end_dt'] = seg_end
            cont_rec['state_end_ts'] = seg_end.strftime('%Y-%m-%d %H:%M:%S')
            cont_rec['atm_state'] = state
            cont_rec['failure_flag'] = (ctype == 'atm_failure')
            cont_rec['failure_type'] = fail_type if ctype=='atm_failure' else ''
            cont_rec['maintenance_flag'] = (ctype in ('maintenance','reduced_service_window'))
            cont_rec['maintenance_type'] = maint_type if ctype in ('maintenance','reduced_service_window') else ''
            cont_rec['network_outage_flag'] = (ctype == 'network_issue')
            if ctype == 'cashout':
                cont_rec['cash_available'] = random.randint(0, 300)
            to_add.append(cont_rec)
            
            # Después
            if r_end > c_end:
                new_rec = rec.copy()
                new_rec['state_start_dt'] = c_end
                new_rec['state_start_ts'] = c_end.strftime('%Y-%m-%d %H:%M:%S')
                to_add.append(new_rec)
        
        for i in sorted(to_remove, reverse=True):
            atm_records.pop(i)
        atm_records.extend(to_add)

atm_rec = pd.DataFrame(atm_records)

# ============================================================
# 5. FORMATEO FINAL Y EXPORTACIÓN
# ============================================================

# Formatear timestamps customer: si son NaT dejar string vacío
for col in ['service_start_ts','service_end_ts','departure_ts','abandon_ts']:
    customer_rec[col] = pd.to_datetime(customer_rec[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    customer_rec[col] = customer_rec[col].replace('NaT', '')
    customer_rec[col] = customer_rec[col].fillna('')

# Formatear ATM timestamps
atm_rec['state_start_ts'] = atm_rec['state_start_dt'].dt.strftime('%Y-%m-%d %H:%M:%S')
atm_rec['state_end_ts'] = atm_rec['state_end_dt'].dt.strftime('%Y-%m-%d %H:%M:%S')

# Asegurar tipos enteros donde corresponde
int_cols_cust = ['arrival_second_of_day','arrival_minute_of_day','interarrival_time_sec',
                 'waiting_time_sec','service_time_sec','time_in_system_sec','queue_position_at_arrival']
for c in int_cols_cust:
    if c in customer_rec.columns:
        customer_rec[c] = pd.to_numeric(customer_rec[c], errors='coerce').fillna(0).astype(int)

int_cols_sys = ['snapshot_minute_of_day','queue_length_total','active_atm_count','busy_atm_count',
                'idle_atm_count','failed_atm_count','cashout_atm_count','blocked_arrivals_count']
for c in int_cols_sys:
    if c in system.columns:
        system[c] = pd.to_numeric(system[c], errors='coerce').fillna(0).astype(int)

# Reordenar columnas exactas
customer_rec = customer_rec[customer.columns.tolist()]
system_rec = system[system.columns.tolist()]
atm_rec = atm_rec[atm.columns.tolist()]

# Guardar
customer_rec.to_csv(f"{base}/customer_event_log.csv", index=False)
system_rec.to_csv(f"{base}/system_snapshot_log.csv", index=False)
atm_rec.to_csv(f"{base}/atm_state_log.csv", index=False)

print("=== RECALIBRACIÓN COMPLETA ===")
print(f"Customer rows: {len(customer_rec)}")
print(f"System rows: {len(system_rec)}")
print(f"ATM rows: {len(atm_rec)}")
print(f"\nCustomer avg waiting_time_sec: {customer_rec['waiting_time_sec'].mean():.2f}")
print(f"Customer abandonment rate: {customer_rec['abandoned'].mean()*100:.2f}%")
print(f"Customer queue_entered rate: {customer_rec['queue_entered'].mean()*100:.2f}%")
print(f"Avg queue_position (entered): {customer_rec.loc[customer_rec['queue_entered']==True, 'queue_position_at_arrival'].mean():.2f}")
print("\nSystem peak_operational_type:")
print(system_rec['peak_operational_type'].value_counts())
print("\nATM state distribution:")
print(atm_rec['atm_state'].value_counts())
print("\nCustomer peak_composite_level:")
print(customer_rec['peak_composite_level'].value_counts())
