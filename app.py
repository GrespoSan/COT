import streamlit as st
import requests

# =========================================================================
# CONFIGURAZIONE PAGINA
# =========================================================================
st.set_page_config(page_title="Dashboard COMM_COT_T1 (Auto)", layout="wide")
st.title("🛡️ Dashboard di Validazione — COT Automatico")
st.caption("Dati scaricati in automatico dall'API pubblica ufficiale della CFTC (publicreporting.cftc.gov).")

# =========================================================================
# FUNZIONI DI FETCH (Ora forzate sull'ultimo report disponibile)
# =========================================================================
@st.cache_data(ttl=3600)
def fetch_cftc_data(url, market_name):
    """
    Scarica le ultime 2 righe per un dato mercato, ordinate per data discendente.
    Questo garantisce di avere sempre l'ultimo report e quello precedente per calcolare il Delta.
    """
    params = {
        "$where": f"market_and_exchange_names='{market_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 2
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

# =========================================================================
# MAPPATURA MERCATI (Legacy per Commodity, TFF per Finanziari)
# =========================================================================
MERCATI = {
    "Oro (COMEX)": {"name": "GOLD - COMMODITY EXCHANGE INC.", "type": "LEGACY"},
    "Argento (COMEX)": {"name": "SILVER - COMMODITY EXCHANGE INC.", "type": "LEGACY"},
    "Rame (COMEX)": {"name": "COPPER - COMMODITY EXCHANGE INC.", "type": "LEGACY"},
    "Petrolio WTI (NYMEX)": {"name": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE", "type": "LEGACY"},
    "Gas Naturale (NYMEX)": {"name": "NATURAL GAS - NEW YORK MERCANTILE EXCHANGE", "type": "LEGACY"},
    "Euro FX (CME)": {"name": "EURO FX - CHICAGO MERCANTILE EXCHANGE", "type": "TFF"},
    "S&P 500 E-mini (CME)": {"name": "E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE", "type": "TFF"},
    "Nasdaq 100 E-mini (CME)": {"name": "E-MINI NASDAQ-100 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE", "type": "TFF"},
    "Bitcoin (CME)": {"name": "BITCOIN - CHICAGO MERCANTILE EXCHANGE", "type": "TFF"}
}

# =========================================================================
# LOGICA DI CARICAMENTO DATI
# =========================================================================
asset_scelto = st.selectbox("Seleziona il Mercato:", list(MERCATI.keys()))
info = MERCATI[asset_scelto]
url = "https://publicreporting.cftc.gov/resource/6dca-aqww.json" if info["type"] == "LEGACY" else "https://publicreporting.cftc.gov/resource/gpe5-46if.json"

# Inizializziamo valori di default
val_oi_tot, val_oi_var = 174440, -9288
val_mm_long, val_mm_short = 1261, -3831
val_comm_long, val_comm_short = -5748, 1044

dati = fetch_cftc_data(url, info["name"])

if dati and len(dati) >= 2:
    curr, prev = dati[0], dati[1]
    st.success(f"Dati caricati: Report del {curr.get('report_date_as_yyyy_mm_dd', '')[:10]}")
    
    # Estrazione dinamica basata sul tipo di report
    val_oi_tot = float(curr.get("open_interest_all", 0))
    val_oi_var = val_oi_tot - float(prev.get("open_interest_all", 0))
    
    if info["type"] == "LEGACY":
        val_mm_long = float(curr.get("noncomm_positions_long_all", 0)) - float(prev.get("noncomm_positions_long_all", 0))
        val_mm_short = float(curr.get("noncomm_positions_short_all", 0)) - float(prev.get("noncomm_positions_short_all", 0))
        val_comm_long = float(curr.get("comm_positions_long_all", 0)) - float(prev.get("comm_positions_long_all", 0))
        val_comm_short = float(curr.get("comm_positions_short_all", 0)) - float(prev.get("comm_positions_short_all", 0))
    else:
        val_mm_long = float(curr.get("lev_money_positions_long_all", 0)) - float(prev.get("lev_money_positions_long_all", 0))
        val_mm_short = float(curr.get("lev_money_positions_short_all", 0)) - float(prev.get("lev_money_positions_short_all", 0))
        val_comm_long = float(curr.get("dealer_positions_long_all", 0)) - float(prev.get("dealer_positions_long_all", 0))
        val_comm_short = float(curr.get("dealer_positions_short_all", 0)) - float(prev.get("dealer_positions_short_all", 0))
else:
    st.warning("Dati non trovati o server CFTC irraggiungibile. Usa i valori di default o controlla la connessione.")

# =========================================================================
# BLOCCO 1: Inserimento Dati
# =========================================================================
st.header("1. Inserimento Dati")
st.caption("I dati sono autocompilati, ma puoi modificarli manualmente.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.subheader("Open Interest")
    oi_tot = st.number_input("Open Interest Totale", value=int(val_oi_tot))
    oi_var = st.number_input("Change in Open Interest", value=int(val_oi_var))
with col2:
    st.subheader("Managed Money (MM)")
    mm_long = st.number_input("MM Change Long", value=int(val_mm_long))
    mm_short = st.number_input("MM Change Short", value=int(val_mm_short))
with col3:
    st.subheader("Commercials")
    comm_long = st.number_input("Comm Change Long", value=int(val_comm_long))
    comm_short = st.number_input("Comm Change Short", value=int(val_comm_short))
with col4:
    st.subheader("Term Structure")
    term_struct = st.radio("Stato attuale:", ["Backwardation (verde)", "Contango (rosso)"])

# =========================================================================
# BLOCCO 2: Elaborazione Matematica
# =========================================================================
pct_delta_oi = (oi_var / (oi_tot - oi_var)) * 100 if (oi_tot - oi_var) != 0 else 0
flusso_netto_mm = mm_long - mm_short
flusso_netto_comm = comm_long - comm_short

st.header("2. Elaborazione Matematica")
calc1, calc2, calc3 = st.columns(3)
calc1.metric("Variazione % Open Interest", f"{pct_delta_oi:.2f}%")
calc2.metric("Flusso Netto Speculativo (MM)", f"{flusso_netto_mm:+.0f}")
calc3.metric("Flusso Netto Commerciale", f"{flusso_netto_comm:+.0f}")

st.divider()

# =========================================================================
# BLOCCO 3: Matrice di Diagnosi
# =========================================================================
st.header("3. Matrice di Diagnosi Microstrutturale: Il Verdetto")

stato_colore, stato_testo, verdetto, azione = "orange", "FASE DI TRANSIZIONE / INCERTEZZA", "Flussi misti in assestamento", "Resta in attesa."

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    stato_colore, stato_testo, verdetto = "green", "CONVERGENT LONG / FORZA STRUTTURALE", "Espansione Rialzista Istituzionale [STADIO 1-A]"
    azione = "Valuta ingressi Long sui supporti volumetrici o mantieni i Long attivi."
elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    stato_colore, stato_testo, verdetto = "red", "DISTRIBUZIONE / PERICOLO", "Fase di Distribuzione Istituzionale [STADIO 1-B]"
    azione = "Chiudi o proteggi le posizioni Long. Non comprare."
elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    stato_colore, stato_testo, verdetto = "green", "HOLD AGGRESSIVO / SQUEEZE", "Short Covering Squeeze [STADIO 3-B]"
    azione = "Mantieni l'acquisto. Alza i target protettivi."

st.markdown(f"#### **Il Verdetto:** {verdetto}")
st.info(f"Diagnosi: OI ({pct_delta_oi:.2f}%), MM ({flusso_netto_mm:+}), Comm ({flusso_netto_comm:+})")
st.markdown(f"### Stato Operativo: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)
st.success(f"**Azione Strategica:** {azione}")

st.divider()

# =========================================================================
# BLOCCO 4: Interpretazione Macro
# =========================================================================
st.header("4. Interpretazione Macro e Sequenza Temporale")

if flusso_netto_mm > 0 and flusso_netto_comm < 0:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE**")
    st.write(f"Armonia rialzista. Speculatori comprano (`{flusso_netto_mm:+.0f}`) e OI sale. Commerciali coprono la produzione.")
elif flusso_netto_mm < 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA ISTITUZIONALE: SHORT ➔ LONG**")
    st.write(f"Speculatori vendono (`{flusso_netto_mm:+.0f}`), ma i Commercials accumulano Long creando un pavimento.")
elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA ISTITUZIONALE: LONG ➔ SHORT**")
    st.write(f"Speculatori spingono (`{flusso_netto_mm:+.0f}`), Commercials vendono (`{flusso_netto_comm:+.0f}`). Stanno creando un tetto.")
elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write("Debolezza totale. Sia fondi che commerciali scaricano il mercato.")
else:
    st.info("⚪ **FLUSSI IN EQUILIBRIO NEUTRO**")
    st.write("Nessuno sbilanciamento direzionale rilevante.")
