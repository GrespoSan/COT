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
    """Scarica il report più recente e legge direttamente i campi 'change' ufficiali."""
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
        return r.json()[0] if r.json() else None
    except:
        return None

# Mappatura: (Nome CFTC, Tipo Report)
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

st.caption("Seleziona l'asset per autocompilare i dati dal server CFTC:")
scelta_utente = st.selectbox("Mercato:", list(MERCATI.keys()), label_visibility="collapsed")
nome_cftc, tipo_report = MERCATI[scelta_utente]

# Valori di default
val_oi_tot, val_oi_var = 174440, -9288
val_mm_long, val_mm_short = 1261, -3831
val_comm_long, val_comm_short = -5748, 1044

# Esecuzione chiamata API
dati_api = fetch_cot_data(nome_cftc, tipo_report)

if dati_api:
    try:
        # Leggiamo i campi ufficiali "change" forniti dalla CFTC
        val_oi_tot = int(float(dati_api.get("open_interest_all", 0)))
        
        if tipo_report == "LEGACY":
            val_oi_var = int(float(dati_api.get("change_in_open_interest_all", 0)))
            val_mm_long = int(float(dati_api.get("change_in_noncomm_long_all", 0)))
            val_mm_short = int(float(dati_api.get("change_in_noncomm_short_all", 0)))
            val_comm_long = int(float(dati_api.get("change_in_comm_long_all", 0)))
            val_comm_short = int(float(dati_api.get("change_in_comm_short_all", 0)))
        else:
            # Report TFF: Dealer = Commercials, Lev Money = Speculatori
            val_oi_var = int(float(dati_api.get("change_in_open_interest_all", 0)))
            val_mm_long = int(float(dati_api.get("change_in_lev_money_long_all", 0)))
            val_mm_short = int(float(dati_api.get("change_in_lev_money_short_all", 0)))
            val_comm_long = int(float(dati_api.get("change_in_dealer_long_all", 0)))
            val_comm_short = int(float(dati_api.get("change_in_dealer_short_all", 0)))
        
        st.success(f"Dati sincronizzati con il report ufficiale CFTC del **{dati_api.get('report_date_as_yyyy_mm_dd', '')[:10]}**")
    except Exception:
        st.error("Errore di caricamento dati. Usare i valori manuali.")
else:
    st.warning("Impossibile contattare la CFTC. Fallback manuale attivo.")

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

# --- BLOCCO 3: Verdetto ---
st.header("3. Matrice di Diagnosi Microstrutturale: Il Verdetto")

# Logica invariata
stato_colore = "orange"
stato_testo = "FASE DI TRANSIZIONE / INCERTEZZA"
verdetto = "Flussi misti in assestamento"
azione = "Resta in attesa di una chiara convergenza o divergenza strutturale."

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    stato_colore = "green"
    stato_testo = "CONVERGENT LONG / FORZA STRUTTURALE"
    verdetto = "Espansione Rialzista Istituzionale - Ingresso di Capitale Buyer [STADIO 1-A]"
    azione = "Valuta ingressi Long sui supporti volumetrici o mantieni i Long attivi piramidando sulla forza."

elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    stato_colore = "red"
    stato_testo = "DISTRIBUZIONE / PERICOLO"
    verdetto = "Fase di Distribuzione Istituzionale e Accumulo Short [STADIO 1-B]"
    azione = "Chiudi o proteggi drasticamente le posizioni Long. Non comprare assolutamente in questa fase."

elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    stato_colore = "green"
    stato_testo = "HOLD AGGRESSIVO / SQUEEZE"
    verdetto = "Short Covering Squeeze di continuazione strutturale [STADIO 3-B]"
    azione = "Mantieni l'acquisto effettuato. Alza i target protettivi e stringi lo stop-loss sotto i minimi di struttura."

st.markdown(f"#### **Il Verdetto:** {verdetto}")
st.markdown(f"### Stato Operativo: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)
st.success(f"**Azione Strategica:**\n- {azione}")
st.divider()

# --- BLOCCO 4: Interpretazione Macro ---
st.header("4. Interpretazione Macro e Sequenza Temporale")

if flusso_netto_mm > 0 and flusso_netto_comm < 0:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE**")
    st.write(f"**Cosa sta succedendo:** Siamo in piena armonia rialzista. Speculatori comprano (`{flusso_netto_mm:+.0f}`) e l'OI sale. Commerciali vendono per coprire la produzione.")
    st.error("**💡 Conclusione:** Trend solido, asseconda il segnale Long.")

elif flusso_netto_mm < 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA: SHORT ➔ LONG**")
    st.write(f"**Cosa sta succedendo:** Speculatori vendono (`{flusso_netto_mm:+.0f}`), ma i Commerciali accumulano Long creando un pavimento.")
    st.error("**💡 Conclusione:** Breve termine Short, monitora per inversione Long.")

elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA: LONG ➔ SHORT**")
    st.write(f"**Cosa sta succedendo:** Speculatori spingono alto (`{flusso_netto_mm:+.0f}`), ma Commerciali vendono massicciamente (`{flusso_netto_comm:+.0f}`).")
    st.error("**💡 Conclusione:** Trend di brevissimo ancora Long, ma la Smart Money costruisce un tetto.")

elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write("Entrambi vendono. Il mercato è strutturalmente debole.")

else:
    st.info("⚪ **FLUSSI IN EQUILIBRIO NEUTRO**")
