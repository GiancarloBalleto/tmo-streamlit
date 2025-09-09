# tiempo_sin_gestion_app.py
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta, time
import math

# ========= Helpers =========

from streamlit.components.v1 import html as st_html

def render_gestor_cards(df_resumen, total_min, top_n=None, key="gestor"):
    """Renderiza tarjetas bonitas por Gestor usando un componente HTML (sin que Streamlit las escape)."""
    if df_resumen is None or df_resumen.empty:
        st.info("No hay datos para mostrar tarjetas.")
        return

    df_show = df_resumen.sort_values("minutos_sin_gestion", ascending=False).copy()
    if top_n is not None:
        df_show = df_show.head(top_n)

    # Cálculo de alto del iframe en función de cuántas cards hay
    n = len(df_show)
    cols = 4   # hasta 4 columnas responsivas
    rows = math.ceil(n / cols)
    height = 170 * rows + 40  # alto aproximado (ajusta si quieres más compacto / alto)

    # CSS scopeado con un id único para evitar colisiones
    root_id = f"cards-{key}"
    styles = f"""
    <style>
      #{root_id} {{
        font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji','Segoe UI Emoji';
      }}
      #{root_id} .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 14px;
      }}
      #{root_id} .card {{
        background: #fff;
        border: 1px solid #e9eef5;
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 6px 18px rgba(17, 24, 39, 0.06);
      }}
      #{root_id} .name {{
        font-weight: 600; font-size: 0.95rem; color: #111827; letter-spacing: .2px;
        margin-bottom: 4px;
      }}
      #{root_id} .value {{
        font-weight: 800; font-size: 1.6rem; margin: 6px 0 8px 0;
      }}
      #{root_id} .muted {{ color:#64748b; font-size:12px; margin-left:6px; }}
      #{root_id} .bar {{ height: 8px; width: 100%; background:#eef2f7; border-radius:999px; overflow:hidden; margin:2px 0 8px 0; }}
      #{root_id} .bar > div {{ height:100%; background:linear-gradient(90deg,#3b82f6 0%, #06b6d4 100%); width:0%; }}
      #{root_id} .chip {{
        display:inline-block; font-size:12px; background:#f1f5f9; color:#334155;
        padding:2px 10px; border-radius:999px;
      }}
    </style>
    """

    # Cards
    def row_html(row):
        mins = float(row["minutos_sin_gestion"])
        hhmm = fmt_hhmm_from_minutes(mins)
        pct = 0 if total_min <= 0 else (mins / float(total_min)) * 100
        intentos = int(row.get("intentos_nc_inu", 0))
        return f"""
          <div class="card">
            <div class="name">{row['Gestor']}</div>
            <div class="value">{hhmm}<span class="muted"> h</span></div>
            <div class="bar"><div style="width:{pct:.0f}%"></div></div>
            <span class="chip">Intentos NC/IN: {intentos}</span>
          </div>
        """

    cards_html = "\n".join(row_html(r) for _, r in df_show.iterrows())
    html = f"""
      {styles}
      <div id="{root_id}">
        <div class="grid">
          {cards_html}
        </div>
      </div>
    """
    st_html(html, height=height, scrolling=False)
    
def fmt_hhmm_from_minutes(mins):
    try:
        secs = int(round(float(mins) * 60))
    except Exception:
        return "00:00"
    if secs < 0: secs = 0
    h = secs // 3600
    m = (secs % 3600) // 60
    return f"{h:02d}:{m:02d}"

def minutes_excluding_breaks(start_ts: datetime, end_ts: datetime, breaks: list[tuple[time, time]]):
    """Minutos del intervalo [start_ts, end_ts) excluyendo solapes con descansos diarios."""
    if pd.isna(start_ts) or pd.isna(end_ts) or end_ts <= start_ts:
        return 0.0
    total = (end_ts - start_ts).total_seconds() / 60.0
    if total <= 0:
        return 0.0
    d = start_ts.date()
    end_d = end_ts.date()
    overlap = 0.0
    while d <= end_d:
        for bstart, bend in breaks:
            bs = datetime.combine(d, bstart)
            be = datetime.combine(d, bend)
            s = max(start_ts, bs)
            e = min(end_ts, be)
            if e > s:
                overlap += (e - s).total_seconds() / 60.0
        d += timedelta(days=1)
    return max(0.0, total - overlap)

def split_interval_by_hours_excl_breaks(start_ts: datetime, end_ts: datetime,
                                        breaks: list[tuple[time, time]],
                                        start_h: int, end_h: int):
    """Divide [start_ts, end_ts) en bloques de 1h; devuelve (hour, minutos_netos_sin_break) por bloque."""
    out = []
    if pd.isna(start_ts) or pd.isna(end_ts) or end_ts <= start_ts:
        return out
    cur = start_ts.replace(minute=0, second=0, microsecond=0)
    if cur > start_ts:
        cur -= timedelta(hours=1)
    while cur < end_ts:
        nxt = cur + timedelta(hours=1)
        s = max(start_ts, cur)
        e = min(end_ts, nxt)
        if e > s:
            mins_block = (e - s).total_seconds() / 60.0
            d = s.date()
            for bstart, bend in breaks:
                bs = datetime.combine(d, bstart)
                be = datetime.combine(d, bend)
                ss = max(s, bs)
                ee = min(e, be)
                if ee > ss:
                    mins_block -= (ee - ss).total_seconds() / 60.0
            mins_block = max(0.0, mins_block)
            if start_h <= cur.hour < end_h and mins_block > 0:
                out.append((cur.hour, mins_block))
        cur = nxt
    return out

# ========= App config =========
st.set_page_config(page_title="Análisis de Tiempo sin Gestión", layout="wide")
st.title("📊 Análisis de Tiempo sin Gestión Telefónica")

# ========= Sidebar =========
st.sidebar.header("Configuración")
uploaded_file = st.sidebar.file_uploader("Sube el archivo CSV", type=["csv"])
min_interval = st.sidebar.selectbox("Intervalo mínimo (minutos)", [1, 2, 3, 5], index=3)

# Refrigerio
excluir_refrigerio = st.sidebar.checkbox("Excluir horario de refrigerio", value=True)
ref_inicio = st.sidebar.time_input("Inicio refrigerio", value=time(13, 0))
ref_fin    = st.sidebar.time_input("Fin refrigerio",    value=time(14, 30))
if (datetime.combine(datetime.today(), ref_fin) <= datetime.combine(datetime.today(), ref_inicio)):
    st.sidebar.warning("El fin de refrigerio debe ser mayor que el inicio. Se usará 13:00–14:30.")
    ref_inicio, ref_fin = time(13, 0), time(14, 30)
breaks_cfg = [(ref_inicio, ref_fin)] if excluir_refrigerio else []

if not uploaded_file:
    st.info("📁 Por favor, sube un archivo CSV para comenzar.")
    st.stop()

# ========= Carga =========
try:
    df_raw = pd.read_csv(uploaded_file, encoding="latin1", on_bad_lines="skip")
except Exception as e:
    st.error(f"❌ Error al procesar el archivo: {e}")
    st.stop()

for col in ["FchCreacion", "HraCreacion", "Gestor", "GstCodigo"]:
    if col not in df_raw.columns:
        st.error(f"El archivo no contiene la columna obligatoria '{col}'.")
        st.stop()

# ========= Preparación =========
df_raw["datetime"] = pd.to_datetime(
    df_raw["FchCreacion"].astype(str).str.strip() + " " + df_raw["HraCreacion"].astype(str).str.strip(),
    errors="coerce"
)
df = df_raw.dropna(subset=["datetime", "Gestor"]).copy()
df["Gestor"] = df["Gestor"].astype(str).str.strip()
df["GstCodigo_norm"] = df["GstCodigo"].astype(str).str.strip().str.lower()

# Filtros de fecha/gestor
min_date = df["datetime"].dt.date.min()
max_date = df["datetime"].dt.date.max()
date_range = st.sidebar.date_input("Rango de fechas", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date
if start_date > end_date:
    start_date, end_date = min_date, max_date

df = df[(df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)].copy()
if df.empty:
    st.warning("No hay datos para el rango de fechas seleccionado.")
    st.stop()

gestores_disponibles = sorted(df["Gestor"].unique().tolist())
gestores_seleccionados = st.sidebar.multiselect("Selecciona Gestor(es)",
                                                options=gestores_disponibles,
                                                default=gestores_disponibles)
if gestores_seleccionados:
    df = df[df["Gestor"].isin(gestores_seleccionados)].copy()
if df.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ========= LÓGICA CORRECTA =========
# 1) Ordenamos TODO por Gestor/fecha-hora y calculamos la gestión previa REAL (cualquier código)
df = df.sort_values(["Gestor", "datetime"]).copy()
df["prev_any"] = df.groupby("Gestor")["datetime"].shift(1)

# 2) Nos quedamos SOLO con filas actuales que sean NoContacto / Inubicado
codigos_permitidos = {"nocontacto", "inubicado"}
df_nc = df[df["GstCodigo_norm"].isin(codigos_permitidos)].copy()
if df_nc.empty:
    st.warning("No hay registros con GstCodigo en {'NoContacto','Inubicado'} para los filtros seleccionados.")
    st.stop()

st.caption(
    f"Se consideran **solo** filas con `GstCodigo` en {sorted(list(codigos_permitidos))}, "
    f"pero el **intervalo** se calcula contra la gestión **previa real** (sea del código que sea). "
    + (f"(Refrigerio excluido: **{ref_inicio.strftime('%H:%M')}–{ref_fin.strftime('%H:%M')}**)" if excluir_refrigerio else "(Sin exclusión de refrigerio)")
)

# 3) Minutos netos del intervalo previo→actual (restando refrigerio)
df_nc["minutos_netos"] = df_nc.apply(
    lambda r: minutes_excluding_breaks(r["prev_any"], r["datetime"], breaks_cfg), axis=1
)

# 4) Umbral y dataset final de tiempos sin gestión
df_sin = df_nc[df_nc["minutos_netos"] >= float(min_interval)].copy()
df_sin["minutos_sin_gestion"] = df_sin["minutos_netos"]
df_sin["intervalo_hhmm"] = df_sin["minutos_sin_gestion"].apply(fmt_hhmm_from_minutes)
df_sin["hhmm"] = df_sin["minutos_sin_gestion"].apply(fmt_hhmm_from_minutes)

# ========= Agregados =========
intentos_por_gestor = (df_nc.groupby("Gestor", as_index=False).size()
                       .rename(columns={"size": "intentos_nc_inu"}))
tot_por_gestor = (df_sin.groupby("Gestor", as_index=False)["minutos_sin_gestion"].sum()
                  .sort_values("minutos_sin_gestion", ascending=False))
resumen_gestor = pd.merge(intentos_por_gestor, tot_por_gestor, on="Gestor", how="left").fillna({"minutos_sin_gestion": 0})
resumen_gestor["hhmm_total"] = resumen_gestor["minutos_sin_gestion"].apply(fmt_hhmm_from_minutes)

# ========= KPIs =========
total_min = resumen_gestor["minutos_sin_gestion"].sum()
promedio_por_gestor_min = resumen_gestor["minutos_sin_gestion"].mean() if not resumen_gestor.empty else 0
gestor_max = resumen_gestor.sort_values("minutos_sin_gestion", ascending=False)["Gestor"].iloc[0] if not resumen_gestor.empty else "—"

# ========= Tabs =========
tab_kpi, tab_barras, tab_heatmap, tab_matriz, tab_detalle = st.tabs([
    "📌 KPIs", "📊 Barras por Gestor", "🔥 Mapa de calor Hora × Día", "🧮 Matriz Hora × Gestor", "📋 Detalle"
])

with tab_kpi:
    st.subheader("🔎 Métricas clave")
    c1, c2, c3 = st.columns(3)
    c1.metric("⏱ Total (todos los gestores filtrados)", f"{fmt_hhmm_from_minutes(total_min)} h")
    c2.metric("📊 Promedio por Gestor", f"{fmt_hhmm_from_minutes(promedio_por_gestor_min)} h")
    c3.metric("👤 Gestor con más tiempo sin gestión", gestor_max)

    # ——— Cards profesionales por gestor ———
    st.markdown("### 🧑‍💼 Tiempo sin gestión por Gestor (HH:MM)")

    # Control Top N (independiente del de Barras)
    n_total = len(resumen_gestor)
    if n_total > 4:
        top_n_cards = st.slider("Mostrar Top N", min_value=4, max_value=min(20, n_total),
                                value=min(8, n_total), key="top_n_cards")
    else:
        top_n_cards = n_total
        st.caption("Se muestran todos los gestores seleccionados.")

    render_gestor_cards(resumen_gestor, total_min, top_n=top_n_cards, key="gestor")

with tab_barras:
    st.subheader("Minutos sin gestión por Gestor")
    if resumen_gestor.empty or resumen_gestor["minutos_sin_gestion"].sum() == 0:
        st.info("No hay intervalos que cumplan el umbral seleccionado.")
    else:
        data_top = resumen_gestor.sort_values("minutos_sin_gestion", ascending=False).copy()
        n_g = len(data_top)
        if n_g > 1:
            top_n = st.slider("Mostrar Top N Gestores", 1, min(50, n_g), min(15, n_g))
        else:
            top_n = 1
            st.caption("Solo hay 1 gestor en el resultado; se muestra sin selector Top N.")
        data_top = data_top.head(top_n)
        bars = (alt.Chart(data_top)
            .mark_bar()
            .encode(
                x=alt.X("minutos_sin_gestion:Q", title="Minutos (netos)"),
                y=alt.Y("Gestor:N", sort="-x"),
                tooltip=[
                    alt.Tooltip("Gestor:N"),
                    alt.Tooltip("intentos_nc_inu:Q", title="Intentos NC/IN"),
                    alt.Tooltip("minutos_sin_gestion:Q", title="Minutos", format=".2f"),
                    alt.Tooltip("hhmm_total:N", title="HH:MM"),
                ]
            ).properties(height=max(300, 22*len(data_top)), width='container'))
        st.altair_chart(bars, use_container_width=True)

with tab_heatmap:
    st.subheader("Concentración por Hora × Día (minutos netos)")
    if df_sin.empty:
        st.info("No hay intervalos que cumplan el umbral.")
    else:
        tmp = df_sin[["datetime", "minutos_sin_gestion"]].copy()
        tmp["hora"] = tmp["datetime"].dt.hour
        tmp["weekday_num"] = tmp["datetime"].dt.weekday
        dias = {0:"Lun",1:"Mar",2:"Mié",3:"Jue",4:"Vie",5:"Sáb",6:"Dom"}
        tmp["dia_semana"] = tmp["weekday_num"].map(dias)
        heat = tmp.groupby(["dia_semana","weekday_num","hora"], as_index=False)["minutos_sin_gestion"].sum()
        heat["hhmm"] = heat["minutos_sin_gestion"].apply(fmt_hhmm_from_minutes)
        chart = (alt.Chart(heat).mark_rect().encode(
            x=alt.X("hora:O", title="Hora"),
            y=alt.Y("dia_semana:O", sort=["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]),
            color=alt.Color("minutos_sin_gestion:Q", title="Minutos (netos)"),
            tooltip=[
                alt.Tooltip("dia_semana:N", title="Día"),
                alt.Tooltip("hora:O", title="Hora"),
                alt.Tooltip("minutos_sin_gestion:Q", title="Minutos", format=".2f"),
                alt.Tooltip("hhmm:N", title="HH:MM")
            ]).properties(height=240, width='container'))
        st.altair_chart(chart, use_container_width=True)

with tab_matriz:
    st.subheader("Detalle por Gestor × Rango horario (formato HH:MM )")
    if df_sin.empty:
        st.info("No hay intervalos que cumplan el umbral.")
    else:
        c0, c1, c2, c3 = st.columns(4)
        usar_solapamiento = c0.checkbox("Atribución exacta por solapamiento", value=True,
                                        help="Reparte cada intervalo entre las horas que cruza y excluye refrigerio.")
        start_h = c1.number_input("Hora de inicio (0–23)", 0, 23, 6, 1)
        end_h   = c2.number_input("Hora fin (1–24)",       1, 24, 21, 1)
        umbral_rojo = c3.number_input("Resaltar en rojo si supera (min)", 1, 240, 30, 1)

        if end_h <= start_h:
            st.warning("La hora fin debe ser mayor que la hora inicio.")
        else:
            all_cols = [f"{h:02d}a{(h+1):02d}" for h in range(start_h, end_h)]

            if usar_solapamiento:
                rows = []
                # OJO: usamos prev_any calculado sobre TODO el set
                for _, r in df_sin[["Gestor","prev_any","datetime","minutos_sin_gestion"]].iterrows():
                    parts = split_interval_by_hours_excl_breaks(r["prev_any"], r["datetime"], breaks_cfg, start_h, end_h)
                    for hour, mins in parts:
                        rows.append({"Gestor": r["Gestor"], "col_etiqueta": f"{hour:02d}a{(hour+1):02d}", "minutos": float(mins)})
                agg = pd.DataFrame(rows, columns=["Gestor","col_etiqueta","minutos"]).dropna()
                value_col = "minutos"
            else:
                tmp = df_sin[["Gestor", "datetime", "minutos_sin_gestion"]].copy()
                tmp["hora"] = tmp["datetime"].dt.hour
                tmp = tmp[(tmp["hora"] >= start_h) & (tmp["hora"] < end_h)]
                tmp["col_etiqueta"] = tmp["hora"].apply(lambda h: f"{h:02d}a{(h+1):02d}")
                agg = tmp.rename(columns={"minutos_sin_gestion": "minutos"})[["Gestor","col_etiqueta","minutos"]]
                value_col = "minutos"

            if agg.empty:
                st.info("No hay minutos acumulados en el rango horario seleccionado.")
            else:
                # consolidar y pivot_table para evitar duplicados
                agg = agg.groupby(["Gestor","col_etiqueta"], as_index=False)[value_col].sum()
                matriz = pd.pivot_table(agg, index="Gestor", columns="col_etiqueta",
                                        values=value_col, aggfunc="sum", fill_value=0.0).astype(float).copy()
                for c in all_cols:
                    if c not in matriz.columns: matriz[c] = 0.0
                matriz = matriz[all_cols].sort_index()
                matriz["Total_min"] = matriz.sum(axis=1)
                total_row = pd.DataFrame(matriz.sum(axis=0)).T; total_row.index = ["TOTAL_GENERAL"]
                matriz = pd.concat([matriz, total_row])

                matriz_hhmm = matriz.copy()
                for c in all_cols + ["Total_min"]:
                    matriz_hhmm[c] = matriz_hhmm[c].apply(fmt_hhmm_from_minutes)

                def highlight_threshold(v):
                    try: val = float(v)
                    except Exception: val = 0.0
                    return "background-color:#ffe5e5; color:#b00000; font-weight:bold;" if val > umbral_rojo else ""

                styler = (matriz.style
                          .format({c: fmt_hhmm_from_minutes for c in all_cols + ["Total_min"]})
                          .background_gradient(axis=None, cmap="Blues", subset=all_cols)
                          .applymap(highlight_threshold, subset=all_cols)
                          .set_properties(**{"text-align": "center", "font-family": "monospace"})
                          .set_table_styles([
                              {"selector": "th.col_heading", "props": [("text-align", "center")]},
                              {"selector": "th.row_heading", "props": [("text-align", "left")]},
                              {"selector": "thead th", "props": [("background-color", "#f6f8fa")]}
                          ])
                          .set_properties(subset=pd.IndexSlice[["TOTAL_GENERAL"], :], **{"font-weight": "bold"}))
                st.dataframe(styler, use_container_width=True)

                # Descargar
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    matriz.to_excel(writer, sheet_name="Matriz_minutos")
                    matriz_hhmm.to_excel(writer, sheet_name="Matriz_hhmm")
                st.download_button("📥 Descargar matriz (Excel)", data=buffer.getvalue(),
                                   file_name="matriz_horas_gestor.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab_detalle:
    st.subheader("Detalles de Tiempos Sin Gestión (minutos netos)")
    if not df_sin.empty:
        df_sin = df_sin.sort_values(by=["Gestor","datetime"])
    cols = ["Gestor","datetime","GstCodigo","intervalo_hhmm","hhmm","minutos_sin_gestion"]
    st.dataframe(df_sin[cols], use_container_width=True)
    st.caption("El intervalo se calcula entre la **gestión previa real** y la fila actual (solo si es NoContacto/Inubicado). "
               + ("Se excluye refrigerio." if excluir_refrigerio else "No se excluye refrigerio."))
