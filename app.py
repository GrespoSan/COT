import streamlit as st
import requests

# --- Configurazione Pagina ---
st.set_page_config(page_title="Dashboard COMM_COT_T1 (Auto)", layout="wide")
st.title("🛡️ Dashboard di Validazione — COT Automatico")

# =========================================================================
# MOTORE DI AUTOMAZIONE (Estrazione API CFTC)
# =========================================================================
@st.cache_data(ttl=3600)
def fetch_cot_data(market_name, report_type):
    """
    Scarica l'ultimo report disponibile per il mercato scelto.
    L'ordinamento DESC garantisce di ottenere sempre l'ultimo record.
    """
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
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except Exception:
        return None

# Mappatura Mercati
MERCATI = {
    "S&P 500": ("S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "Nasdaq 100": ("NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "Dow Jones": ("DJIA x $5 - CHICAGO BOARD OF TRADE", "LEGACY"),
    "Russell 2000": ("RUSSELL E-MINI - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "CL WTI (Petrolio)": ("WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "RB Gasoline RBOB": ("GASOLINE RBOB - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "Gold (Oro)": ("GOLD - COMMODITY EXCHANGE INC.", "LEGACY"),
    "Silver (Argento)": ("SILVER - COMMODITY EXCHANGE INC.", "LEGACY"),
    "Copper (Rame)": ("COPPER - COMMODITY EXCHANGE INC.", "LEGACY"),
    "PL Platino": ("PLATINUM - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "PA Palladium": ("PALLADIUM - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "Natural Gas": ("NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE", "LEGACY"),
    "DX1 USD": ("USD INDEX - ICE FUTURES U.S.", "LEGACY"),
    "6E Euro": ("EURO FX - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "6B GBP": ("BRITISH POUND - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "6A AUD": ("AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "6N NZD": ("NZ DOLLAR - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "6C CAD": ("CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "6S CHF": ("SWISS FRANC - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "6J JEN": ("JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "Bitcoin": ("BITCOIN - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "Ether": ("ETHER CASH SETTLED - CHICAGO MERCANTILE EXCHANGE", "LEGACY"),
    "CC Cacao": ("COCOA - ICE FUTURES U.S.", "LEGACY"),
    "KC Coffee": ("COFFEE C - ICE FUTURES U.S.", "LEGACY"),
    "CT Coton": ("COTTON NO. 2 - ICE FUTURES U.S.", "LEGACY"),
    "SB Sugar": ("SUGAR NO. 11 - ICE FUTURES U.S.", "LEGACY"),
    "ZC Corn (Mais)": ("CORN - CHICAGO BOARD OF TRADE", "LEGACY"),
    "ZS Soybeans (Soia)": ("SOYBEANS - CHICAGO BOARD OF TRADE", "LEGACY"),
    "ZL Soybeans Oil (Olia di soia)": ("SOYBEAN OIL - CHICAGO BOARD OF TRADE", "LEGACY"),
    "ZM Soybeans Meal (Farina di soia)": ("SOYBEAN MEAL - CHICAGO BOARD OF TRADE", "LEGACY"),
    "ZW Wheat SRW (Grano)": ("WHEAT-SRW - CHICAGO BOARD OF TRADE", "LEGACY"),
    "KE Wheat HRW (Grano)": ("WHEAT-HRW - CHICAGO BOARD OF TRADE", "LEGACY"),
    "30-DAY FEDERAL FUNDS": ("FED FUNDS - CHICAGO BOARD OF TRADE", "LEGACY"),
    "2-YEAR U.S. TREASURY NOTES": ("UST 2Y NOTE - CHICAGO BOARD OF TRADE", "LEGACY"),
    "5-YEAR U.S. TREASURY NOTES": ("UST 5Y NOTE - CHICAGO BOARD OF TRADE", "LEGACY"),
    "10-YEAR U.S. TREASURY NOTES": ("UST 10Y NOTE - CHICAGO BOARD OF TRADE", "LEGACY"),
    "Orange Juice": ("FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.", "LEGACY"),
    "Lumber": ("LUMBER - CHICAGO MERCANTILE EXCHANGE", "LEGACY")
}

asset_scelto = st.selectbox("Seleziona Mercato:", list(MERCATI.keys()))
nome_cftc, tipo_report = MERCATI[asset_scelto]

# Valori di default
val_oi_tot, val_oi_var = 174440, -9288
val_mm_long, val_mm_short = 1261, -3831
val_comm_long, val_comm_short = -5748, 1044

dati = fetch_cot_data(nome_cftc, tipo_report)

if dati:
    st.success(f"Dati sincronizzati: Report del {dati.get('report_date_as_yyyy_mm_dd', '')[:10]}")
    val_oi_tot = float(dati.get("open_interest_all", 0))
    val_oi_var = float(dati.get("change_in_open_interest_all", 0))
    
    if tipo_report == "LEGACY":
        val_mm_long = float(dati.get("change_in_noncomm_long_all", 0))
        val_mm_short = float(dati.get("change_in_noncomm_short_all", 0))
        val_comm_long = float(dati.get("change_in_comm_long_all", 0))
        val_comm_short = float(dati.get("change_in_comm_short_all", 0))
    else:
        val_mm_long = float(dati.get("change_in_lev_money_long_all", 0))
        val_mm_short = float(dati.get("change_in_lev_money_short_all", 0))
        val_comm_long = float(dati.get("change_in_dealer_long_all", 0))
        val_comm_short = float(dati.get("change_in_dealer_short_all", 0))

# =========================================================================
# BLOCCO 1: Inserimento Dati
# =========================================================================
st.header("1. Inserimento Dati")
st.caption("Trascrivi i dati dal blocco base del terminale")

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
    term_struct = st.radio(
        "Stato attuale della curva futures: inserimento manuale (non automatizzato)", 
        ["Backwardation (verde)", "Contango (rosso)"],
        index=1
    )

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
# BLOCCO 3: Matrice di Diagnosi Microstrutturale
# =========================================================================
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
    diag_comm = f"I Commercials assecondano la salita vendendo coperture sui massimi (Flusso: {flusso_netto_comm:+.0f}), tipico dei mercati sani."
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
st.info(f"- **Diagnosi OI:** {diag_oi}\n- **Diagnosi MM:** {diag_mm}\n- **Diagnosi Commercials:** {diag_comm}")
st.markdown(f"### Stato Operativo Ricalibrato: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)
st.success(f"**Azione Strategica:**\n- {azione}")
st.divider()

# =========================================================================
# BLOCCO 4: Interpretazione Macro e Sequenza Temporale (CORRETTO E SINCRONIZZATO)
# =========================================================================
st.header("4. Interpretazione Macro e Sequenza Temporale")

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE**")
    st.write("Siamo in una fase di **piena armonia rialzista**. I grandi speculatori stanno comprando in modo aggressivo e l'Open Interest sale. I commerciali stanno vendendo contratti commerciali per coprire la produzione futura, comportamento normalissimo in un mercato forte.")
    st.error("**💡 Conclusione:** Il trend è solido, asseconda il segnale Long e cerca conferme grafiche sul prezzo prima di operare.")

elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: SHORT ➔ LONG**")
    st.write("1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno vendendo pesantemente. Il prezzo risente della pressione immediata. 2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali stanno assorbendo tutto e accumulano Long. Stanno fabbricando un pavimento.")
    st.error("**💡 Conclusione:** Nel brevissimo è Short, ma monitora il grafico perché ci stiamo preparando a girarci Long.")

elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: LONG ➔ SHORT**")
    st.write("1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno spingendo il mercato verso l'alto o ricoprendo le vendite. Il prezzo attuale mostra ancora forza inerziale rialzista. 2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali ritengono che questi prezzi siano ottimi per fare coperture e stanno vendendo massicciamente. Stanno costruendo un tetto al mercato.")
    st.error("**💡 Conclusione:** Il trend di brevissimo è ancora Long, ma la Smart Money si sta posizionando Short per un'inversione ribassista nelle prossime settimane. Proteggi i profitti dei tuoi Long e non inseguire i massimi.")

elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write("Sia i grandi fondi che i commerciali stanno togliendo liquidità o aumentando i contratti short. Il mercato è strutturalmente debole a tutti i livelli temporali, la pressione ribassista è totale.")
else:
    st.info("🟡 **FASE DI TRANSIZIONE / FLUSSI MISTI**")
    st.write(f"I dati non mostrano una convergenza direzionale netta o l'Open Interest registra variazioni non indicative di trend forte (Variazione OI: {pct_delta_oi:.2f}%). I flussi tra speculatori e commerciali sono in fase di assestamento.")
    st.warning("**💡 Conclusione:** Il quadro macro è in una zona grigia. Nessuna forza direzionale dominante; attendi la configurazione di setup definiti prima di agire.")
