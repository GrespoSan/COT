import streamlit as st
import requests
import pandas as pd
import datetime

# --- Configurazione Pagina ---
st.set_page_config(page_title="Dashboard COMM_COT_T1", layout="wide")
st.title("🛡️ Dashboard Automatizzata COT (API Live — Legacy Futures)")

# Endpoint Socrata ufficiale CFTC per il report Legacy Futures Only
LEGACY_API_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

# --- FUNZIONI DI ACCESSO API (Prese dal tuo esempio e ottimizzate) ---
@st.cache_data(ttl=43200)  # Cache di 12 ore per non sovraccaricare l'API cftc
def fetch_all_market_names():
    """Scarica la lista completa dei mercati disponibili sul server CFTC."""
    params = {
        "$select": "market_and_exchange_names",
        "$group": "market_and_exchange_names",
        "$limit": 2000,
    }
    try:
        r = requests.get(LEGACY_API_URL, params=params, timeout=15)
        r.raise_for_status()
        return sorted(row["market_and_exchange_names"] for row in r.json() if "market_and_exchange_names" in row)
    except Exception:
        return []

@st.cache_data(ttl=21600)  # Cache di 6 ore per i dati storici dell'asset
def fetch_latest_two_weeks(market_name: str):
    """Scarica le ultime 2 settimane di dati reali per calcolare variazioni certe."""
    safe_name = market_name.replace("'", "''")
    params = {
        "$where": f"market_and_exchange_names='{safe_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 2,
    }
    try:
        r = requests.get(LEGACY_API_URL, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def clean_num(val):
    """Converte in modo sicuro i valori dell'API in interi puliti."""
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return 0

# Caricamento iniziale asincrono di tutti i mercati della CFTC
with st.spinner("Connessione ai server API della CFTC..."):
    tutti_i_mercati_cftc = fetch_all_market_names()

# --- DIZIONARIO DI MAPPATURA (Nomi puliti associati alle stringhe esatte dell'API) ---
MAPPA_FUTURE = {
    "🥇 Oro (COMEX)": "GOLD - COMMODITY EXCHANGE INC.",
    "🥈 Argento (COMEX)": "SILVER - COMMODITY EXCHANGE INC.",
    "🥉 Rame (COMEX)": "COPPER - COMMODITY EXCHANGE INC.",
    "🛢️ Petrolio WTI (NYMEX)": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
    "🔥 Gas Naturale (NYMEX)": "NATURAL GAS - NEW YORK MERCANTILE EXCHANGE",
    "📈 S&P 500 E-Mini (CME)": "E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
    "💻 Nasdaq 100 E-Mini (CME)": "E-MINI NASDAQ-100 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
    "🇪🇺 Euro FX (EUR/USD - CME)": "EURO FX - CHICAGO MERCANTILE EXCHANGE",
    "🇬🇧 Sterlina (GBP/USD - CME)": "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
    "🇯🇵 Yen Giapponese (JPY/USD - CME)": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
    "🪙 Bitcoin (CME)": "BITCOIN - CHICAGO MERCANTILE EXCHANGE",
    "🇺🇸 Treasury Note 10Y (CBOT)": "10-YEAR U.S. TREASURY NOTES - CHICAGO BOARD OF TRADE"
}

# --- BLOCCO 1: Selezione Asset & Raccolta Dati ---
st.header("1. Selezione Asset & Raccolta Dati")

# Configurazione del menu di selezione rapida e fallback
opzioni_menu = list(MAPPA_FUTURE.keys()) + ["--- ELENCO COMPLETO REALE CFTC ---"] + tutti_i_mercati_cftc
scelta_utente = st.selectbox("Scegli il Future da analizzare:", opzioni_menu, index=0)

if scelta_utente in MAPPA_FUTURE:
    selected_asset = MAPPA_FUTURE[scelta_utente]
elif scelta_utente == "--- ELENCO COMPLETO REALE CFTC ---":
    st.warning("Seleziona un asset valido dall'elenco sopra o sotto questa riga di servizio.")
    st.stop()
else:
    selected_asset = scelta_utente

st.info(f"Connessione API attiva su asset: `{selected_asset}`")

# Fetching dei dati tramite il sistema di accesso dell'API Socrata
api_data = fetch_latest_two_weeks(selected_asset)

# Inizializzazione valori di default nel caso l'API fallisse
auto_oi_tot, auto_oi_var, auto_mm_long, auto_mm_short, auto_comm_long, auto_comm_short = 174440, -9288, 1261, -3831, -5748, 1044

if api_data and len(api_data) >= 2:
    r_current = api_data[0]   # Settimana corrente (la più recente)
    r_previous = api_data[1]  # Settimana precedente
    
    # Estrazione dei posizionamenti assoluti delle due settimane
    oi_curr = clean_num(r_current.get("open_interest_all"))
    oi_prev = clean_num(r_previous.get("open_interest_all"))
    
    m_long_curr = clean_num(r_current.get("noncommercial_positions_long_all"))
    m_long_prev = clean_num(r_previous.get("noncommercial_positions_long_all"))
    
    m_short_curr = clean_num(r_current.get("noncommercial_positions_short_all"))
    m_short_prev = clean_num(r_previous.get("noncommercial_positions_short_all"))
    
    c_long_curr = clean_num(r_current.get("commercial_positions_long_all"))
    c_long_prev = clean_num(r_previous.get("commercial_positions_long_all"))
    
    c_short_curr = clean_num(r_current.get("commercial_positions_short_all"))
    c_short_prev = clean_num(r_previous.get("commercial_positions_short_all"))
    
    # Calcolo matematico in tempo reale dei differenziali (Delta precisi al 100%)
    auto_oi_tot = oi_curr
    auto_oi_var = oi_curr - oi_prev
    auto_mm_long = m_long_curr - m_long_prev
    auto_mm_short = m_short_curr - m_short_prev
    auto_comm_long = c_long_curr - c_long_prev
    auto_comm_short = c_short_curr - c_short_prev
    
    # Estrazione e formattazione della data del report
    raw_date = r_current.get("report_date_as_yyyy_mm_dd", "T00:00:00")
    formatted_date = raw_date.split("T")[0]
    st.caption(f"📅 Data ultimo report elaborato via API: **{formatted_date}**")
elif api_data and len(api_data) == 1:
    st.warning("Trovata solo una settimana di storico sull'API. Impossibile calcolare il delta.")
else:
    st.error("Errore di rete o asset non disponibile nell'API Legacy. Fallback sui dati manuali.")

# Layout colonne di input (popolate automaticamente con i dati ricalcolati)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("Open Interest")
    oi_tot = st.number_input("Open Interest Totale", value=auto_oi_tot)
    oi_var = st.number_input("Change in Open Interest", value=auto_oi_var)

with col2:
    st.subheader("Speculators (Non-Comm)")
    mm_long = st.number_input("Non-Comm Change Long", value=auto_mm_long)
    mm_short = st.number_input("Non-Comm Change Short", value=auto_mm_short)

with col3:
    st.subheader("Commercials")
    comm_long = st.number_input("Comm Change Long", value=auto_comm_long)
    comm_short = st.number_input("Comm Change Short", value=auto_comm_short)

with col4:
    st.subheader("Term Structure")
    term_struct = st.radio("Stato attuale della curva (da Tradingview):", ["Backwardation (verde)", "Contango (rosso)"])

# --- BLOCCO 2: Elaborazione Matematica ---
pct_delta_oi = (oi_var / (oi_tot - oi_var)) * 100 if (oi_tot - oi_var) != 0 else 0
flusso_netto_mm = mm_long - mm_short
flusso_netto_comm = comm_long - comm_short

st.header("2. Elaborazione Matematica")
calc1, calc2, calc3 = st.columns(3)
calc1.metric("Variazione % Open Interest", f"{pct_delta_oi:.2f}%")
calc2.metric("Flusso Netto Speculativo (Non-Comm)", f"{flusso_netto_mm:+.0f}")
calc3.metric("Flusso Netto Commerciale", f"{flusso_netto_comm:+.0f}")

st.divider()

# --- BLOCCO 3: Matrice di Diagnosi e Azione Strategica ---
st.header("3. Matrice di Diagnosi Microstrutturale: Il Verdetto")

stato_colore = "orange"
stato_testo = "FASE DI TRANSIZIONE / INCERTEZZA"
verdetto = "Flussi misti in assestamento"
diag_oi = f"La variazione dell'OI ({pct_delta_oi:.2f}%) mostra un posizionamento standard."
diag_mm = f"I grandi fondi speculativi mantengono un flusso netto di {flusso_netto_mm:+.0f}."
diag_comm = f"I Commercials registrano un flusso netto di {flusso_netto_comm:+.0f}."
azione = "Resta in attesa di una chiara convergenza o divergenza strutturale."

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    stato_colore = "green"
    stato_testo = "CONVERGENT LONG / FORZA STRUTTURALE"
    verdetto = "Espansione Rialzista Istituzionale - Ingresso di Capitale Buyer [STADIO 1-A]"
    diag_oi = f"L'Open Interest è in forte espansione ({pct_delta_oi:.2f}%), confermando l'ingresso di nuova liquidità direzionale."
    diag_mm = f"I grandi fondi speculativi guidano il trend immettendo flussi nettamente rialzisti ({flusso_netto_mm:+.0f})."
    diag_comm = f"I Commercials assecondano la salita vendendo coperture sui massimi (Flusso: {flusso_netto_comm:+.0f})."
    azione = "Valuta ingressi Long sui supporti volumetrici o mantieni i Long attivi piramidando sulla forza."

elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    stato_colore = "red"
    stato_testo = "DISTRIBUZIONE / PERICOLO"
    verdetto = "Fase di Distribuzione Istituzionale e Accumulo Short [STADIO 1-B]"
    diag_oi = f"L'Open Interest è in espansione ({pct_delta_oi:.2f}%), ma i contratti aperti sono guidati dai venditori."
    diag_mm = f"I fondi speculativi stanno immettendo massicci flussi ribassisti ({flusso_netto_mm:+.0f}), shortando il mercato."
    diag_comm = f"I Commercials stanno assorbendo la liquidità comprando a sconto (Flusso: {flusso_netto_comm:+.0f})."
    azione = "Chiudi o proteggi drasticamente le posizioni Long. Non comprare assolutamente in questa fase."

elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    stato_colore = "green"
    stato_testo = "HOLD AGGRESSIVO / SQUEEZE"
    verdetto = "Short Covering Squeeze di continuazione strutturale [STADIO 3-B]"
    diag_oi = f"L'Open Interest subisce una contrazione massiccia ({pct_delta_oi:.2f}%), indicando la fuga dei venditori intrappolati."
    diag_mm = f"Flusso Speculativo positivo ({flusso_netto_mm:+.0f}) causato principalmente dalla chiusura forzata degli Short."
    diag_comm = f"Flusso Commercials: {flusso_netto_comm:+.0f}."
    azione = "Mantieni l'acquisto effettuato. Alza i target protettivi e stringi lo stop-loss sotto i minimi di struttura."

st.markdown(f"#### **Il Verdetto:** {verdetto}")
st.info(f"""
- **Diagnosi OI:** {diag_oi}
- **Diagnosi MM:** {diag_mm}
- **Diagnosi Commercials:** {diag_comm}
""")

st.markdown(f"### Stato Operativo Ricalibrato: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)
st.success(f"**Azione Strategica:**\n- {azione}")
st.divider()

# --- BLOCCO 4: Interpretazione Macro ---
st.header("4. Interpretazione Macro e Sequenza Temporale")

if flusso_netto_mm > 0 and flusso_netto_comm < 0:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE (Allineato con TradingView)**")
    st.write(f"**Cosa succede:** I grandi speculatori comprano in modo aggressivo (`{flusso_netto_mm:+.0f}`) e l'OI sale. I commerciali coprono la produzione vendendo sui massimi.")
elif flusso_netto_mm < 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: SHORT ➔ LONG**")
    st.write(f"**Cosa succede:** Nel breve i fondi speculativi vendono (`{flusso_netto_mm:+.0f}`), ma i Commercials stanno accumulando posizioni Long fabbricando un pavimento di medio termine.")
elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: LONG ➔ SHORT**")
    st.write(f"**Cosa succede:** I fondi spingono ancora in alto, ma i Commercials vendono massicciamente (`{flusso_netto_comm:+.0f}`) ponendo un tetto al mercato per le prossime settimane.")
elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write("Il mercato è strutturalmente debole a tutti i livelli temporali, la pressione ribassista è totale.")
else:
    st.info("⚪ **FLUSSI IN EQUILIBRIO NEUTRO**")
