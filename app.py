import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import zipfile
import io
import datetime

# --- Configurazione Pagina ---
st.set_page_config(page_title="Dashboard COMM_COT_T1", layout="wide")
st.title("🛡️ Dashboard Automatizzata COT (Legacy - Solo Futures)")

# --- FUNZIONE DI SCARICAMENTO E PARSING DATI COT LEGACY ---
@st.cache_data(ttl=43200)  # Memorizza i dati per 12 ore
def load_legacy_futures_cot():
    current_year = datetime.datetime.now().year
    years = [current_year - 1, current_year]
    dfs = []
    
    # 🔥 FIX FONDAMENTALE: Simula un browser reale. Senza questo la CFTC rifiuta la connessione (Errore 403)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    for year in years:
        url = f"https://www.cftc.gov/files/dea/history/deahist{year}.zip"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    file_name = z.namelist()[0]
                    df = pd.read_csv(z.open(file_name), low_memory=False)
                    
                    # Rimuove gli spazi bianchi dalle colonne
                    df.columns = df.columns.str.strip()
                    dfs.append(df)
        except Exception:
            continue
            
    if not dfs:
        return None
        
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Mappatura specifica delle colonne del report Legacy
    cols_mapping = {
        'Market_and_Exchange_Names': 'Asset',
        'Report_Date_as_YYYY-MM-DD': 'Data',
        'Open_Interest_All': 'OI',
        'Noncommercial_Positions_Long_All': 'MM_Long',
        'Noncommercial_Positions_Short_All': 'MM_Short',
        'Commercial_Positions_Long_All': 'Comm_Long',
        'Commercial_Positions_Short_All': 'Comm_Short'
    }
    
    df_all = df_all.rename(columns=cols_mapping)
    
    # Controllo difensivo per evitare colonne mancanti
    for col in cols_mapping.values():
        if col not in df_all.columns:
            df_all[col] = 0
            
    # Conversione formati
    df_all['Data'] = pd.to_datetime(df_all['Data'], errors='coerce')
    
    numeric_cols = ['OI', 'MM_Long', 'MM_Short', 'Comm_Long', 'Comm_Short']
    for col in numeric_cols:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce').fillna(0).astype(int)
        
    return df_all

# Caricamento del database globale COT
with st.spinner("Estrazione dati in corso dal server della CFTC..."):
    df_cot = load_legacy_futures_cot()

# --- DIZIONARIO DI MAPPATURA (Lista Pulita) ---
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

if df_cot is not None:
    tutti_i_mercati_cftc = sorted(df_cot['Asset'].dropna().unique())
    opzioni_menu = list(MAPPA_FUTURE.keys()) + ["--- ELENCO COMPLETO CFTC DI SERVIZIO ---"] + tutti_i_mercati_cftc
    
    scelta_utente = st.selectbox("Scegli il Future da analizzare:", opzioni_menu, index=0)
    
    if scelta_utente in MAPPA_FUTURE:
        selected_asset = MAPPA_FUTURE[scelta_utente]
    elif scelta_utente == "--- ELENCO COMPLETO CFTC DI SERVIZIO ---":
        st.warning("⚠️ Seleziona un asset valido dalla lista.")
        st.stop()
    else:
        selected_asset = scelta_utente
        
    st.info(f"Target CFTC Attivo: `{selected_asset}`")

    # Isoliamo lo storico dell'asset selezionato
    df_asset = df_cot[df_cot['Asset'] == selected_asset].sort_values('Data')
    df_asset = df_asset.drop_duplicates(subset=['Data'], keep='last')
    
    if len(df_asset) >= 2:
        r_current = df_asset.iloc[-1]   
        r_previous = df_asset.iloc[-2]  
        
        # Calcolo automatico dei valori e dei delta settimanali
        auto_oi_tot = int(r_current['OI'])
        auto_oi_var = int(r_current['OI'] - r_previous['OI'])
        
        auto_mm_long = int(r_current['MM_Long'] - r_previous['MM_Long'])
        auto_mm_short = int(r_current['MM_Short'] - r_previous['MM_Short'])
        
        auto_comm_long = int(r_current['Comm_Long'] - r_previous['Comm_Long'])
        auto_comm_short = int(r_current['Comm_Short'] - r_previous['Comm_Short'])
        
        st.caption(f"📅 Data ultimo report rilasciato: **{r_current['Data'].strftime('%Y-%m-%d')}**")
    else:
        st.error("Errore: Dati storici insufficienti nel database per questo asset.")
        auto_oi_tot, auto_oi_var, auto_mm_long, auto_mm_short, auto_comm_long, auto_comm_short = 174440, -9288, 1261, -3831, -5748, 1044
else:
    st.error("Impossibile scaricare i dati dalla CFTC. Fallback sui dati manuali.")
    auto_oi_tot, auto_oi_var, auto_mm_long, auto_mm_short, auto_comm_long, auto_comm_short = 174440, -9288, 1261, -3831, -5748, 1044

# Layout colonne di input (pre-compilate)
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
    term_struct = st.radio("Stato attuale (da Tradingview):", ["Backwardation (verde)", "Contango (rosso)"])

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
