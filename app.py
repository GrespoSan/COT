import streamlit as st
import requests

# --- Configurazione Pagina ---
st.set_page_config(page_title="Dashboard COMM_COT_T1", layout="wide")
st.title("🛡️ Dashboard di Validazione")

# ==========================================
# MOTORE DI AUTOMAZIONE (Estrazione API CFTC)
# ==========================================
@st.cache_data(ttl=43200)
def fetch_cot_data(market_name, report_type):
    """Scarica il report più recente e legge i campi 'change' ufficiali CFTC."""
    if report_type == "LEGACY":
        url = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"
    else:
        url = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"
        
    params = {
        "$where": f"market_and_exchange_names='{market_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 1
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None
    except:
        return None

# Mappatura: (Nome ufficiale CFTC, Tipo Report)
MERCATI = {
    "🥇 Oro (COMEX)": ("GOLD - COMMODITY EXCHANGE INC.", "LEGACY"),
    "🥈 Argento (COMEX)": ("SILVER - COMMODITY EXCHANGE INC.", "LEGACY"),
    "🥉 Rame (COMEX)": ("COPPER - COMMODITY EXCHANGE INC.", "LEGACY"),
    "🛢️ Petrolio WTI (NYMEX)": ("CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "🔥 Gas Naturale (NYMEX)": ("NATURAL GAS - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "📈 S&P 500 E-Mini (CME)": ("E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE", "TFF"),
    "💻 Nasdaq 100 E-Mini (CME)": ("E-MINI NASDAQ-100 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE", "TFF"),
    "🇪🇺 Euro FX (CME)": ("EURO FX - CHICAGO MERCANTILE EXCHANGE", "TFF"),
    "🪙 Bitcoin (CME)": ("BITCOIN - CHICAGO MERCANTILE EXCHANGE", "TFF")
}

st.caption("Seleziona l'asset per autocompilare i dati dal server ufficiale CFTC:")
scelta_utente = st.selectbox("Mercato:", list(MERCATI.keys()), label_visibility="collapsed")
nome_cftc, tipo_report = MERCATI[scelta_utente]

# Valori di default (Fallback)
val_oi_tot, val_oi_var = 174440, -9288
val_mm_long, val_mm_short = 1261, -3831
val_comm_long, val_comm_short = -5748, 1044

# Esecuzione chiamata API
dati_api = fetch_cot_data(nome_cftc, tipo_report)

if dati_api:
    try:
        val_oi_tot = int(float(dati_api.get("open_interest_all", 0)))
        val_oi_var = int(float(dati_api.get("change_in_open_interest_all", 0)))
        
        if tipo_report == "LEGACY":
            val_mm_long = int(float(dati_api.get("change_in_noncomm_long_all", 0)))
            val_mm_short = int(float(dati_api.get("change_in_noncomm_short_all", 0)))
            val_comm_long = int(float(dati_api.get("change_in_comm_long_all", 0)))
            val_comm_short = int(float(dati_api.get("change_in_comm_short_all", 0)))
        else:
            val_mm_long = int(float(dati_api.get("change_in_lev_money_long_all", 0)))
            val_mm_short = int(float(dati_api.get("change_in_lev_money_short_all", 0)))
            val_comm_long = int(float(dati_api.get("change_in_dealer_long_all", 0)))
            val_comm_short = int(float(dati_api.get("change_in_dealer_short_all", 0)))
        
        st.success(f"Dati sincronizzati con il report CFTC del **{dati_api.get('report_date_as_yyyy_mm_dd', '')[:10]}**")
    except Exception:
        st.warning("Errore nel parsing dati API. Utilizzo valori di default.")
else:
    st.warning("Impossibile contattare la CFTC. Utilizzo valori di default.")

st.divider()

# --- BLOCCO 1: Inserimento Dati ---
st.header("1. Inserimento Dati")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("Open Interest")
    oi_tot = st.number_input("Open Interest Totale", value=val_oi_tot)
    oi_var = st.number_input("Change in Open Interest", value=val_oi_var)

with col2:
    st.subheader("Managed Money (MM)")
    mm_long = st.number_input("MM Change Long", value=val_mm_long)
    mm_short = st.number_input("MM Change Short", value=val_mm_short)

with col3:
    st.subheader("Commercials")
    comm_long = st.number_input("Comm Change Long", value=val_comm_long)
    comm_short = st.number_input("Comm Change Short", value=val_comm_short)

with col4:
    st.subheader("Term Structure")
    term_struct = st.radio("Stato attuale:", ["Backwardation (verde)", "Contango (rosso)"])

# --- BLOCCO 2: Elaborazione Matematica ---
pct_delta_oi = (oi_var / (oi_tot - oi_var)) * 100 if (oi_tot - oi_var) != 0 else 0
flusso_netto_mm = mm_long - mm_short
flusso_netto_comm = comm_long - comm_short

st.header("2. Elaborazione Matematica")
calc1, calc2, calc3 = st.columns(3)
calc1.metric("Variazione % Open Interest", f"{pct_delta_oi:.2f}%")
calc2.metric("Flusso Netto Speculativo (MM)", f"{flusso_netto_mm:+.0f}")
calc3.metric("Flusso Netto Commerciale", f"{flusso_netto_comm:+.0f}")

st.divider()

# --- BLOCCO 3: Matrice di Diagnosi ---
st.header("3. Matrice di Diagnosi Microstrutturale: Il Verdetto")

stato_colore, stato_testo, verdetto, azione = "orange", "FASE DI TRANSIZIONE", "Flussi misti", "Resta in attesa."

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    stato_colore, stato_testo, verdetto = "green", "CONVERGENT LONG", "Espansione Rialzista [STADIO 1-A]"
    azione = "Valuta ingressi Long sui supporti volumetrici."
elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    stato_colore, stato_testo, verdetto = "red", "DISTRIBUZIONE", "Distribuzione Istituzionale [STADIO 1-B]"
    azione = "Chiudi o proteggi posizioni Long. Non comprare."
elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    stato_colore, stato_testo, verdetto = "green", "HOLD AGGRESSIVO", "Short Covering Squeeze [STADIO 3-B]"
    azione = "Mantieni, alza target protettivi."

st.markdown(f"#### **Il Verdetto:** {verdetto}")
st.markdown(f"### Stato Operativo: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)
st.success(f"**Azione:** {azione}")
st.divider()

# --- BLOCCO 4: Interpretazione Macro ---
st.header("4. Interpretazione Macro")
if flusso_netto_mm > 0 and flusso_netto_comm < 0:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE**")
    st.write(f"Armonia rialzista. Speculatori comprano (`{flusso_netto_mm:+.0f}`) e OI sale.")
elif flusso_netto_mm < 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA: SHORT ➔ LONG**")
    st.write(f"Speculatori vendono (`{flusso_netto_mm:+.0f}`), ma i Commercials accumulano Long.")
elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA: LONG ➔ SHORT**")
    st.write(f"Speculatori spingono (`{flusso_netto_mm:+.0f}`), Commercials vendono (`{flusso_netto_comm:+.0f}`).")
elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write("Debolezza totale, pressione ribassista.")
else:
    st.info("⚪ **FLUSSI NEUTRI**")
