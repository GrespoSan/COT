from __future__ import annotations

from typing import Any

import requests
import streamlit as st


# ============================================================================
# CONFIGURAZIONE PAGINA
# ============================================================================
st.set_page_config(
    page_title="Dashboard COT — Ultimo vs Penultimo",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Dashboard di Validazione COT")
st.caption(
    "Analisi deterministica del report Legacy Futures Only: "
    "ultimo report confrontato con il penultimo."
)


# ============================================================================
# CONFIGURAZIONE CFTC
# ============================================================================
CFTC_LEGACY_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

CFTC_FIELDS = ",".join(
    [
        "report_date_as_yyyy_mm_dd",
        "open_interest_all",
        "noncomm_positions_long_all",
        "noncomm_positions_short_all",
        "comm_positions_long_all",
        "comm_positions_short_all",
    ]
)


# ============================================================================
# MAPPATURA MERCATI
# ============================================================================
MERCATI: dict[str, str] = {
    "S&P 500": "S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE",
    "Nasdaq 100": "NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE",
    "Dow Jones": "DJIA x $5 - CHICAGO BOARD OF TRADE",
    "Russell 2000": "RUSSELL E-MINI - CHICAGO MERCANTILE EXCHANGE",
    "CL WTI (Petrolio)": "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE",
    "RB Gasoline RBOB": "GASOLINE RBOB - NEW YORK MERCANTILE EXCHANGE",
    "Natural Gas": "NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE",
    "Gold (Oro)": "GOLD - COMMODITY EXCHANGE INC.",
    "Silver (Argento)": "SILVER - COMMODITY EXCHANGE INC.",
    "Copper (Rame)": "COPPER - COMMODITY EXCHANGE INC.",
    "PL Platino": "PLATINUM - NEW YORK MERCANTILE EXCHANGE",
    "PA Palladium": "PALLADIUM - NEW YORK MERCANTILE EXCHANGE",
    "DX1 USD": "USD INDEX - ICE FUTURES U.S.",
    "6E Euro": "EURO FX - CHICAGO MERCANTILE EXCHANGE",
    "6B GBP": "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
    "6A AUD": "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "6N NZD": "NZ DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "6C CAD": "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "6S CHF": "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE",
    "6J JPY": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
    "Bitcoin": "BITCOIN - CHICAGO MERCANTILE EXCHANGE",
    "Ether": "ETHER CASH SETTLED - CHICAGO MERCANTILE EXCHANGE",
    "CC Cacao": "COCOA - ICE FUTURES U.S.",
    "KC Coffee": "COFFEE C - ICE FUTURES U.S.",
    "CT Cotone": "COTTON NO. 2 - ICE FUTURES U.S.",
    "SB Sugar": "SUGAR NO. 11 - ICE FUTURES U.S.",
    "ZC Corn (Mais)": "CORN - CHICAGO BOARD OF TRADE",
    "ZS Soybeans (Soia)": "SOYBEANS - CHICAGO BOARD OF TRADE",
    "ZL Soybean Oil": "SOYBEAN OIL - CHICAGO BOARD OF TRADE",
    "ZM Soybean Meal": "SOYBEAN MEAL - CHICAGO BOARD OF TRADE",
    "ZW Wheat SRW": "WHEAT-SRW - CHICAGO BOARD OF TRADE",
    "KE Wheat HRW": "WHEAT-HRW - CHICAGO BOARD OF TRADE",
    "30-Day Federal Funds": "FED FUNDS - CHICAGO BOARD OF TRADE",
    "2-Year U.S. Treasury Notes": "UST 2Y NOTE - CHICAGO BOARD OF TRADE",
    "5-Year U.S. Treasury Notes": "UST 5Y NOTE - CHICAGO BOARD OF TRADE",
    "10-Year U.S. Treasury Notes": "UST 10Y NOTE - CHICAGO BOARD OF TRADE",
    "Orange Juice": "FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.",
    "Lumber": "LUMBER - CHICAGO MERCANTILE EXCHANGE",
}


# ============================================================================
# FUNZIONI DI SUPPORTO
# ============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cot_reports(market_name: str) -> tuple[list[dict[str, Any]], str | None]:
    """Scarica gli ultimi due report COT Legacy Futures Only."""
    safe_market_name = market_name.replace("'", "''")
    params = {
        "$select": CFTC_FIELDS,
        "$where": f"market_and_exchange_names='{safe_market_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 2,
    }

    try:
        response = requests.get(
            CFTC_LEGACY_URL,
            params=params,
            timeout=20,
            headers={"User-Agent": "COT-Dashboard/2.0"},
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list):
            return [], "La risposta CFTC non ha il formato previsto."

        return payload, None

    except requests.Timeout:
        return [], "Timeout durante il collegamento ai server CFTC."
    except requests.RequestException as exc:
        return [], f"Errore durante il recupero dei dati CFTC: {exc}"
    except ValueError:
        return [], "La risposta CFTC non contiene JSON valido."


def to_float(record: dict[str, Any], key: str) -> float:
    """Converte un campo CFTC in float senza interrompere l'app."""
    try:
        value = record.get(key, 0)
        return float(value) if value not in (None, "") else 0.0
    except (TypeError, ValueError, AttributeError):
        return 0.0


def report_date(record: dict[str, Any]) -> str:
    value = str(record.get("report_date_as_yyyy_mm_dd", "N/D"))
    return value[:10] if value else "N/D"


def fmt_number(value: float, signed: bool = False) -> str:
    if signed:
        return f"{value:+,.0f}".replace(",", ".")
    return f"{value:,.0f}".replace(",", ".")


def fmt_pct(value: float) -> str:
    return f"{value:+.2f}%"


def build_position_diagnosis(
    category: str,
    delta_long: float,
    delta_short: float,
    net_flow: float,
) -> str:
    if delta_long > 0 and delta_short < 0:
        return (
            f"I {category} aumentano i Long e riducono gli Short: "
            "la Net Position migliora in modo completo."
        )

    if delta_long < 0 and delta_short > 0:
        return (
            f"I {category} riducono i Long e aumentano gli Short: "
            "la Net Position peggiora in modo completo."
        )

    if net_flow > 0:
        return (
            f"La Net Position dei {category} migliora, "
            "ma Long e Short mostrano un comportamento misto."
        )

    if net_flow < 0:
        return (
            f"La Net Position dei {category} peggiora, "
            "ma Long e Short mostrano un comportamento misto."
        )

    return f"I {category} mostrano un flusso netto sostanzialmente stabile."


# ============================================================================
# SELEZIONE MERCATO E DATI
# ============================================================================
asset_scelto = st.selectbox("Seleziona mercato", list(MERCATI.keys()))
nome_cftc = MERCATI[asset_scelto]

with st.spinner("Recupero degli ultimi due report CFTC..."):
    reports, fetch_error = fetch_cot_reports(nome_cftc)

if fetch_error:
    st.error(fetch_error)
    st.stop()

if len(reports) < 2:
    st.error(
        "Non sono disponibili due report COT consecutivi per il mercato selezionato."
    )
    st.stop()

current = reports[0]
previous = reports[1]

current_date = report_date(current)
previous_date = report_date(previous)

oi_current = to_float(current, "open_interest_all")
oi_previous = to_float(previous, "open_interest_all")

noncomm_long_current = to_float(current, "noncomm_positions_long_all")
noncomm_long_previous = to_float(previous, "noncomm_positions_long_all")
noncomm_short_current = to_float(current, "noncomm_positions_short_all")
noncomm_short_previous = to_float(previous, "noncomm_positions_short_all")

comm_long_current = to_float(current, "comm_positions_long_all")
comm_long_previous = to_float(previous, "comm_positions_long_all")
comm_short_current = to_float(current, "comm_positions_short_all")
comm_short_previous = to_float(previous, "comm_positions_short_all")

delta_oi = oi_current - oi_previous
delta_noncomm_long = noncomm_long_current - noncomm_long_previous
delta_noncomm_short = noncomm_short_current - noncomm_short_previous
delta_comm_long = comm_long_current - comm_long_previous
delta_comm_short = comm_short_current - comm_short_previous

pct_delta_oi = (delta_oi / oi_previous) * 100 if oi_previous != 0 else 0.0
net_flow_noncomm = delta_noncomm_long - delta_noncomm_short
net_flow_comm = delta_comm_long - delta_comm_short

st.success(
    f"Dati sincronizzati: report {current_date} confrontato con {previous_date}."
)

term_structure = st.radio(
    "Term Structure",
    options=["Contango", "Backwardation"],
    horizontal=True,
    help=(
        "La CFTC non fornisce la curva dei contratti. "
        "Per ottenere lo stesso responso del Pine seleziona lo stato mostrato su TradingView."
    ),
)
is_backwardation = term_structure == "Backwardation"


# ============================================================================
# DATI DI BASE
# ============================================================================
st.header("1. Ultimo report confrontato con il penultimo")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Open Interest attuale", fmt_number(oi_current))
col2.metric("Δ Open Interest", fmt_number(delta_oi, signed=True), fmt_pct(pct_delta_oi))
col3.metric("Flusso netto Noncommercial", fmt_number(net_flow_noncomm, signed=True))
col4.metric("Flusso netto Commercial", fmt_number(net_flow_comm, signed=True))

comparison_rows = [
    {
        "Voce": "Open Interest",
        f"Report {previous_date}": fmt_number(oi_previous),
        f"Report {current_date}": fmt_number(oi_current),
        "Variazione": fmt_number(delta_oi, signed=True),
    },
    {
        "Voce": "Noncommercial Long",
        f"Report {previous_date}": fmt_number(noncomm_long_previous),
        f"Report {current_date}": fmt_number(noncomm_long_current),
        "Variazione": fmt_number(delta_noncomm_long, signed=True),
    },
    {
        "Voce": "Noncommercial Short",
        f"Report {previous_date}": fmt_number(noncomm_short_previous),
        f"Report {current_date}": fmt_number(noncomm_short_current),
        "Variazione": fmt_number(delta_noncomm_short, signed=True),
    },
    {
        "Voce": "Commercial Long",
        f"Report {previous_date}": fmt_number(comm_long_previous),
        f"Report {current_date}": fmt_number(comm_long_current),
        "Variazione": fmt_number(delta_comm_long, signed=True),
    },
    {
        "Voce": "Commercial Short",
        f"Report {previous_date}": fmt_number(comm_short_previous),
        f"Report {current_date}": fmt_number(comm_short_current),
        "Variazione": fmt_number(delta_comm_short, signed=True),
    },
]

st.dataframe(comparison_rows, width="stretch", hide_index=True)


# ============================================================================
# LOGICA BIAS — STESSO ORDINE DEL PINE
# ============================================================================
is_stadio_1a = (
    net_flow_noncomm > 0
    and net_flow_comm < 0
    and pct_delta_oi > 0.5
)

is_stadio_1b = (
    net_flow_noncomm < 0
    and net_flow_comm > 0
    and pct_delta_oi > 0.5
)

is_squeeze = (
    pct_delta_oi <= -0.5
    and net_flow_noncomm > 0
    and is_backwardation
)

is_div_short = net_flow_noncomm > 0 and net_flow_comm > 0
is_conv_short = net_flow_noncomm < 0 and net_flow_comm < 0

bias_testo = "NEUTRAL / MISTO"
bias_colore = "#9A6700"
verdetto = "Flussi misti in assestamento."
stato_testo = "FASE DI TRANSIZIONE / INCERTEZZA"
azione = "Attendi una configurazione più chiara prima di aumentare l'esposizione."

if is_stadio_1a:
    bias_testo = "CONVERGENZA LONG"
    bias_colore = "#15803D"
    verdetto = "Convergenza rialzista tra Noncommercial e Commercial."
    stato_testo = "FORZA RIALZISTA NELL'ULTIMO REPORT"
    azione = "Cerca conferme del prezzo sui supporti prima di aumentare l'esposizione long."

elif is_stadio_1b:
    bias_testo = "DISTRIBUZIONE / SHORT"
    bias_colore = "#B91C1C"
    verdetto = "Pressione ribassista con Open Interest in espansione."
    stato_testo = "PRESSIONE SHORT NELL'ULTIMO REPORT"
    azione = "Evita nuovi long e attendi un miglioramento dei flussi."

elif is_squeeze:
    bias_testo = "SHORT COVERING SQUEEZE"
    bias_colore = "#15803D"
    verdetto = "Miglioramento speculativo con Open Interest in contrazione e Backwardation."
    stato_testo = "SQUEEZE IN CORSO"
    azione = "Non inseguire il movimento e proteggi le posizioni già aperte."

elif is_div_short:
    bias_testo = "DIVERG. LONG ➔ SHORT"
    bias_colore = "#C2410C"
    verdetto = "Divergenza tra Noncommercial e Commercial."
    stato_testo = "POSSIBILE PRIMO DETERIORAMENTO"
    azione = "Proteggi gli eventuali long e attendi una nuova convergenza."

elif is_conv_short:
    bias_testo = "CONVERGENZA SHORT"
    bias_colore = "#B91C1C"
    verdetto = "Convergenza ribassista dei flussi netti."
    stato_testo = "PRESSIONE RIBASSISTA CONDIVISA"
    azione = "Evita acquisti in controtendenza e attendi un miglioramento dei flussi."


# ============================================================================
# DIAGNOSI
# ============================================================================
diag_noncomm = build_position_diagnosis(
    "Noncommercial",
    delta_noncomm_long,
    delta_noncomm_short,
    net_flow_noncomm,
)

diag_comm = build_position_diagnosis(
    "Commercial",
    delta_comm_long,
    delta_comm_short,
    net_flow_comm,
)

if pct_delta_oi > 0.5:
    diag_oi = (
        f"L'Open Interest aumenta del {pct_delta_oi:.2f}%: "
        "la partecipazione al mercato è in espansione."
    )
elif pct_delta_oi <= -0.5:
    diag_oi = (
        f"L'Open Interest diminuisce del {abs(pct_delta_oi):.2f}%: "
        "la partecipazione al mercato è in contrazione."
    )
else:
    diag_oi = (
        f"L'Open Interest varia del {pct_delta_oi:.2f}%: "
        "la partecipazione non mostra un'espansione significativa."
    )

diag_term = (
    "La Backwardation offre una conferma positiva proveniente dal contratto più vicino."
    if is_backwardation
    else "Il Contango non offre una conferma rialzista immediata dalla curva futures."
)


# ============================================================================
# CONCLUSIONE AUTOMATICA — SOLO ULTIMO VS PENULTIMO
# ============================================================================
if is_stadio_1a:
    frase_bias = (
        "Nell'ultimo report è comparsa una convergenza rialzista tra "
        "Noncommercial e Commercial, accompagnata da un aumento dell'Open Interest."
    )
elif is_stadio_1b:
    frase_bias = (
        "Nell'ultimo report è comparsa una pressione ribassista, con deterioramento "
        "dei Noncommercial e miglioramento della Net Position dei Commercial."
    )
elif is_squeeze:
    frase_bias = (
        "Nell'ultimo report è emersa una dinamica di short covering squeeze, "
        "con miglioramento dei Noncommercial e contrazione dell'Open Interest."
    )
elif is_div_short:
    frase_bias = (
        "Nell'ultimo report è comparsa una divergenza tra Noncommercial e Commercial, "
        "che rappresenta un possibile primo deterioramento del precedente quadro rialzista."
    )
elif is_conv_short:
    frase_bias = (
        "Nell'ultimo report Noncommercial e Commercial mostrano una convergenza ribassista, "
        "indicando una pressione short condivisa."
    )
else:
    frase_bias = (
        "Nell'ultimo report i flussi non mostrano una direzione istituzionale "
        "sufficientemente chiara."
    )

conclusione_automatica = f"{frase_bias} {diag_oi} {diag_term} Il quadro suggerisce di {azione[0].lower() + azione[1:]}"


# ============================================================================
# OUTPUT
# ============================================================================
st.header("2. Responso dell'ultimo report")

st.markdown(
    f"""
    <div style="
        border:1px solid #B8B8B8;
        border-left:8px solid {bias_colore};
        border-radius:8px;
        padding:16px 18px;
        margin-bottom:14px;
        background:rgba(127,127,127,0.06);
    ">
        <div style="font-size:0.85rem;font-weight:700;">BIAS ATTUALE</div>
        <div style="font-size:1.45rem;font-weight:800;color:{bias_colore};">{bias_testo}</div>
        <div style="margin-top:8px;"><b>Verdetto:</b> {verdetto}</div>
        <div><b>Stato:</b> {stato_testo}</div>
        <div><b>Term Structure:</b> {term_structure}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Diagnosi tecnica")
st.info(
    f"**Open Interest**\n\n{diag_oi}\n\n"
    f"**Noncommercial**\n\n{diag_noncomm}\n\n"
    f"**Commercial**\n\n{diag_comm}\n\n"
    f"**Term Structure**\n\n{diag_term}"
)

st.subheader("Indicazione operativa")
if bias_colore == "#15803D":
    st.success(azione)
elif bias_colore == "#B91C1C":
    st.error(azione)
else:
    st.warning(azione)

st.subheader("Conclusione automatica")
st.write(conclusione_automatica)

# ============================================================================
# ANALISI E COMMENTO CON AI
# ============================================================================
st.header("3. Analisi e commento con AI")
st.caption(
    "L'AI commenta il responso deterministico già calcolato. "
    "Non modifica il Bias e non introduce il confronto 3-6 settimane."
)

ai_provider = st.selectbox(
    "Provider AI",
    ["Google Gemini", "Groq"],
)

default_gemini_model = st.secrets.get("GEMINI_MODEL", "gemini-3.5-flash")
default_groq_model = st.secrets.get("GROQ_MODEL", "llama-3.3-70b-versatile")

if ai_provider == "Google Gemini":
    ai_model = st.text_input("Modello Gemini", value=default_gemini_model)
else:
    ai_model = st.text_input("Modello Groq", value=default_groq_model)

if st.button("Genera analisi con AI", type="primary"):
    prompt_utente = f"""
Analizza il seguente report COT Legacy Futures Only per il mercato {asset_scelto}.

Confronto:
- Ultimo report: {current_date}
- Penultimo report: {previous_date}

Dati calcolati:
- Open Interest attuale: {oi_current:.0f}
- Variazione Open Interest: {delta_oi:+.0f} ({pct_delta_oi:+.2f}%)
- Variazione Noncommercial Long: {delta_noncomm_long:+.0f}
- Variazione Noncommercial Short: {delta_noncomm_short:+.0f}
- Flusso netto Noncommercial: {net_flow_noncomm:+.0f}
- Variazione Commercial Long: {delta_comm_long:+.0f}
- Variazione Commercial Short: {delta_comm_short:+.0f}
- Flusso netto Commercial: {net_flow_comm:+.0f}
- Term Structure: {term_structure}

Responso deterministico:
- Bias: {bias_testo}
- Verdetto: {verdetto}
- Stato: {stato_testo}
- Indicazione operativa: {azione}

Diagnosi:
- Open Interest: {diag_oi}
- Noncommercial: {diag_noncomm}
- Commercial: {diag_comm}
- Term Structure: {diag_term}

Conclusione automatica:
{conclusione_automatica}

Scrivi una sintesi operativa chiara e concisa in italiano.
Mantieni il responso coerente con i dati forniti.
Non inventare dati mancanti.
Non introdurre analisi a 3 o 6 settimane.
Non trasformare il COT in un segnale immediato di ingresso.
Concludi con un semaforo finale: 🟢, 🟡 oppure 🔴.
"""

    with st.spinner(f"Interrogo {ai_provider}..."):
        try:
            if ai_provider == "Google Gemini":
                from google import genai

                api_key = st.secrets["GEMINI_API_KEY"]
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=ai_model,
                    contents=prompt_utente,
                )
                risposta_ai = response.text or "Nessuna risposta ricevuta da Gemini."

            else:
                from groq import Groq

                api_key = st.secrets["GROQ_API_KEY"]
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model=ai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Sei un analista COT. Rispetta rigorosamente i dati forniti, "
                                "non inventare dati e non introdurre analisi 3-6 settimane."
                            ),
                        },
                        {"role": "user", "content": prompt_utente},
                    ],
                    temperature=0.2,
                )
                risposta_ai = response.choices[0].message.content

            st.markdown("### Risposta dell'AI")
            st.write(risposta_ai)

        except KeyError as exc:
            st.error(
                f"Chiave API mancante nei Secrets di Streamlit: {exc}. "
                "Configura GEMINI_API_KEY oppure GROQ_API_KEY."
            )
        except Exception as exc:
            error_text = str(exc)
            if "503" in error_text or "UNAVAILABLE" in error_text:
                st.warning(
                    "Il provider AI è temporaneamente non disponibile. "
                    "Riprova più tardi oppure seleziona l'altro provider."
                )
            else:
                st.error(f"Errore durante la comunicazione con l'AI: {exc}")

st.divider()
st.warning(
    "Il report COT è un dato settimanale ritardato: descrive il posizionamento "
    "rilevato alla data del report e va utilizzato come contesto, non come segnale "
    "immediato di ingresso. Questa versione confronta esclusivamente ultimo e "
    "penultimo report; non calcola la struttura 3–6 settimane né i COT Index."
)
