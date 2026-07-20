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
# BLOCCO 3: Matrice di Diagnosi Microstrutturale e Calcolo Bias
# =========================================================================
st.header("3. Matrice di Diagnosi Microstrutturale: Il Verdetto")

stato_colore = "orange"
stato_testo = "FASE DI TRANSIZIONE / INCERTEZZA"
verdetto = "Flussi misti in assestamento"
bias_testo = "NEUTRAL / MISTO"
bias_colore = "orange"

diag_oi = f"La variazione dell'OI ({pct_delta_oi:.2f}%) mostra un posizionamento standard."
diag_mm = f"I grandi fondi speculativi mantengono un flusso netto di {flusso_netto_mm:+.0f}."
diag_comm = f"I Commercials registrano un flusso netto di {flusso_netto_comm:+.0f}."
azione = "Resta in attesa di una chiara convergenza o divergenza strutturale."

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    stato_colore = "green"
    stato_testo = "CONVERGENT LONG / FORZA STRUTTURALE"
    verdetto = "Espansione Rialzista Istituzionale - Ingresso di Capitale Buyer [STADIO 1-A]"
    bias_testo = "CONVERGENT LONG"
    bias_colore = "green"
    diag_oi = f"L'Open Interest è in forte espansione ({pct_delta_oi:.2f}%), confermando l'ingresso di nuova liquidità direzionale."
    diag_mm = f"I grandi fondi speculativi guidano il trend immettendo flussi nettamente rialzisti ({flusso_netto_mm:+.0f})."
    diag_comm = f"I Commercials assecondano la salita vendendo coperture sui massimi (Flusso: {flusso_netto_comm:+.0f}), tipico dei mercati sani."
    azione = "Valuta ingressi Long sui supporti volumetrici o mantieni i Long attivi piramidando sulla forza."

elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    stato_colore = "red"
    stato_testo = "DISTRIBUZIONE / PERICOLO"
    verdetto = "Fase di Distribuzione Istituzionale e Accumulo Short [STADIO 1-B]"
    bias_testo = "DISTRIBUZIONE / SHORT"
    bias_colore = "red"
    diag_oi = f"L'Open Interest è in espansione ({pct_delta_oi:.2f}%), ma i contratti aperti sono guidati dai venditori."
    diag_mm = f"I fondi speculativi stanno immettendo massicci flussi ribassisti ({flusso_netto_mm:+.0f}), shortando il mercato."
    diag_comm = f"I Commercials stanno assorbendo la liquidità comprando a sconto (Flusso: {flusso_netto_comm:+.0f})."
    azione = "Chiudi o proteggi drasticamente le posizioni Long. Non comprare assolutamente in questa fase."

elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    stato_colore = "green"
    stato_testo = "HOLD AGGRESSIVO / SQUEEZE"
    verdetto = "Short Covering Squeeze di continuazione strutturale [STADIO 3-B]"
    bias_testo = "SQUEEZE LONG"
    bias_colore = "green"
    diag_oi = f"L'Open Interest subisce una contrazione massiccia ({pct_delta_oi:.2f}%), indicando la fuga dei venditori intrappolati."
    diag_mm = f"Flusso Speculativo positivo ({flusso_netto_mm:+.0f}) causato principalmente dalla chiusura forzata degli Short."
    diag_comm = f"Flusso Commercials: {flusso_netto_comm:+.0f}."
    azione = "Mantieni l'acquisto effettuato. Alza i target protettivi e stringi lo stop-loss sotto i minimi di struttura."

elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    bias_testo = "DIVERG. LONG ➔ SHORT"
    bias_colore = "orange"

elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    bias_testo = "CONVERGENT SHORT"
    bias_colore = "red"

st.markdown(f"#### **Il Verdetto:** {verdetto}")
st.info(f"- **Diagnosi OI:** {diag_oi}\n- **Diagnosi MM:** {diag_mm}\n- **Diagnosi Commercials:** {diag_comm}")

# Mostriamo a colpo d'occhio anche il Bias calcolato
st.markdown(f"### Bias di Mercato: <span style='color:{bias_colore}'>{bias_testo}</span>", unsafe_allow_html=True)
st.markdown(f"### Stato Operativo Ricalibrato: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)
st.success(f"**Azione Strategica:**\n- {azione}")
st.divider()

# =========================================================================
# BLOCCO 4: Interpretazione Macro e Sequenza Temporale (CORRETTO CON MARKDOWN)
# =========================================================================
st.header("4. Interpretazione Macro e Sequenza Temporale")

if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE [STADIO 1-A]**")
    st.markdown("Siamo in una fase di **piena armonia rialzista**. I grandi speculatori stanno comprando in modo aggressivo e l'Open Interest sale. I commerciali stanno vendendo contratti di copertura sui massimi, comportamento normalissimo in un mercato forte.")
    st.error("**💡 Conclusione:** Il trend è solido, asseconda il segnale Long e cerca conferme grafiche sul prezzo prima di operare.")

elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    st.error("🔴 **PRESSIONE RIBASSISTA / DISTRIBUZIONE ISTITUZIONALE [STADIO 1-B]**")
    st.markdown("1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno spingendo pesantemente al ribasso (flusso netto negativo), e il mercato risente di questa pressione immediata.")
    st.markdown("2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali stanno assorbendo la liquidità a sconto comprando contratti long. In regime di Contango, questo accumulo non anticipa un'inversione immediata al rialzo, bensì una fase di copertura passiva o di accumulo difensivo in un contesto di debolezza.")
    st.warning("**💡 Conclusione:** Il quadro resta orientato alla debolezza o alla distribuzione. La pressione ribassista dei fondi comanda il brevissimo termine: evita categoricamente di comprare in questa fase.")

elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    st.success("🟢 **SHORT COVERING SQUEEZE [STADIO 3-B]**")
    st.markdown("1. **OGGI / BREVE TERMINE:** L'Open Interest crolla mentre i prezzi salgono o reagiscono; i venditori scoperti stanno subendo una ricopertura forzata (stop loss saltati).")
    st.markdown("2. **PROSSIME SETTIMANE / MEDIO TERMINE:** Il movimento è alimentato dall'uscita di forza degli short e non da nuovo denaro fresco in acquisto strutturale, ma la spinta di prezzo è violenta.")
    st.error("**💡 Conclusione:** Dinamica di squeeze in atto. Mantieni la posizione long protetta da trailing stop stretti, sfruttando la debolezza dei venditori intrappolati.")

elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **DIVERGENZA ISTITUZIONALE: LONG ➔ SHORT**")
    st.markdown("1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno spingendo il mercato verso l'alto o ricoprendo le vendite. Il prezzo attuale mostra ancora forza inerziale rialzista.")
    st.markdown("2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali ritengono che questi prezzi siano ottimi per fare coperture e stanno vendendo massicciamente. Stanno costruendo un tetto al mercato.")
    st.error("**💡 Conclusione:** Il trend di brevissimo è ancora Long, ma la Smart Money si sta posizionando Short per un'inversione ribassista nelle prossime settimane. Proteggi i profitti dei tuoi Long e non inseguire i massimi.")

elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.markdown("Sia i grandi fondi che i commerciali stanno togliendo liquidità o aumentando i contratti short. Il mercato è strutturalmente debole a tutti i livelli temporali, la pressione ribassista è totale.")
else:
    st.info("🟡 **FASE DI TRANSIZIONE / FLUSSI MISTI**")
    st.markdown(f"I dati non mostrano una convergenza direzionale netta o l'Open Interest registra variazioni non indicative di trend forte (Variazione OI: {pct_delta_oi:.2f}%). I flussi tra speculatori e commerciali sono in fase di assestamento.")
    st.warning("**💡 Conclusione:** Il quadro macro è in una zona grigia. Nessuna forza direzionale dominante; attendi la configurazione di setup definiti prima di agire.")
    
# =========================================================================
# BLOCCO 5: Analisi Automatica con Gemini
# =========================================================================
st.header("5. Analisi e Commento di Gemini")

if st.button("Genera Analisi con Gemini"):
    with st.spinner("Interrogo Gemini in corso..."):
        try:
            # Importazione locale per garantire che il modulo sia sempre definito
            from google import genai
            
            # Prende la chiave direttamente dai segreti di Streamlit
            api_key = st.secrets["GEMINI_API_KEY"]
            
            # Inizializza il client Google GenAI
            client = genai.Client(api_key=api_key)
            
            # Prepara il prompt strutturato con i dati attuali della dashboard
            prompt_utente = f"""
            Analizza questi dati del report COT per il mercato {asset_scelto} in data {dati.get('report_date_as_yyyy_mm_dd', '')[:10]}:
            - Open Interest Totale: {oi_tot} (Variazione: {oi_var}, %: {pct_delta_oi:.2f}%)
            - Flusso Netto Speculativo (MM): {flusso_netto_mm:+.0f}
            - Flusso Netto Commerciale: {flusso_netto_comm:+.0f}
            - Stato della struttura: {term_struct}
            - Verdetto tecnico della dashboard: {verdetto} ({stato_testo})
            
            Fornisci una sintesi operativa concisa, evidenziando cosa stanno facendo i grandi operatori e un giudizio di sintesi con un semaforo (🟢, 🔴 o 🟡).
            """
            
            # Chiamata al modello corretto
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt_utente,
            )
            
            # Mostra la risposta nell'app
            st.markdown("### Risposta dell'AI:")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"Errore durante la comunicazione con Gemini: {e}")
