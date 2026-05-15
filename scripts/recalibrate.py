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
# 1. DEFINIR CONTINGENCIAS
# ============================================================
# Días únicos
dates = sorted(customer['observation_date'].unique())

contingency_types = ['atm_failure', 'cashout', 'maintenance', 'network_issue', 'reduced_service_window']

# Mapeo a estado ATM y flags
TYPE_TO_ATM_STATE = {
    'atm_failure': 'falla',
    'cashout': 'cashout',
    'maintenance': 'mantenimiento',
    'network_issue': 'network_issue',
    'reduced_service_window': 'mantenimiento'
}
TYPE_TO_FAILURE_TYPE = {
    'atm_failure': random.choice(['error_lectura_tarjeta','falla_impresion','error_conexion','falla_hardware']),
    'cashout': '',
    'maintenance': '',
    'network_issue': '',
    'reduced_service_window': ''
}
TYPE_TO_MAINT_TYPE = {
    'atm_failure': '',
    'cashout': '',
    'maintenance': random.choice(['mantenimiento_programado','mantenimiento_urgente','limpieza']),
    'network_issue': '',
    'reduced_service_window': random.choice(['ventana_reducida','cierre_temprano'])
}

contingencies = []
for date in dates:
    n_cont = random.randint(1, 3)
    used_starts = set()
    for _ in range(n_cont):
        ctype = random.choice(contingency_types)
        duration = random.randint(25, 80)  # minutos
        # Horario comercial 08:00 - 20:00
        start_min = random.randint(480, 1200 - duration)
        # Evitar solapamientos muy cercanos en el mismo día
        attempts = 0
        while any(abs(start_min - s) < duration + 15 for s in used_starts) and attempts < 20:
            start_min = random.randint(480, 1200 - duration)
            attempts += 1
        used_starts.add(start_min)
        
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
# Función para saber qué contingencias afectan un snapshot
snapshot_contingency_cache = {}

def get_snapshot_contingency(row):
    key = row['snapshot_ts']
    if key in snapshot_contingency_cache:
        return snapshot_contingency_cache[key]
    dt = row['snapshot_dt']
    date = str(dt.date())
    conts = cont_df[(cont_df['date']==date) & (cont_df['start_ts'] <= dt) & (cont_df['end_ts'] > dt)]
    if len(conts) == 0:
        snapshot_contingency_cache[key] = (None, [])
        return None, []
    # Si hay múltiples, tomar la primera (raro)
    c = conts.iloc[0]
    snapshot_contingency_cache[key] = (c['type'], c['affected_atms'])
    return c['type'], c['affected_atms']

# Aplicar
for idx, row in system.iterrows():
    ctype, affected = get_snapshot_contingency(row)
    
    # Reset base: 4 ATMs totales
    active = 4
    failed = 0
    cashout = 0
    busy = row['busy_atm_count']
    queue = row['queue_length_total']
    blocked = row['blocked_arrivals_count']
    comp_level = row['peak_composite_level']
    op_type = 'none'
    
    if ctype:
        op_type = ctype
        # Reducir ATMs activos
        active = 4 - len(affected)
        if ctype == 'atm_failure':
            failed = len(affected)
        elif ctype == 'cashout':
            cashout = len(affected)
        elif ctype in ('maintenance','reduced_service_window','network_issue'):
            # No se contabilizan como failed ni cashout, pero bajan active
            pass
        
        # Ajustar busy: en contingencia, los ATMs restantes suelen estar más cargados
        busy = min(active, max(busy, active - random.randint(0,1)))
        
        # Aumentar cola considerablemente si es pico + contingencia
        if row['peak_flag']:
            queue = max(queue, random.randint(4, 12))
            blocked = random.randint(0, 5)
            comp_level = random.choice(['alto','critico'])
        else:
            queue = max(queue, random.randint(2, 7))
            blocked = random.randint(0, 3)
            if comp_level == 'normal':
                comp_level = random.choice(['moderado','alto'])
    else:
        # Sin contingencia: ajustar busy para que no sea siempre 1 en off-peak
        if row['peak_flag']:
            busy = min(4, max(busy, random.randint(2,4)))
            queue = max(queue, random.randint(1, 5))
        else:
            busy = min(4, max(busy, random.randint(0,2)))
            queue = max(queue, random.randint(0, 3))
    
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
# 3. RECALIBRAR CUSTOMER EVENT LOG
# ============================================================
# Función helper para contingencias que afectan un momento dado
def get_event_contingency(dt):
    date = str(dt.date())
    conts = cont_df[(cont_df['date']==date) & (cont_df['start_ts'] <= dt) & (cont_df['end_ts'] > dt)]
    if len(conts)==0:
        return None, 4
    c = conts.iloc[0]
    active = 4 - len(c['affected_atms'])
    return c['type'], active

# Promedio de service_time para estimar waits
avg_service = customer['service_time_sec'].mean()

def is_peak_window(dt):
    m = dt.hour*60 + dt.minute
    return (690 <= m <= 839) or (1020 <= m <= 1139)  # 11:30-13:59 y 17:00-18:59

new_rows = []  # para guardar modificados

for idx, row in customer.iterrows():
    dt = row['arrival_dt']
    ctype, active_atms = get_event_contingency(dt)
    
    # Corregir peak_operational_type inválido
    if row['peak_operational_type'] in ['midday_peak','evening_peak']:
        row['peak_operational_type'] = ctype if ctype else 'none'
    
    # Ajustar peak_composite_level si hay contingencia
    if ctype:
        if row['peak_flag']:
            row['peak_composite_level'] = random.choice(['alto','critico'])
        else:
            if row['peak_composite_level'] == 'normal':
                row['peak_composite_level'] = random.choice(['moderado','alto'])
    
    # --- Recalibrar waiting_time y queue_position ---
    if row['queue_entered'] == True:
        qpos = row['queue_position_at_arrival']
        
        # Si está en pico, forzar queue_position más alta para muchos
        if is_peak_window(dt):
            if qpos < 1 or pd.isna(qpos):
                qpos = random.randint(1, 5)
            else:
                # Aumentar con probabilidad
                if random.random() < 0.6:
                    qpos = min(10, qpos + random.randint(1, 4))
        else:
            # Fuera de pico, mantener o ligero aumento si hay contingencia
            if ctype and qpos < 1:
                qpos = random.randint(1, 3)
        
        row['queue_position_at_arrival'] = int(qpos)
        
        # Calcular waiting_time coherente
        # wait ≈ posición * (tiempo_servicio_prom / ATMs_activos)
        base_wait = qpos * (avg_service / max(active_atms, 1))
        noise = random.uniform(0.7, 1.4)
        wait = int(base_wait * noise)
        if wait < 0: wait = 0
        
        # En pico, mínimo de fricción
        if is_peak_window(dt) and wait < 20:
            wait = random.randint(20, 60)
        
        # --- Abandonos ---
        abandoned = False
        abandon_reason = ''
        
        # Probabilidad de abandono
        if is_peak_window(dt):
            if qpos >= 5:
                abandoned = random.random() < 0.30
            elif qpos >= 3:
                abandoned = random.random() < 0.15
            elif wait > 180:
                abandoned = random.random() < 0.20
            elif wait > 90:
                abandoned = random.random() < 0.08
        else:
            if ctype and qpos >= 4:
                abandoned = random.random() < 0.12
            elif wait > 120:
                abandoned = random.random() < 0.05
        
        if abandoned:
            row['abandoned'] = True
            row['served_flag'] = False
            row['loss_flag'] = True
            row['queue_delay_flag'] = True
            abandon_reason = random.choice(['tiempo_espera_excesivo','cliente_impaciente','cola_larga','urgencia_personal'])
            row['abandon_reason'] = abandon_reason
            
            # No esperó el tiempo completo calculado; abandonó antes
            actual_wait = int(wait * random.uniform(0.25, 0.75))
            if actual_wait < 10: actual_wait = random.randint(15, 45)
            row['waiting_time_sec'] = actual_wait
            
            tis = actual_wait + random.randint(10, 40)  # time in system hasta que se fue
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
    
    new_rows.append(row)

customer_rec = pd.DataFrame(new_rows)

# ============================================================
# 4. RECALIBRAR ATM STATE LOG
# ============================================================
# Dividir registros busy que se solapan con contingencias
atm_records = atm.to_dict('records')
new_atm_records = []

for cont in contingencies:
    ctype = cont['type']
    state = TYPE_TO_ATM_STATE[ctype]
    fail_type = TYPE_TO_FAILURE_TYPE[ctype] if ctype=='atm_failure' else ''
    maint_type = TYPE_TO_MAINT_TYPE[ctype] if ctype in ('maintenance','reduced_service_window') else ''
    
    for atm_id in cont['affected_atms']:
        c_start = cont['start_ts']
        c_end = cont['end_ts']
        
        # Buscar registros de este ATM que se solapan
        to_remove = []
        to_add = []
        
        for i, rec in enumerate(atm_records):
            if rec['atm_id'] != atm_id:
                continue
            r_start = rec['state_start_dt']
            r_end = rec['state_end_dt']
            
            if r_start >= c_end or r_end <= c_start:
                continue  # no solapamiento
            
            to_remove.append(i)
            
            # Segmento antes de la contingencia (busy original)
            if r_start < c_start:
                new_rec = rec.copy()
                new_rec['state_end_dt'] = c_start
                new_rec['state_end_ts'] = c_start.strftime('%Y-%m-%d %H:%M:%S')
                # Recalcular duración implícita? No hay columna de duración.
                to_add.append(new_rec)
            
            # Segmento de contingencia
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
                cont_rec['cash_available'] = random.randint(0, 500)
            elif ctype == 'network_issue':
                cont_rec['cash_available'] = rec['cash_available']  # sin cambio
            elif ctype in ('atm_failure','maintenance','reduced_service_window'):
                cont_rec['cash_available'] = rec['cash_available']
            to_add.append(cont_rec)
            
            # Segmento después de la contingencia (busy original)
            if r_end > c_end:
                new_rec = rec.copy()
                new_rec['state_start_dt'] = c_end
                new_rec['state_start_ts'] = c_end.strftime('%Y-%m-%d %H:%M:%S')
                to_add.append(new_rec)
        
        # Remover en orden inverso para no desfasar índices
        for i in sorted(to_remove, reverse=True):
            atm_records.pop(i)
        
        atm_records.extend(to_add)

atm_rec = pd.DataFrame(atm_records)

# ============================================================
# 5. FORMATEO Y EXPORTACIÓN
# ============================================================
# Restaurar formato de timestamps string exacto YYYY-MM-DD HH:MM:SS
for col in ['service_start_ts','service_end_ts','departure_ts','abandon_ts']:
    customer_rec[col] = pd.to_datetime(customer_rec[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
    customer_rec[col] = customer_rec[col].replace('NaT', '')
    # Algunos pueden quedar como NaN, reemplazar por string vacío
    customer_rec[col] = customer_rec[col].fillna('')

# Asegurar tipos de bool/enteros limpios
bool_cols = ['peak_flag','peak_social_transfer_flag','queue_delay_flag','loss_flag','queue_entered','abandoned','served_flag','blocked_by_closed_hours']
for c in bool_cols:
    if c in customer_rec.columns:
        customer_rec[c] = customer_rec[c].astype(bool)

int_cols_cust = ['waiting_time_sec','service_time_sec','time_in_system_sec','queue_position_at_arrival']
for c in int_cols_cust:
    customer_rec[c] = customer_rec[c].astype(int)

# ATM timestamps
for col in ['state_start_ts','state_end_ts']:
    atm_rec[col] = atm_rec['state_start_dt'].dt.strftime('%Y-%m-%d %H:%M:%S') if col=='state_start_ts' else atm_rec['state_end_dt'].dt.strftime('%Y-%m-%d %H:%M:%S')

# Reordenar columnas exactas como original
customer_rec = customer_rec[customer.columns.tolist()]
system_rec = system[system.columns.tolist()]
atm_rec = atm_rec[atm.columns.tolist()]

# Guardar
customer_rec.to_csv(f"{base}/customer_event_log.csv", index=False)
system_rec.to_csv(f"{base}/system_snapshot_log.csv", index=False)
atm_rec.to_csv(f"{base}/atm_state_log.csv", index=False)

print("Recalibración completa. Archivos guardados.")
print(f"Customer rows: {len(customer_rec)}")
print(f"System rows: {len(system_rec)}")
print(f"ATM rows: {len(atm_rec)}")

# Quick stats
print("\n=== POST-RECAL STATS ===")
print("Customer avg wait:", customer_rec['waiting_time_sec'].mean())
print("Customer abandonment rate:", customer_rec['abandoned'].mean()*100, "%")
print("System operational types:\n", system_rec['peak_operational_type'].value_counts())
print("ATM state dist:\n", atm_rec['atm_state'].value_counts())
