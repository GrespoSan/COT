import streamlit as st
import yfinance as yf

# --- Configurazione Pagina ---
st.set_page_config(page_title="Dashboard COMM_COT_T1", layout="wide")
st.title("🛡️ Dashboard di Validazione")

# --- BLOCCO 1: Inserimento Dati (Rapporto COT) ---
st.header("1. Inserimento Dati")
st.caption("Trascrivi i dati dal blocco base del terminale")

col1, col2, col3, col4 = st.columns(4)
#cot_data = load_cot_data("GOLD")
with col1:
    st.subheader("Open Interest")
    # oi_tot = st.number_input("Open Interest Totale", value=174440)
    # oi_var = st.number_input("Change in Open Interest", value=-9288)
    oi_tot = cot_data["open_interest"]
    oi_var = cot_data["oi_change"]

with col2:
    st.subheader("Managed Money (MM)")
    # mm_long = st.number_input("MM Change Long", value=1261)
    # mm_short = st.number_input("MM Change Short", value=-3831)
    mm_long = cot_data["mm_long_change"]
    mm_short = cot_data["mm_short_change"]

with col3:
    st.subheader("Commercials")
    # comm_long = st.number_input("Comm Change Long", value=-5748)
    # comm_short = st.number_input("Comm Change Short", value=1044)
    comm_long = cot_data["comm_long_change"]
    comm_short = cot_data["comm_short_change"]

with col4:
    st.subheader("Term Structure")
    term_struct = st.radio("Stato attuale (inserimento manuale vedi indicatore in Tradingview):", ["Backwardation (verde)", "Contango (rosso)"])

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

# --- BLOCCO 3 e 4: Matrice di Diagnosi e Azione Strategica ---
st.header("3. Matrice di Diagnosi Microstrutturale: Il Verdetto")

# Inizializziamo le variabili di default
stato_colore = "orange"
stato_testo = "FASE DI TRANSIZIONE / INCERTEZZA"
verdetto = "Flussi misti in assestamento"
diag_oi = f"La variazione dell'OI ({pct_delta_oi:.2f}%) mostra un posizionamento standard."
diag_mm = f"I grandi fondi speculativi mantengono un flusso netto di {flusso_netto_mm:+.0f}."
diag_comm = f"I Commercials registrano un flusso netto di {flusso_netto_comm:+.0f}."
azione = "Resta in attesa di una chiara convergenza o divergenza strutturale."

# 1. SCENARIO CONVERGENT LONG (Massima Forza)
if flusso_netto_mm > 0 and flusso_netto_comm < 0 and pct_delta_oi > 0.5:
    stato_colore = "green"
    stato_testo = "CONVERGENT LONG / FORZA STRUTTURALE"
    verdetto = "Espansione Rialzista Istituzionale - Ingresso di Capitale Buyer [STADIO 1-A]"
    diag_oi = f"L'Open Interest è in forte espansione ({pct_delta_oi:.2f}%), confermando l'ingresso di nuova liquidità direzionale."
    diag_mm = f"I grandi fondi speculativi guidano il trend immettendo flussi nettamente rialzisti ({flusso_netto_mm:+.0f})."
    diag_comm = f"I Commercials assecondano la salita vendendo coperture sui massimi (Flusso: {flusso_netto_comm:+.0f}), tipico dei mercati sani."
    azione = "Valuta ingressi Long sui supporti volumetrici o mantieni i Long attivi piramidando sulla forza."

# 2. SCENARIO DISTRIBUZIONE / PERICOLO (Massima Debolezza)
elif flusso_netto_mm < 0 and flusso_netto_comm > 0 and pct_delta_oi > 0.5:
    stato_colore = "red"
    stato_testo = "DISTRIBUZIONE / PERICOLO"
    verdetto = "Fase di Distribuzione Istituzionale e Accumulo Short [STADIO 1-B]"
    diag_oi = f"L'Open Interest è in espansione ({pct_delta_oi:.2f}%), ma i contratti aperti sono guidati dai venditori."
    diag_mm = f"I fondi speculativi stanno immettendo massicci flussi ribassisti ({flusso_netto_mm:+.0f}), shortando il mercato."
    diag_comm = f"I Commercials stanno assorbendo la liquidità comprando a sconto (Flusso: {flusso_netto_comm:+.0f})."
    azione = "Chiudi o proteggi drasticamente le posizioni Long. Non comprare assolutamente in questa fase."

# 3. SCENARIO SHORT COVERING SQUEEZE
elif pct_delta_oi <= -0.5 and flusso_netto_mm > 0 and term_struct == "Backwardation (verde)":
    stato_colore = "green"
    stato_testo = "HOLD AGGRESSIVO / SQUEEZE"
    verdetto = "Short Covering Squeeze di continuazione strutturale [STADIO 3-B]"
    diag_oi = f"L'Open Interest subisce una contrazione massiccia ({pct_delta_oi:.2f}%), indicando la fuga dei venditori intrappolati."
    diag_mm = f"Flusso Speculativo positivo ({flusso_netto_mm:+.0f}) causato principalmente dalla chiusura forzata degli Short."
    diag_comm = f"Flusso Commercials: {flusso_netto_comm:+.0f}."
    azione = "Mantieni l'acquisto effettuato. Alza i target protettivi e stringi lo stop-loss sotto i minimi di struttura."

# Renderizzazione del Verdetto
st.markdown(f"#### **Il Verdetto:** {verdetto}")
st.info(f"""
- **Diagnosi OI:** {diag_oi}
- **Diagnosi MM:** {diag_mm}
- **Diagnosi Commercials:** {diag_comm}
""")

st.markdown(f"### Stato Operativo Ricalibrato: <span style='color:{stato_colore}'>{stato_testo}</span>", unsafe_allow_html=True)

st.success(f"""
**Azione Strategica:**
- {azione}
""")

st.divider()

# --- BLOCCO 4: Interpretazione Macro e Sequenza Temporale ---
st.header("4. Interpretazione Macro e Sequenza Temporale")

# Allineamento dinamico e interpretazione in parole semplici
if flusso_netto_mm > 0 and flusso_netto_comm < 0:
    st.success("🟢 **CONVERGENZA RIALZISTA STRUTTURALE (Allineato con TradingView)**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    Siamo in una fase di **piena armonia rialzista**. I grandi speculatori stanno comprando in modo aggressivo (Flusso: `{flusso_netto_mm:+.0f}`) e l'Open Interest sale. I commerciali stanno vendendo contratti commerciali per coprire la produzione futura, comportamento normalissimo in un mercato forte.
    """)
    st.error(f"""
    **💡 Conclusione:** Il trend è solido, asseconda il segnale Long di TradingView e cerca conferme grafiche per l'operatività.
    """)

elif flusso_netto_mm < 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: SHORT ➔ LONG**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno vendendo pesantemente (Flusso Speculativo: `{flusso_netto_mm:+.0f}`). Il prezzo risente della pressione immediata.
    2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali stanno assorbendo tutto e accumulano Long. Stanno fabbricando un pavimento.
    """)
    st.error(f"""
    **💡 Conclusione:** Nel brevissimo è Short, ma monitora il grafico perché ci stiamo preparando a girarci Long.
    """)

elif flusso_netto_mm > 0 and flusso_netto_comm > 0:
    st.warning("⚠️ **Rilevata DIVERGENZA ISTITUZIONALE: LONG ➔ SHORT**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    1. **OGGI / BREVE TERMINE:** I grandi fondi speculativi stanno spingendo il mercato verso l'alto o ricoprendo le vendite (Flusso Speculativo: `{flusso_netto_mm:+.0f}`). Il prezzo attuale mostra ancora forza inerziale rialzista.
    2. **PROSSIME SETTIMANE / MEDIO TERMINE:** I Commerciali ritengono che questi prezzi siano ottimi per fare coperture e stanno vendendo massicciamente (Flusso Commerciale: `{flusso_netto_comm:+.0f}`). Stanno costruendo un tetto al mercato.
    """)
    st.error(f"""
    **💡 Conclusione:** Il trend di brevissimo è ancora Long, ma la Smart Money si sta posizionando Short per un'inversione ribassista nelle prossime settimane. Proteggi i profitti dei tuoi Long e non inseguire i massimi.
    """)

elif flusso_netto_mm < 0 and flusso_netto_comm < 0:
    st.error("🔴 **CONVERGENZA RIBASSISTA STRUTTURALE**")
    st.write(f"""
    **Cosa sta succedendo in parole semplici:**
    Sia i grandi fondi che i commerciali stanno togliendo liquidità o aumentando i contratti short. Il mercato è strutturalmente debole a tutti i livelli temporali, la pressione ribassista è totale.
    """)

else:
    st.info("⚪ **FLUSSI IN EQUILIBRIO NEUTRO**")
    st.write("I flussi non mostrano sbilanciamenti direzionali o divergenze macroscopiche. Il mercato si trova in una fase di attesa o lateralità tecnica.")
