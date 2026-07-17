import streamlit as st
import requests

# =========================================================================
# CONFIGURAZIONE PAGINA
# =========================================================================
st.set_page_config(page_title="Dashboard COMM_COT_T1 (Auto)", layout="wide")
st.title("🛡️ Dashboard di Validazione — COT Automatico")
st.caption(
    "Dati scaricati in automatico dall'API pubblica e gratuita della CFTC "
    "(publicreporting.cftc.gov) — nessuna API key richiesta."
)

# =========================================================================
# COSTANTI: endpoint CFTC (Socrata) e preset di mercati comuni
# =========================================================================
DISAGG_URL = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"   # Disaggregated Futures Only (materie prime)
TFF_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"      # Traders in Financial Futures (valute/indici/tassi)

COMMODITY_PRESETS = {
    "Oro (COMEX)": "GOLD",
    "Argento (COMEX)": "SILVER",
    "Rame (COMEX)": "COPPER",
    "Petrolio WTI (NYMEX)": "WTI",
    "Gas Naturale (NYMEX)": "NAT GAS",
    "Grano SRW (CBOT)": "WHEAT-SRW",
    "Mais (CBOT)": "CORN",
    "Soia (CBOT)": "SOYBEANS",
    "Caffè (ICE)": "COFFEE",
    "Zucchero (ICE)": "SUGAR",
    "Cotone (ICE)": "COTTON",
}

FINANCIAL_PRESETS = {
    "Euro FX (CME)": "EURO FX",
    "Sterlina GBP (CME)": "BRITISH POUND",
    "Yen JPY (CME)": "JAPANESE YEN",
    "Dollaro Australiano (CME)": "AUSTRALIAN DOLLAR",
    "Dollaro Canadese (CME)": "CANADIAN DOLLAR",
    "Franco Svizzero (CME)": "SWISS FRANC",
    "S&P 500 E-mini (CME)": "E-MINI S&P 500",
    "Nasdaq 100 E-mini (CME)": "NASDAQ-100",
    "Dow Jones (CBOT)": "DOW JONES",
    "VIX (CBOE)": "VIX",
    "US 10Y Treasury Note (CBOT)": "10-YEAR U.S. TREASURY NOTES",
}

# =========================================================================
# FUNZIONI DI FETCH (con cache: i report CFTC escono una volta a settimana,
# quindi non ha senso richiamare l'API ad ogni rerun di Streamlit)
# =========================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def search_markets(base_url: str, query: str, limit: int = 20):
    """Cerca i nomi esatti dei mercati CFTC che contengono `query`."""
    if not query or len(query.strip()) < 2:
        return []
    params = {
        "$select": "market_and_exchange_names",
        "$group": "market_and_exchange_names",
        "$where": f"upper(market_and_exchange_names) like '%{query.strip().upper()}%'",
        "$limit": limit,
    }
    r = requests.get(base_url, params=params, timeout=15)
    r.raise_for_status()
    return sorted(row["market_and_exchange_names"] for row in r.json())


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_latest_report(base_url: str, market_name: str):
    """Scarica l'ultima riga (report più recente) per un mercato esatto."""
    safe_name = market_name.replace("'", "''")
    params = {
        "$where": f"market_and_exchange_names='{safe_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 1,
    }
    r = requests.get(base_url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else None


def to_num(row, key, default=0.0):
    try:
        return float(row.get(key, default))
    except (TypeError, ValueError):
        return default


# =========================================================================
# BLOCCO 1: Selezione automatica del mercato
# =========================================================================
st.header("1. Selezione automatica del mercato")

col_type, col_search, col_pick = st.columns([1, 1.3, 1.7])

with col_type:
    report_type = st.radio(
        "Categoria",
        ["Materie prime", "Valute / Indici / Tassi"],
        help=(
            "Materie prime → report 'Disaggregated' (Managed Money vs Producer/Merchant+Swap Dealer).\n"
            "Valute/Indici/Tassi → report 'TFF' (Leveraged Funds vs Dealer/Intermediary, "
            "l'analogo più vicino a MM/Commercials per questi strumenti)."
        ),
    )

base_url = DISAGG_URL if report_type == "Materie prime" else TFF_URL
presets = COMMODITY_PRESETS if report_type == "Materie prime" else FINANCIAL_PRESETS

with col_search:
    preset_label = st.selectbox("Preset rapido", ["— nessuno —"] + list(presets.keys()))
    free_query = st.text_input(
        "…oppure cerca liberamente (es. 'PLATINUM', 'BITCOIN')",
        value="" if preset_label == "— nessuno —" else presets[preset_label],
    )

with col_pick:
    matches = search_markets(base_url, free_query) if free_query else []
    if matches:
        selected_market = st.selectbox("Mercato esatto trovato su CFTC.gov", matches)
    else:
        selected_market = None
        if free_query:
            st.warning("Nessun mercato trovato con questo termine. Prova con un'altra parola chiave.")

fetch_col, info_col = st.columns([1, 3])
with fetch_col:
    do_fetch = st.button("🔄 Scarica ultimo report COT", type="primary", disabled=selected_market is None)

if do_fetch and selected_market:
    with st.spinner("Interrogo l'API CFTC..."):
        row = fetch_latest_report(base_url, selected_market)
    if row is None:
        st.error("Nessun dato restituito per questo mercato.")
    else:
        st.session_state["cot_row"] = row
        st.session_state["cot_market"] = selected_market
        st.session_state["cot_report_type"] = report_type

if "cot_row" in st.session_state:
    r = st.session_state["cot_row"]
    st.success(
        f"Ultimo report caricato: **{st.session_state['cot_market']}** — "
        f"settimana del **{r.get('report_date_as_yyyy_mm_dd', '')[:10]}**"
    )

st.divider()

# =========================================================================
# BLOCCO 2: Inserimento Dati (auto-popolato, ma sempre modificabile a mano)
# =========================================================================
st.header("2. Dati del report (modificabili)")
st.caption(
    "I campi sono pre-compilati con l'ultimo report CFTC scaricato. "
    "Puoi comunque correggerli a mano se necessario."
)

row = st.session_state.get("cot_row")
rtype = st.session_state.get("cot_report_type", report_type)

if row:
    oi_tot_default = to_num(row, "open_interest_all")
    oi_var_default = to_num(row, "change_in_open_interest_all")

    if rtype == "Materie prime":
        mm_long_default = to_num(row, "change_in_m_money_long_all")
        mm_short_default = to_num(row, "change_in_m_money_short_all")
    else:
        mm_long_default = to_num(row, "change_in_lev_money_long_all")
        mm_short_default = to_num(row, "change_in_lev_money_short_all")
else:
    oi_tot_default = 174440.0
    oi_var_default = -9288.0
    mm_long_default = 1261.0
    mm_short_default = -3831.0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.subheader("Open Interest")
    oi_tot = st.number_input("Open Interest Totale", value=oi_tot_default)
    oi_var = st.number_input("Change in Open Interest", value=oi_var_default)

with col2:
    st.subheader("Managed Money (MM)")
    mm_long = st.number_input("MM Change Long", value=mm_long_default)
    mm_short = st.number_input("MM Change Short", value=mm_short_default)

with col3:
    st.subheader("Commercials")
    if row and rtype == "Materie prime":
        include_swap = st.checkbox(
            "Includi Swap Dealer nei Commercials",
            value=True,
            help="Il 'Commercial' del report Legacy corrisponde a Producer/Merchant + Swap Dealer nel Disaggregated.",
        )
        comm_long_default = to_num(row, "change_in_prod_merc_long")
        comm_short_default = to_num(row, "change_in_prod_merc_short")
        if include_swap:
            comm_long_default += to_num(row, "change_in_swap_long_all")
            comm_short_default += to_num(row, "change_in_swap_short_all")
    elif row and rtype != "Materie prime":
        comm_long_default = to_num(row, "change_in_dealer_long_all")
        comm_short_default = to_num(row, "change_in_dealer_short_all")
    else:
        comm_long_default = -5748.0
        comm_short_default = 1044.0

    comm_long = st.number_input("Comm Change Long", value=comm_long_default)
    comm_short = st.number_input("Comm Change Short", value=comm_short_default)

with col4:
    st.subheader("Term Structure")
    st.caption("Non automatizzabile gratuitamente: richiede la curva futures live.")
    term_struct = st.radio(
        "Stato attuale (vedi indicatore in TradingView):",
        ["Backwardation (verde)", "Contango (rosso)"],
    )

# =========================================================================
# BLOCCO 3: Elaborazione Matematica (invariata)
# =========================================================================
pct_delta_oi = (oi_var / (oi_tot - oi_var)) * 100 if (oi_tot - oi_var) != 0 else 0
flusso_netto_mm = mm_long - mm_short
flusso_netto_comm = comm_long - comm_short

st.header("3. Elaborazione Matematica")
calc1, calc2, calc3 = st.columns(3)
calc1.metric("Variazione % Open Interest", f"{pct_delta_oi:.2f}%")
calc2.metric("Flusso Netto Speculativo (MM)", f"{flusso_netto_mm:+.0f}")
calc3.metric("Flusso Netto Commerciale", f"{flusso_netto_comm:+.0f}")

st.divider()

# =========================================================================
# BLOCCO 4 e 5: Matrice di Diagnosi e Azione Strategica (invariata)
# =========================================================================
st.header("4. Matrice di Diagnosi Microstrutturale: Il Verdetto")

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
st.info(f"""
- **Diagnosi OI:** {diag_oi}
- **Diagnosi MM:** {diag_mm}
- **Diagnosi Commercials:** {diag_comm}
""")

st.markdown(
    f"### Stato Operativo Ricalibrato: <span style='color:{stato_colore}'>{stato_testo}</span>",
    unsafe_allow_html=True,
)

st.success(f"""
**Azione Strategica:**
- {azione}
""")

st.divider()

# =========================================================================
# BLOCCO 6: Interpretazione Macro e Sequenza Temporale (invariata)
# =========================================================================
st.header("5. Interpretazione Macro e Sequenza Temporale")

if flusso_netto_mm > 0 and flusso_netto_comm < 0:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE (Allineato con TradingView)**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    Siamo in una fase di **piena armonia rialzista**. I grandi speculatori stanno comprando in modo aggressivo (Flusso: `{flusso_netto_mm:+.0f}`) e l'Open Interest sale. I commerciali stanno vendendo contratti per coprire la produzione futura, comportamento normalissimo in un mercato forte.
    """)
    st.error("💡 **Conclusione:** Il trend è solido, asseconda il segnale Long di TradingView e cerca conferme grafiche per l'operatività.")

elif flusso_netto_mm < 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: SHORT ➔ LONG**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno vendendo pesantemente (Flusso Speculativo: `{flusso_netto_mm:+.0f}`). Il prezzo risente della pressione immediata.
    2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali stanno assorbendo tutto e accumulano Long. Stanno fabbricando un pavimento.
    """)
    st.error("💡 **Conclusione:** Nel brevissimo è Short, ma monitora il grafico perché ci stiamo preparando a girarci Long.")

elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: LONG ➔ SHORT**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno spingendo il mercato verso l'alto o ricoprendo le vendite (Flusso Speculativo: `{flusso_netto_mm:+.0f}`). Il prezzo attuale mostra ancora forza inerziale rialzista.
    2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali ritengono che questi prezzi siano ottimi per fare coperture e stanno vendendo massicciamente (Flusso Commerciale: `{flusso_netto_comm:+.0f}`). Stanno costruendo un tetto al mercato.
    """)
    st.error("💡 **Conclusione:** Il trend di brevissimo è ancora Long, ma la Smart Money si sta posizionando Short per un'inversione ribassista nelle prossime settimane. Proteggi i profitti dei tuoi Long e non inseguire i massimi.")

elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write("""
    **Cosa sta succedendo in parole semplici:**
    Sia i grandi fondi che i commerciali stanno togliendo liquidità o aumentando i contratti short. Il mercato è strutturalmente debole a tutti i livelli temporali, la pressione ribassista è totale.
    """)

else:
    st.info("⚪ **FLUSSI IN EQUILIBRIO NEUTRO**")
    st.write("I flussi non mostrano sbilanciamenti direzionali o divergenze macroscopiche. Il mercato si trova in una fase di attesa o lateralità tecnica.")

st.divider()
st.caption(
    "Fonte dati: CFTC Commitments of Traders — publicreporting.cftc.gov (Disaggregated & TFF report). "
    "I report escono ogni venerdì pomeriggio (dati riferiti al martedì precedente)."
)
