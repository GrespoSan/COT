from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
import io
import math
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf


# =============================================================================
# CONFIGURAZIONE PAGINA
# =============================================================================
st.set_page_config(
    page_title="COT Smart Money — Python",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2rem;}
    .cot-card {
        border: 1px solid rgba(128,128,128,.35);
        border-left: 8px solid var(--accent);
        border-radius: 10px;
        padding: 16px 18px;
        margin: 4px 0 14px 0;
        background: rgba(127,127,127,.055);
    }
    .cot-kicker {font-size:.78rem; font-weight:800; letter-spacing:.04em; opacity:.8;}
    .cot-title {font-size:1.42rem; font-weight:850; color:var(--accent); margin:.15rem 0 .45rem 0;}
    .cot-small {font-size:.93rem; line-height:1.45;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ COT Smart Money — versione Python")
st.caption(
    "Dashboard deterministica basata sui report CFTC Futures Only. "
    "Seleziona automaticamente TFF per i finanziari e Disaggregated per le commodity."
)


# =============================================================================
# COSTANTI CFTC
# =============================================================================
CFTC_DATASETS = {
    "Legacy": "6dca-aqww",
    "Disaggregated": "72hh-3qpy",
    "Financial": "gpe5-46if",
}

CFTC_API_BASES = (
    "https://publicreporting.cftc.gov/resource",
    "https://publicreportinghub.cftc.gov/resource",
)

TERM_OPTIONS = ["Non disponibile", "Contango", "Backwardation", "Curva piatta"]


@dataclass(frozen=True)
class MarketSpec:
    label: str
    root: str
    group: str
    family: str  # commodity | financial
    is_fx: bool
    preferred_name: str
    search_terms: tuple[str, ...]
    yahoo_ticker: str

    @property
    def specific_report(self) -> str:
        return "Disaggregated" if self.family == "commodity" else "Financial"

    @property
    def trend_label(self) -> str:
        return "Managed Money" if self.family == "commodity" else "Leveraged Funds"

    @property
    def counter_label(self) -> str:
        if self.family == "commodity":
            return "Producer / Merchant"
        if self.is_fx:
            return "Dealer / Intermediary"
        return "Asset Manager"

    @property
    def market_family_label(self) -> str:
        if self.family == "commodity":
            return "COMMODITY"
        if self.is_fx:
            return "VALUTE"
        return "FINANZIARI"


# La lista conserva i mercati già presenti nella prima app e aggiunge alcuni
# contratti previsti dal motore Pine.
MARKETS: tuple[MarketSpec, ...] = (
    # Indici e volatilità
    MarketSpec("ES — S&P 500", "ES", "Indici", "financial", False, "S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE", ("S&P 500", "CONSOLIDATED"), "ES=F"),
    MarketSpec("NQ — Nasdaq 100", "NQ", "Indici", "financial", False, "NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE", ("NASDAQ MINI", "NASDAQ"), "NQ=F"),
    MarketSpec("YM — Dow Jones", "YM", "Indici", "financial", False, "DJIA x $5 - CHICAGO BOARD OF TRADE", ("DJIA", "$5"), "YM=F"),
    MarketSpec("RTY — Russell 2000", "RTY", "Indici", "financial", False, "RUSSELL E-MINI - CHICAGO MERCANTILE EXCHANGE", ("RUSSELL", "E-MINI"), "RTY=F"),
    MarketSpec("VX — VIX Futures", "VX", "Indici", "financial", False, "VIX FUTURES - CBOE FUTURES EXCHANGE", ("VIX",), "^VIX"),

    # Valute
    MarketSpec("DX — U.S. Dollar Index", "DX", "Valute", "financial", True, "USD INDEX - ICE FUTURES U.S.", ("USD INDEX",), "DX-Y.NYB"),
    MarketSpec("6E — Euro FX", "6E", "Valute", "financial", True, "EURO FX - CHICAGO MERCANTILE EXCHANGE", ("EURO FX",), "6E=F"),
    MarketSpec("6B — British Pound", "6B", "Valute", "financial", True, "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE", ("BRITISH POUND",), "6B=F"),
    MarketSpec("6A — Australian Dollar", "6A", "Valute", "financial", True, "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE", ("AUSTRALIAN DOLLAR",), "6A=F"),
    MarketSpec("6N — New Zealand Dollar", "6N", "Valute", "financial", True, "NZ DOLLAR - CHICAGO MERCANTILE EXCHANGE", ("NZ DOLLAR", "NEW ZEALAND"), "6N=F"),
    MarketSpec("6C — Canadian Dollar", "6C", "Valute", "financial", True, "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE", ("CANADIAN DOLLAR",), "6C=F"),
    MarketSpec("6S — Swiss Franc", "6S", "Valute", "financial", True, "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE", ("SWISS FRANC",), "6S=F"),
    MarketSpec("6J — Japanese Yen", "6J", "Valute", "financial", True, "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE", ("JAPANESE YEN",), "6J=F"),

    # Tassi
    MarketSpec("ZQ — 30-Day Federal Funds", "ZQ", "Tassi", "financial", False, "FED FUNDS - CHICAGO BOARD OF TRADE", ("FED FUNDS",), "ZQ=F"),
    MarketSpec("ZT — U.S. Treasury 2Y", "ZT", "Tassi", "financial", False, "UST 2Y NOTE - CHICAGO BOARD OF TRADE", ("UST 2Y", "2Y NOTE"), "ZT=F"),
    MarketSpec("ZF — U.S. Treasury 5Y", "ZF", "Tassi", "financial", False, "UST 5Y NOTE - CHICAGO BOARD OF TRADE", ("UST 5Y", "5Y NOTE"), "ZF=F"),
    MarketSpec("ZN — U.S. Treasury 10Y", "ZN", "Tassi", "financial", False, "UST 10Y NOTE - CHICAGO BOARD OF TRADE", ("UST 10Y", "10Y NOTE"), "ZN=F"),
    MarketSpec("ZB — U.S. Treasury Bond", "ZB", "Tassi", "financial", False, "UST BOND - CHICAGO BOARD OF TRADE", ("UST BOND", "TREASURY BONDS"), "ZB=F"),

    # Crypto CME
    MarketSpec("BTC — Bitcoin CME", "BTC", "Crypto CME", "financial", False, "BITCOIN - CHICAGO MERCANTILE EXCHANGE", ("BITCOIN",), "BTC=F"),
    MarketSpec("ETH — Ether CME", "ETH", "Crypto CME", "financial", False, "ETHER CASH SETTLED - CHICAGO MERCANTILE EXCHANGE", ("ETHER CASH", "ETHER"), "ETH=F"),

    # Energia
    MarketSpec("CL — WTI Crude Oil", "CL", "Energia", "commodity", False, "WTI-PHYSICAL - NEW YORK MERCANTILE EXCHANGE", ("WTI-PHYSICAL", "CRUDE OIL"), "CL=F"),
    MarketSpec("RB — Gasoline RBOB", "RB", "Energia", "commodity", False, "GASOLINE RBOB - NEW YORK MERCANTILE EXCHANGE", ("GASOLINE RBOB",), "RB=F"),
    MarketSpec("NG — Natural Gas", "NG", "Energia", "commodity", False, "NAT GAS NYME - NEW YORK MERCANTILE EXCHANGE", ("NAT GAS", "NATURAL GAS"), "NG=F"),
    MarketSpec("HO — Heating Oil", "HO", "Energia", "commodity", False, "NO. 2 HEATING OIL, N.Y. HARBOR - NEW YORK MERCANTILE EXCHANGE", ("HEATING OIL",), "HO=F"),
    MarketSpec("BZ — Brent", "BZ", "Energia", "commodity", False, "BRENT LAST DAY - NEW YORK MERCANTILE EXCHANGE", ("BRENT",), "BZ=F"),

    # Metalli
    MarketSpec("GC — Gold", "GC", "Metalli", "commodity", False, "GOLD - COMMODITY EXCHANGE INC.", ("GOLD", "COMMODITY EXCHANGE"), "GC=F"),
    MarketSpec("SI — Silver", "SI", "Metalli", "commodity", False, "SILVER - COMMODITY EXCHANGE INC.", ("SILVER",), "SI=F"),
    MarketSpec("HG — Copper", "HG", "Metalli", "commodity", False, "COPPER - COMMODITY EXCHANGE INC.", ("COPPER",), "HG=F"),
    MarketSpec("PL — Platinum", "PL", "Metalli", "commodity", False, "PLATINUM - NEW YORK MERCANTILE EXCHANGE", ("PLATINUM",), "PL=F"),
    MarketSpec("PA — Palladium", "PA", "Metalli", "commodity", False, "PALLADIUM - NEW YORK MERCANTILE EXCHANGE", ("PALLADIUM",), "PA=F"),

    # Cereali e semi oleosi
    MarketSpec("ZC — Corn", "ZC", "Agricoli", "commodity", False, "CORN - CHICAGO BOARD OF TRADE", ("CORN",), "ZC=F"),
    MarketSpec("ZS — Soybeans", "ZS", "Agricoli", "commodity", False, "SOYBEANS - CHICAGO BOARD OF TRADE", ("SOYBEANS",), "ZS=F"),
    MarketSpec("ZL — Soybean Oil", "ZL", "Agricoli", "commodity", False, "SOYBEAN OIL - CHICAGO BOARD OF TRADE", ("SOYBEAN OIL",), "ZL=F"),
    MarketSpec("ZM — Soybean Meal", "ZM", "Agricoli", "commodity", False, "SOYBEAN MEAL - CHICAGO BOARD OF TRADE", ("SOYBEAN MEAL",), "ZM=F"),
    MarketSpec("ZW — Wheat SRW", "ZW", "Agricoli", "commodity", False, "WHEAT-SRW - CHICAGO BOARD OF TRADE", ("WHEAT-SRW",), "ZW=F"),
    MarketSpec("KE — Wheat HRW", "KE", "Agricoli", "commodity", False, "WHEAT-HRW - CHICAGO BOARD OF TRADE", ("WHEAT-HRW",), "KE=F"),
    MarketSpec("ZO — Oats", "ZO", "Agricoli", "commodity", False, "OATS - CHICAGO BOARD OF TRADE", ("OATS",), "ZO=F"),
    MarketSpec("ZR — Rough Rice", "ZR", "Agricoli", "commodity", False, "ROUGH RICE - CHICAGO BOARD OF TRADE", ("ROUGH RICE",), "ZR=F"),

    # Soft commodity
    MarketSpec("CC — Cocoa", "CC", "Soft", "commodity", False, "COCOA - ICE FUTURES U.S.", ("COCOA",), "CC=F"),
    MarketSpec("KC — Coffee C", "KC", "Soft", "commodity", False, "COFFEE C - ICE FUTURES U.S.", ("COFFEE C",), "KC=F"),
    MarketSpec("CT — Cotton No. 2", "CT", "Soft", "commodity", False, "COTTON NO. 2 - ICE FUTURES U.S.", ("COTTON NO. 2",), "CT=F"),
    MarketSpec("SB — Sugar No. 11", "SB", "Soft", "commodity", False, "SUGAR NO. 11 - ICE FUTURES U.S.", ("SUGAR NO. 11",), "SB=F"),
    MarketSpec("OJ — Orange Juice", "OJ", "Soft", "commodity", False, "FRZN CONCENTRATED ORANGE JUICE - ICE FUTURES U.S.", ("ORANGE JUICE",), "OJ=F"),
    MarketSpec("LBR — Lumber", "LBR", "Soft", "commodity", False, "LUMBER - CHICAGO MERCANTILE EXCHANGE", ("LUMBER",), "LBR=F"),

    # Bestiame
    MarketSpec("LE — Live Cattle", "LE", "Bestiame", "commodity", False, "LIVE CATTLE - CHICAGO MERCANTILE EXCHANGE", ("LIVE CATTLE",), "LE=F"),
    MarketSpec("HE — Lean Hogs", "HE", "Bestiame", "commodity", False, "LEAN HOGS - CHICAGO MERCANTILE EXCHANGE", ("LEAN HOGS",), "HE=F"),
    MarketSpec("GF — Feeder Cattle", "GF", "Bestiame", "commodity", False, "FEEDER CATTLE - CHICAGO MERCANTILE EXCHANGE", ("FEEDER CATTLE",), "GF=F"),
)

MARKET_BY_LABEL = {m.label: m for m in MARKETS}


# =============================================================================
# FUNZIONI GENERALI
# =============================================================================
def normalize_text(value: str) -> str:
    value = value.upper().strip()
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def escape_soql(value: str) -> str:
    return value.replace("'", "''")


def to_float(value: Any) -> float:
    if value in (None, "", "."):
        return math.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def fmt_number(value: float, signed: bool = False) -> str:
    if pd.isna(value):
        return "N/A"
    template = f"{value:+,.0f}" if signed else f"{value:,.0f}"
    return template.replace(",", ".")


def fmt_pct(value: float, signed: bool = False, digits: int = 1) -> str:
    if pd.isna(value):
        return "N/A"
    sign = "+" if signed and value > 0 else ""
    return f"{sign}{value:.{digits}f}%"


def fmt_decimal(value: float, digits: int = 1) -> str:
    return "N/A" if pd.isna(value) else f"{value:.{digits}f}"


def card(kicker: str, title: str, detail: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="cot-card" style="--accent:{accent};">
            <div class="cot-kicker">{kicker}</div>
            <div class="cot-title">{title}</div>
            <div class="cot-small">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def accent_for_state(state: str) -> str:
    text = state.upper()
    if any(token in text for token in ("LONG CONFERMATO", "RIALZISTA", "POSSIBILE MINIMO", "MIGLIORAMENTO")):
        return "#15803D"
    if any(token in text for token in ("SHORT CONFERMATO", "RIBASSISTA", "POSSIBILE MASSIMO", "DETERIORAMENTO")):
        return "#B91C1C"
    if any(token in text for token in ("RITARDO", "AFFOLLATO", "DIVERGENZA", "PRESSIONE", "LIQUIDAZIONE")):
        return "#C2410C"
    return "#9A6700"


def safe_pct_change(current: float, previous: float) -> float:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return math.nan
    return (current - previous) / previous * 100.0


def historical_percentile(series: pd.Series, lookback: int) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna().tail(lookback)
    if len(values) < 2:
        return math.nan
    current = values.iloc[-1]
    history = values.iloc[:-1]
    return float((history <= current).mean() * 100.0)


def last_complete_friday(today: date | None = None) -> date:
    today = today or date.today()
    weekday = today.weekday()  # lun=0 ... dom=6
    if weekday == 4:  # venerdì: evitiamo sempre la settimana potenzialmente ancora aperta
        return today - timedelta(days=7)
    if weekday < 4:
        return today - timedelta(days=weekday + 3)
    return today - timedelta(days=weekday - 4)


# =============================================================================
# ACCESSO CFTC
# =============================================================================
class CFTCError(RuntimeError):
    pass


@st.cache_data(ttl=3600, show_spinner=False)
def cftc_request(dataset_id: str, params_items: tuple[tuple[str, str], ...]) -> list[dict[str, Any]]:
    params = dict(params_items)
    errors: list[str] = []
    for base in CFTC_API_BASES:
        url = f"{base}/{dataset_id}.json"
        try:
            response = requests.get(
                url,
                params=params,
                timeout=30,
                headers={"User-Agent": "Grespo-COT-Smart-Money/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                errors.append(f"{base}: risposta non tabellare")
                continue
            return payload
        except (requests.RequestException, ValueError) as exc:
            errors.append(f"{base}: {exc}")
    raise CFTCError(" | ".join(errors))


def run_cftc_query(dataset_id: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    normalized = tuple(sorted((str(k), str(v)) for k, v in params.items()))
    return cftc_request(dataset_id, normalized)


def candidate_score(candidate: str, spec: MarketSpec) -> float:
    cand = normalize_text(candidate)
    preferred = normalize_text(spec.preferred_name)
    ratio = SequenceMatcher(None, cand, preferred).ratio()
    keyword_bonus = sum(0.18 for term in spec.search_terms if normalize_text(term) in cand)
    return ratio + keyword_bonus


@st.cache_data(ttl=21600, show_spinner=False)
def resolve_market_name(dataset_id: str, spec: MarketSpec) -> tuple[str, str]:
    exact_params = {
        "$select": "market_and_exchange_names",
        "$where": f"market_and_exchange_names='{escape_soql(spec.preferred_name)}'",
        "$limit": 1,
    }
    exact = run_cftc_query(dataset_id, exact_params)
    if exact:
        return str(exact[0]["market_and_exchange_names"]), "corrispondenza esatta"

    candidates: dict[str, None] = {}
    for term in spec.search_terms:
        params = {
            "$select": "market_and_exchange_names",
            "$where": f"market_and_exchange_names like '%{escape_soql(term.upper())}%'",
            "$limit": 100,
        }
        try:
            for row in run_cftc_query(dataset_id, params):
                name = row.get("market_and_exchange_names")
                if name:
                    candidates[str(name)] = None
        except CFTCError:
            continue

    if not candidates:
        raise CFTCError(
            f"Mercato non trovato nel dataset {dataset_id}: {spec.preferred_name}"
        )

    best = max(candidates, key=lambda name: candidate_score(name, spec))
    return best, "corrispondenza automatica"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_market_history(
    report_type: str,
    spec: MarketSpec,
    limit: int,
) -> tuple[list[dict[str, Any]], str, str]:
    dataset_id = CFTC_DATASETS[report_type]
    market_name, resolution = resolve_market_name(dataset_id, spec)
    params = {
        "$where": f"market_and_exchange_names='{escape_soql(market_name)}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": limit,
    }
    rows = run_cftc_query(dataset_id, params)
    return rows, market_name, resolution


# =============================================================================
# NORMALIZZAZIONE CAMPI CFTC
# =============================================================================
def normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def resolve_field(records: Iterable[dict[str, Any]], candidates: Iterable[str]) -> str | None:
    keys: dict[str, str] = {}
    for row in list(records)[:10]:
        for key in row:
            keys.setdefault(normalized_key(key), key)

    for candidate in candidates:
        if candidate in keys.values():
            return candidate
        normalized = normalized_key(candidate)
        if normalized in keys:
            return keys[normalized]
    return None


COMMON_FIELDS = {
    "date": ("report_date_as_yyyy_mm_dd", "as_of_date_form_yyyy_mm_dd"),
    "oi": ("open_interest_all",),
    "code": ("cftc_contract_market_code",),
    "commodity": ("commodity_name", "contract_market_name"),
    "conc_long": (
        "conc_net_le_8_tdr_long",
        "conc_net_le_8_tdr_long_all",
        "conc_net_lt_8_tdr_long_all",
        "conc_net_long_all_8",
    ),
    "conc_short": (
        "conc_net_le_8_tdr_short",
        "conc_net_le_8_tdr_short_all",
        "conc_net_lt_8_tdr_short_all",
        "conc_net_short_all_8",
    ),
}

REPORT_FIELDS = {
    "Financial": {
        "trend_long": ("lev_money_positions_long", "lev_money_positions_long_all"),
        "trend_short": ("lev_money_positions_short", "lev_money_positions_short_all"),
        "asset_long": ("asset_mgr_positions_long", "asset_mgr_positions_long_all"),
        "asset_short": ("asset_mgr_positions_short", "asset_mgr_positions_short_all"),
        "dealer_long": ("dealer_positions_long", "dealer_positions_long_all"),
        "dealer_short": ("dealer_positions_short", "dealer_positions_short_all"),
    },
    "Disaggregated": {
        "trend_long": ("m_money_positions_long", "m_money_positions_long_all"),
        "trend_short": ("m_money_positions_short", "m_money_positions_short_all"),
        "producer_long": ("prod_merc_positions_long", "prod_merc_positions_long_all"),
        "producer_short": ("prod_merc_positions_short", "prod_merc_positions_short_all"),
    },
    "Legacy": {
        "trend_long": ("noncomm_positions_long_all", "noncomm_positions_long"),
        "trend_short": ("noncomm_positions_short_all", "noncomm_positions_short"),
        "commercial_long": ("comm_positions_long_all", "comm_positions_long"),
        "commercial_short": ("comm_positions_short_all", "comm_positions_short"),
    },
}


def build_history_df(
    records: list[dict[str, Any]],
    report_type: str,
    spec: MarketSpec,
    cot_lookback: int,
) -> tuple[pd.DataFrame, dict[str, str | None]]:
    if not records:
        return pd.DataFrame(), {}

    fields: dict[str, str | None] = {
        name: resolve_field(records, candidates) for name, candidates in COMMON_FIELDS.items()
    }
    fields.update(
        {
            name: resolve_field(records, candidates)
            for name, candidates in REPORT_FIELDS[report_type].items()
        }
    )

    if report_type == "Financial":
        if spec.is_fx:
            fields["counter_long"] = fields.get("dealer_long")
            fields["counter_short"] = fields.get("dealer_short")
        else:
            fields["counter_long"] = fields.get("asset_long")
            fields["counter_short"] = fields.get("asset_short")
    elif report_type == "Disaggregated":
        fields["counter_long"] = fields.get("producer_long")
        fields["counter_short"] = fields.get("producer_short")
    else:
        fields["counter_long"] = fields.get("commercial_long")
        fields["counter_short"] = fields.get("commercial_short")

    required = ("date", "oi", "trend_long", "trend_short", "counter_long", "counter_short")
    missing = [name for name in required if not fields.get(name)]
    if missing:
        available = sorted(records[0].keys())
        raise CFTCError(
            "Campi CFTC mancanti: " + ", ".join(missing) +
            ". Campi disponibili: " + ", ".join(available[:40])
        )

    rows: list[dict[str, Any]] = []
    for record in records:
        parsed_date = pd.to_datetime(record.get(fields["date"] or ""), errors="coerce")
        if pd.isna(parsed_date):
            continue
        rows.append(
            {
                "date": parsed_date.tz_localize(None) if getattr(parsed_date, "tzinfo", None) else parsed_date,
                "oi": to_float(record.get(fields["oi"] or "")),
                "trend_long": to_float(record.get(fields["trend_long"] or "")),
                "trend_short": to_float(record.get(fields["trend_short"] or "")),
                "counter_long": to_float(record.get(fields["counter_long"] or "")),
                "counter_short": to_float(record.get(fields["counter_short"] or "")),
                "conc_long": to_float(record.get(fields["conc_long"] or "")) if fields.get("conc_long") else math.nan,
                "conc_short": to_float(record.get(fields["conc_short"] or "")) if fields.get("conc_short") else math.nan,
                "cftc_code": str(record.get(fields["code"] or "", "N/A")),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df, fields

    df = (
        df.sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
        .reset_index(drop=True)
    )
    for column in ("oi", "trend_long", "trend_short", "counter_long", "counter_short", "conc_long", "conc_short"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["trend_net"] = df["trend_long"] - df["trend_short"]
    df["counter_net"] = df["counter_long"] - df["counter_short"]

    rolling_min = df["trend_net"].rolling(cot_lookback, min_periods=min(26, cot_lookback)).min()
    rolling_max = df["trend_net"].rolling(cot_lookback, min_periods=min(26, cot_lookback)).max()
    denominator = rolling_max - rolling_min
    df["cot_index"] = np.where(
        denominator.ne(0),
        100.0 * (df["trend_net"] - rolling_min) / denominator,
        50.0,
    )
    return df, fields


# =============================================================================
# PREZZO WEEKLY
# =============================================================================
@st.cache_data(ttl=21600, show_spinner=False)
def fetch_weekly_price(ticker: str) -> tuple[pd.DataFrame, str | None]:
    if not ticker.strip():
        return pd.DataFrame(), "Ticker Yahoo non impostato."
    try:
        daily = yf.download(
            ticker.strip(),
            period="5y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        return pd.DataFrame(), f"Errore Yahoo Finance: {exc}"

    if daily is None or daily.empty:
        return pd.DataFrame(), "Yahoo Finance non ha restituito dati."

    if isinstance(daily.columns, pd.MultiIndex):
        close_candidates = [col for col in daily.columns if col[0] == "Close"]
        if not close_candidates:
            return pd.DataFrame(), "Colonna Close non trovata nei dati Yahoo."
        close = daily[close_candidates[0]].copy()
    elif "Close" in daily.columns:
        close = daily["Close"].copy()
    else:
        return pd.DataFrame(), "Colonna Close non trovata nei dati Yahoo."

    close.index = pd.to_datetime(close.index).tz_localize(None)
    close = pd.to_numeric(close, errors="coerce").dropna()
    weekly = close.resample("W-FRI").last().to_frame("close")
    cutoff = pd.Timestamp(last_complete_friday())
    weekly = weekly.loc[weekly.index <= cutoff].copy()
    weekly["ema21"] = weekly["close"].ewm(span=21, adjust=False).mean()
    return weekly.tail(180), None


def analyze_price(weekly: pd.DataFrame) -> dict[str, Any]:
    unavailable = {
        "available": False,
        "text": "PREZZO WEEKLY NON DISPONIBILE",
        "detail": "Manca una serie Weekly valida per la conferma del prezzo.",
        "long_confirmed": False,
        "short_confirmed": False,
        "above_ema": False,
        "below_ema": False,
        "rising": False,
        "falling": False,
        "close": math.nan,
        "previous": math.nan,
        "ema21": math.nan,
    }
    if weekly.empty or len(weekly) < 22:
        return unavailable

    current = weekly.iloc[-1]
    previous = weekly.iloc[-2]
    close = float(current["close"])
    prev_close = float(previous["close"])
    ema21 = float(current["ema21"])
    above = close > ema21
    below = close < ema21
    rising = close > prev_close
    falling = close < prev_close
    long_confirmed = above and rising
    short_confirmed = below and falling

    if long_confirmed:
        text = "CONFERMA RIALZISTA"
    elif short_confirmed:
        text = "CONFERMA RIBASSISTA"
    elif above and falling:
        text = "SOPRA EMA21, MOMENTUM IN CALO"
    elif below and rising:
        text = "SOTTO EMA21, RIMBALZO IN CORSO"
    elif above:
        text = "PREZZO SOPRA EMA21"
    elif below:
        text = "PREZZO SOTTO EMA21"
    else:
        text = "PREZZO NEUTRALE SULLA EMA21"

    return {
        "available": True,
        "text": text,
        "detail": f"Close W: {close:.4f} | EMA21 W: {ema21:.4f} | Close precedente: {prev_close:.4f}",
        "long_confirmed": long_confirmed,
        "short_confirmed": short_confirmed,
        "above_ema": above,
        "below_ema": below,
        "rising": rising,
        "falling": falling,
        "close": close,
        "previous": prev_close,
        "ema21": ema21,
    }


# =============================================================================
# MOTORE SMART MONEY
# =============================================================================
def cot_zone(index_value: float) -> str:
    if pd.isna(index_value):
        return "NON DISPONIBILE"
    if index_value >= 80:
        return "ESTREMO LONG — MOLTI FONDI GIÀ LONG"
    if index_value >= 60:
        return "POSIZIONAMENTO LONG ELEVATO"
    if index_value > 40:
        return "ZONA INTERMEDIA"
    if index_value > 20:
        return "POSIZIONAMENTO SHORT ELEVATO"
    return "ESTREMO SHORT — MOLTI FONDI GIÀ SHORT"


def analyze_smart_money(
    df: pd.DataFrame,
    spec: MarketSpec,
    price: dict[str, Any],
    oi_threshold: float,
) -> dict[str, Any]:
    if df.empty or len(df) < 7:
        return {
            "available": False,
            "final_bias": "BIAS NON DISPONIBILE",
            "final_detail": "Servono almeno sette report consecutivi per l'analisi 1W, 3W e 6W.",
            "action": "NESSUNA INDICAZIONE OPERATIVA",
            "reason": "I dati COT non sono sufficienti.",
        }

    cur = df.iloc[-1]
    prev = df.iloc[-2]
    w3 = df.iloc[-4]
    w6 = df.iloc[-7]

    trend_flow_1w = float(cur["trend_net"] - prev["trend_net"])
    counter_flow_1w = float(cur["counter_net"] - prev["counter_net"])
    trend_flow_3w = float(cur["trend_net"] - w3["trend_net"])
    counter_flow_3w = float(cur["counter_net"] - w3["counter_net"])
    trend_flow_6w = float(cur["trend_net"] - w6["trend_net"])
    counter_flow_6w = float(cur["counter_net"] - w6["counter_net"])

    trend_chg_l = float(cur["trend_long"] - prev["trend_long"])
    trend_chg_s = float(cur["trend_short"] - prev["trend_short"])
    counter_chg_l = float(cur["counter_long"] - prev["counter_long"])
    counter_chg_s = float(cur["counter_short"] - prev["counter_short"])
    pct_delta_oi = safe_pct_change(float(cur["oi"]), float(prev["oi"]))
    cot_index = float(cur["cot_index"]) if not pd.isna(cur["cot_index"]) else math.nan

    oi_up = not pd.isna(pct_delta_oi) and pct_delta_oi > oi_threshold
    oi_down = not pd.isna(pct_delta_oi) and pct_delta_oi < -oi_threshold

    new_long = trend_flow_1w > 0 and trend_chg_l > 0 and oi_up
    new_short = trend_flow_1w < 0 and trend_chg_s > 0 and oi_up
    short_covering = trend_flow_1w > 0 and trend_chg_s < 0 and oi_down
    long_liquidation = trend_flow_1w < 0 and trend_chg_l < 0 and oi_down

    if new_long:
        last_report = "NUOVI LONG PROBABILI"
    elif new_short:
        last_report = "NUOVI SHORT PROBABILI"
    elif short_covering:
        last_report = "SHORT COVERING PROBABILE"
    elif long_liquidation:
        last_report = "LIQUIDAZIONE LONG PROBABILE"
    elif trend_flow_1w > 0:
        last_report = "POSIZIONAMENTO IN MIGLIORAMENTO"
    elif trend_flow_1w < 0:
        last_report = "POSIZIONAMENTO IN PEGGIORAMENTO"
    else:
        last_report = "FLUSSO STABILE / MISTO"

    macro_long = trend_flow_3w > 0 and trend_flow_6w > 0
    macro_short = trend_flow_3w < 0 and trend_flow_6w < 0
    macro_recovery = trend_flow_3w > 0 and trend_flow_6w < 0
    macro_deterioration = trend_flow_3w < 0 and trend_flow_6w > 0

    if macro_long and trend_flow_1w > 0:
        structure = "LONG IN RAFFORZAMENTO"
    elif macro_long and trend_flow_1w < 0:
        structure = "LONG IN DETERIORAMENTO"
    elif macro_short and trend_flow_1w < 0:
        structure = "SHORT IN RAFFORZAMENTO"
    elif macro_short and trend_flow_1w > 0:
        structure = "RECUPERO DA STRUTTURA SHORT"
    elif macro_recovery:
        structure = "RECUPERO LONG IN CORSO"
    elif macro_deterioration:
        structure = "DETERIORAMENTO DEL LONG"
    else:
        structure = "STRUTTURA MISTA / TRANSIZIONE"

    counter_macro_long = counter_flow_3w > 0 and counter_flow_6w > 0
    counter_macro_short = counter_flow_3w < 0 and counter_flow_6w < 0

    if spec.family == "commodity":
        if counter_flow_1w > 0:
            counter_reading = "PRODUCER MIGLIORANO LA NET POSITION"
        elif counter_flow_1w < 0:
            counter_reading = "PRODUCER AUMENTANO L'HEDGING SHORT"
        else:
            counter_reading = "PRODUCER SOSTANZIALMENTE STABILI"
    elif spec.is_fx:
        if trend_flow_1w > 0 and counter_flow_1w < 0:
            counter_reading = "DEALER CONTROPARTE DEI LONG"
        elif trend_flow_1w < 0 and counter_flow_1w > 0:
            counter_reading = "DEALER CONTROPARTE DEGLI SHORT"
        else:
            counter_reading = "DINAMICA DEALER NON CONCORDE"
    else:
        if counter_flow_1w > 0:
            counter_reading = "ASSET MANAGER AUMENTANO L'ESPOSIZIONE"
        elif counter_flow_1w < 0:
            counter_reading = "ASSET MANAGER RIDUCONO L'ESPOSIZIONE"
        else:
            counter_reading = "ASSET MANAGER STABILI"

    financial_long_alignment = spec.family == "financial" and not spec.is_fx and trend_flow_1w > 0 and counter_flow_1w > 0
    financial_short_alignment = spec.family == "financial" and not spec.is_fx and trend_flow_1w < 0 and counter_flow_1w < 0
    fx_long_alignment = spec.is_fx and trend_flow_1w > 0 and counter_flow_1w < 0
    fx_short_alignment = spec.is_fx and trend_flow_1w < 0 and counter_flow_1w > 0
    commodity_joint_long = spec.family == "commodity" and trend_flow_1w > 0 and counter_flow_1w > 0
    commodity_joint_short = spec.family == "commodity" and trend_flow_1w < 0 and counter_flow_1w < 0
    commodity_trend_long = spec.family == "commodity" and trend_flow_1w > 0 and counter_flow_1w < 0
    commodity_trend_short = spec.family == "commodity" and trend_flow_1w < 0 and counter_flow_1w > 0

    financial_long_confirmed = financial_long_alignment and macro_long and counter_macro_long
    financial_short_confirmed = financial_short_alignment and macro_short and counter_macro_short
    fx_long_confirmed = fx_long_alignment and macro_long and counter_macro_short
    fx_short_confirmed = fx_short_alignment and macro_short and counter_macro_long

    possible_bottom = spec.family == "commodity" and cot_index <= 20 and commodity_joint_long
    possible_top = spec.family == "commodity" and cot_index >= 80 and commodity_joint_short

    if possible_bottom:
        engine_bias = "POSSIBILE MINIMO ISTITUZIONALE"
        engine_detail = "Managed Money molto scarico e in miglioramento insieme ai Producer."
    elif possible_top:
        engine_bias = "POSSIBILE MASSIMO ISTITUZIONALE"
        engine_detail = "Managed Money molto carico e flussi in peggioramento insieme ai Producer."
    elif spec.family == "commodity" and commodity_trend_long and macro_long:
        engine_bias = "TREND LONG SPECULATIVO"
        engine_detail = "Managed Money accumula mentre i Producer aumentano le coperture."
    elif spec.family == "commodity" and commodity_trend_short and macro_short:
        engine_bias = "TREND SHORT SPECULATIVO"
        engine_detail = "Managed Money aumenta la pressione ribassista mentre i Producer migliorano la posizione."
    elif spec.family == "commodity" and commodity_joint_long:
        engine_bias = "RECUPERO LONG DA CONFERMARE"
        engine_detail = "Managed Money e Producer migliorano, ma la struttura 3-6W non è ancora pienamente rialzista."
    elif spec.family == "commodity" and commodity_joint_short:
        engine_bias = "PRESSIONE SHORT IN AUMENTO"
        engine_detail = "Managed Money e Producer peggiorano insieme."
    elif fx_long_confirmed:
        engine_bias = "LONG VALUTA CONFERMATO"
        engine_detail = "Leveraged Funds rialzisti e Dealer nel normale ruolo di controparte."
    elif fx_short_confirmed:
        engine_bias = "SHORT VALUTA CONFERMATO"
        engine_detail = "Leveraged Funds ribassisti e Dealer nel normale ruolo di controparte."
    elif spec.is_fx and fx_long_alignment and macro_long:
        engine_bias = "LONG FX CON CONFERMA PARZIALE"
        engine_detail = "Struttura Leveraged rialzista, ma Dealer non ancora concordi sulle 3-6W."
    elif spec.is_fx and fx_short_alignment and macro_short:
        engine_bias = "SHORT FX CON CONFERMA PARZIALE"
        engine_detail = "Struttura Leveraged ribassista, ma Dealer non ancora concordi sulle 3-6W."
    elif spec.is_fx and fx_long_alignment:
        engine_bias = "RECUPERO LONG VALUTA"
        engine_detail = "Flusso settimanale rialzista ancora da confermare sulle 3-6W."
    elif spec.is_fx and fx_short_alignment:
        engine_bias = "PRESSIONE SHORT VALUTA"
        engine_detail = "Flusso settimanale ribassista ancora da confermare sulle 3-6W."
    elif financial_long_confirmed:
        engine_bias = "LONG ISTITUZIONALE CONFERMATO"
        engine_detail = "Leveraged Funds e Asset Manager migliorano insieme anche nella struttura 3-6W."
    elif financial_short_confirmed:
        engine_bias = "SHORT ISTITUZIONALE CONFERMATO"
        engine_detail = "Leveraged Funds e Asset Manager peggiorano insieme anche nella struttura 3-6W."
    elif financial_long_alignment and macro_long:
        engine_bias = "LONG LEVERAGED CON CONFERMA PARZIALE"
        engine_detail = "Leveraged rialzisti; Asset Manager non ancora concordi sulle 3-6W."
    elif financial_short_alignment and macro_short:
        engine_bias = "SHORT LEVERAGED CON CONFERMA PARZIALE"
        engine_detail = "Leveraged ribassisti; Asset Manager non ancora concordi sulle 3-6W."
    elif financial_long_alignment:
        engine_bias = "RECUPERO LONG ISTITUZIONALE"
        engine_detail = "Leveraged Funds e Asset Manager migliorano, ma manca conferma 3-6W."
    elif financial_short_alignment:
        engine_bias = "PRESSIONE SHORT ISTITUZIONALE"
        engine_detail = "Leveraged Funds e Asset Manager peggiorano, ma manca conferma 3-6W."
    elif trend_flow_1w > 0:
        engine_bias = "MIGLIORAMENTO SPECULATIVO"
        engine_detail = f"La Net Position dei {spec.trend_label} migliora, ma il quadro non è completo."
    elif trend_flow_1w < 0:
        engine_bias = "DETERIORAMENTO SPECULATIVO"
        engine_detail = f"La Net Position dei {spec.trend_label} peggiora, ma il quadro non è completo."
    else:
        engine_bias = "BIAS MISTO / TRANSIZIONE"
        engine_detail = "I flussi non mostrano ancora una direzione abbastanza chiara."

    confirmed_long = (spec.family == "commodity" and commodity_trend_long and macro_long) or fx_long_confirmed or financial_long_confirmed
    confirmed_short = (spec.family == "commodity" and commodity_trend_short and macro_short) or fx_short_confirmed or financial_short_confirmed
    extreme_long = not pd.isna(cot_index) and cot_index >= 80
    extreme_short = not pd.isna(cot_index) and cot_index <= 20
    crowded_long = confirmed_long and extreme_long
    crowded_short = confirmed_short and extreme_short

    full_long = confirmed_long and price["long_confirmed"]
    full_short = confirmed_short and price["short_confirmed"]
    long_price_divergence = confirmed_long and price["short_confirmed"]
    short_price_divergence = confirmed_short and price["long_confirmed"]

    partial_long = (not confirmed_long and trend_flow_1w > 0 and (commodity_joint_long or fx_long_alignment or financial_long_alignment or macro_recovery))
    partial_short = (not confirmed_short and trend_flow_1w < 0 and (commodity_joint_short or fx_short_alignment or financial_short_alignment or macro_deterioration))
    partial_long_with_price = partial_long and price["long_confirmed"]
    partial_short_with_price = partial_short and price["short_confirmed"]

    # Bias COT + prezzo
    combined_bias = engine_bias
    combined_detail = engine_detail
    if possible_bottom and price["long_confirmed"]:
        combined_bias = "POSSIBILE MINIMO + PREZZO RIALZISTA"
    elif possible_top and price["short_confirmed"]:
        combined_bias = "POSSIBILE MASSIMO + PREZZO RIBASSISTA"
    elif crowded_long and price["short_confirmed"]:
        combined_bias = "TROPPI FONDI GIÀ LONG / PREZZO IN CALO"
    elif crowded_short and price["long_confirmed"]:
        combined_bias = "TROPPI FONDI GIÀ SHORT / PREZZO IN RIALZO"
    elif crowded_long:
        combined_bias = "LONG CONFERMATO — MOLTI FONDI GIÀ LONG"
    elif crowded_short:
        combined_bias = "SHORT CONFERMATO — MOLTI FONDI GIÀ SHORT"
    elif full_long:
        combined_bias = "LONG CONFERMATO: COT + PREZZO"
    elif full_short:
        combined_bias = "SHORT CONFERMATO: COT + PREZZO"
    elif long_price_divergence:
        combined_bias = "DIVERGENZA: COT LONG / PREZZO SHORT"
    elif short_price_divergence:
        combined_bias = "DIVERGENZA: COT SHORT / PREZZO LONG"
    elif confirmed_long:
        combined_bias = "LONG ISTITUZIONALE ANTICIPATO"
    elif confirmed_short:
        combined_bias = "SHORT ISTITUZIONALE ANTICIPATO"
    elif partial_long_with_price:
        combined_bias = "RECUPERO LONG + PREZZO RIALZISTA"
    elif partial_short_with_price:
        combined_bias = "PRESSIONE SHORT + PREZZO RIBASSISTA"

    # Indicazione operativa, con priorità coerente con il Pine
    action = "ATTENDI: IL QUADRO NON È ANCORA CHIARO"
    reason = "I Fondi e gli altri operatori non mostrano ancora una direzione abbastanza chiara."
    if short_covering:
        action = "NON INSEGUIRE IL RIALZO: ATTENDI NUOVI ACQUISTI REALI"
        reason = "Il miglioramento può dipendere soprattutto dalla chiusura di vecchi Short, non da nuovi acquisti."
    elif long_liquidation:
        action = "EVITA DI COMPRARE SUBITO: ATTENDI UNA STABILIZZAZIONE"
        reason = "Il ribasso può dipendere soprattutto dalla chiusura di vecchi Long, non da nuova pressione Short."
    elif possible_bottom:
        action = "CERCA CONFERME LONG SUI SUPPORTI: EVITA SHORT TARDIVI"
        reason = "Managed Money e Producer migliorano da un estremo Short; un minimo è possibile ma va confermato."
    elif possible_top:
        action = "PROTEGGI GLI EVENTUALI LONG: CERCA CONFERME RIBASSISTE"
        reason = "Managed Money è molto carico e i flussi iniziano a peggiorare."
    elif crowded_long:
        action = "LONG CONFERMATO MA AFFOLLATO: NON INSEGUIRE I MASSIMI"
        reason = "Molti Fondi sono già Long; una presa di profitto può rendere la discesa rapida."
    elif crowded_short:
        action = "SHORT CONFERMATO MA AFFOLLATO: NON INSEGUIRE I MINIMI"
        reason = "Molti Fondi sono già Short; uno short covering può rendere il rimbalzo rapido."
    elif full_long:
        action = "PRIVILEGIA I PULLBACK LONG: EVITA SHORT CONTROTENDENZA"
        reason = "COT e prezzo Weekly confermano insieme il quadro rialzista."
    elif full_short:
        action = "PRIVILEGIA I RIMBALZI SHORT: EVITA LONG CONTROTENDENZA"
        reason = "COT e prezzo Weekly confermano insieme il quadro ribassista."
    elif long_price_divergence:
        action = "RIDUCI L'AGGRESSIVITÀ LONG: IL PREZZO NON CONFERMA"
        reason = "Il COT è rialzista, ma il prezzo Weekly è ribassista."
    elif short_price_divergence:
        action = "NON INSEGUIRE GLI SHORT: IL PREZZO NON CONFERMA"
        reason = "Il COT è ribassista, ma il prezzo Weekly è rialzista."
    elif confirmed_long:
        action = "ATTENDI CONFERMA DEL PREZZO: NON ANTICIPARE IL LONG"
        reason = "Il quadro istituzionale è rialzista, ma il prezzo Weekly non è ancora completamente concorde."
    elif confirmed_short:
        action = "ATTENDI CONFERMA DEL PREZZO: NON ANTICIPARE LO SHORT"
        reason = "Il quadro istituzionale è ribassista, ma il prezzo Weekly non è ancora completamente concorde."
    elif partial_long_with_price:
        action = "QUADRO IN RECUPERO: CERCA SOLO PULLBACK LONG CONFERMATI"
        reason = "Prezzo e flussi settimanali migliorano, ma la struttura istituzionale non è ancora completa."
    elif partial_short_with_price:
        action = "PRESSIONE IN AUMENTO: CERCA SOLO RIMBALZI SHORT CONFERMATI"
        reason = "Prezzo e flussi settimanali peggiorano, ma la struttura istituzionale non è ancora completa."
    elif macro_recovery or fx_long_alignment or financial_long_alignment or commodity_joint_long:
        action = "ATTENDI CONFERMA DEL PREZZO: NON ANTICIPARE IL LONG"
        reason = "I Fondi migliorano, ma le ultime settimane non confermano ancora un quadro rialzista completo."
    elif macro_deterioration or fx_short_alignment or financial_short_alignment or commodity_joint_short:
        action = "RIDUCI L'AGGRESSIVITÀ LONG: ATTENDI CONFERMA RIBASSISTA"
        reason = "I Fondi peggiorano, ma manca ancora una conferma Short completa."
    elif trend_flow_1w > 0:
        action = "QUADRO IN MIGLIORAMENTO: ATTENDI UN PULLBACK CONFERMATO"
        reason = "Il flusso principale migliora, ma gli altri dati non sono ancora tutti allineati."
    elif trend_flow_1w < 0:
        action = "QUADRO IN PEGGIORAMENTO: MANTIENI PRUDENZA SUI LONG"
        reason = "Il flusso principale peggiora, ma manca ancora una conferma Short completa."

    report_date = pd.Timestamp(cur["date"]).date()
    age_days = max((date.today() - report_date).days, 0)
    freshness = "FRESCO" if age_days <= 10 else "POSSIBILE RITARDO" if age_days <= 17 else "DATI DATATI"
    final_bias = combined_bias
    final_detail = combined_detail
    if age_days > 17:
        final_bias = f"{combined_bias} — DATI COT DATATI"
        action = "NESSUNA INDICAZIONE ATTUALE: ATTENDI UN NUOVO REPORT"
        reason = f"Le posizioni disponibili risalgono a {age_days} giorni fa."
    elif age_days > 10:
        final_bias = f"{combined_bias} — POSSIBILE RITARDO"
        action = f"{action} — VERIFICA L'ARRIVO DEL NUOVO REPORT"
        reason += f" Le posizioni disponibili risalgono a {age_days} giorni fa."

    conc_long_rank = historical_percentile(df["conc_long"], 156)
    conc_short_rank = historical_percentile(df["conc_short"], 156)
    conc_long_high = not pd.isna(conc_long_rank) and conc_long_rank >= 80
    conc_short_high = not pd.isna(conc_short_rank) and conc_short_rank >= 80
    if conc_long_high and conc_short_high:
        concentration_state = "MOLTI GRANDI TRADER GIÀ LONG E SHORT"
    elif conc_long_high:
        concentration_state = "MOLTI GRANDI TRADER GIÀ LONG"
    elif conc_short_high:
        concentration_state = "MOLTI GRANDI TRADER GIÀ SHORT"
    elif max(conc_long_rank if not pd.isna(conc_long_rank) else 0, conc_short_rank if not pd.isna(conc_short_rank) else 0) >= 60:
        concentration_state = "CONCENTRAZIONE SOPRA LA NORMA"
    elif pd.isna(conc_long_rank) or pd.isna(conc_short_rank):
        concentration_state = "DATI NON DISPONIBILI"
    else:
        concentration_state = "CONCENTRAZIONE NORMALE"

    return {
        "available": True,
        "report_date": report_date,
        "previous_date": pd.Timestamp(prev["date"]).date(),
        "age_days": age_days,
        "freshness": freshness,
        "cftc_code": str(cur.get("cftc_code", "N/A")),
        "oi": float(cur["oi"]),
        "pct_delta_oi": pct_delta_oi,
        "trend_long": float(cur["trend_long"]),
        "trend_short": float(cur["trend_short"]),
        "counter_long": float(cur["counter_long"]),
        "counter_short": float(cur["counter_short"]),
        "trend_chg_l": trend_chg_l,
        "trend_chg_s": trend_chg_s,
        "counter_chg_l": counter_chg_l,
        "counter_chg_s": counter_chg_s,
        "trend_flow_1w": trend_flow_1w,
        "trend_flow_3w": trend_flow_3w,
        "trend_flow_6w": trend_flow_6w,
        "counter_flow_1w": counter_flow_1w,
        "counter_flow_3w": counter_flow_3w,
        "counter_flow_6w": counter_flow_6w,
        "cot_index": cot_index,
        "positioning": cot_zone(cot_index),
        "last_report": last_report,
        "structure": structure,
        "counter_reading": counter_reading,
        "engine_bias": engine_bias,
        "engine_detail": engine_detail,
        "combined_bias": combined_bias,
        "final_bias": final_bias,
        "final_detail": final_detail,
        "action": action,
        "reason": reason,
        "new_long": new_long,
        "new_short": new_short,
        "short_covering": short_covering,
        "long_liquidation": long_liquidation,
        "confirmed_long": confirmed_long,
        "confirmed_short": confirmed_short,
        "crowded_long": crowded_long,
        "crowded_short": crowded_short,
        "conc_long": float(cur["conc_long"]) if not pd.isna(cur["conc_long"]) else math.nan,
        "conc_short": float(cur["conc_short"]) if not pd.isna(cur["conc_short"]) else math.nan,
        "conc_long_rank": conc_long_rank,
        "conc_short_rank": conc_short_rank,
        "concentration_state": concentration_state,
    }


# =============================================================================
# MODULO LEGACY DI VALIDAZIONE
# =============================================================================
def analyze_legacy(df: pd.DataFrame, term_structure: str) -> dict[str, Any]:
    if df.empty or len(df) < 2:
        return {"available": False, "bias": "NON DISPONIBILE", "detail": "Dati Legacy insufficienti."}

    cur = df.iloc[-1]
    prev = df.iloc[-2]
    oi_delta = float(cur["oi"] - prev["oi"])
    pct_delta_oi = safe_pct_change(float(cur["oi"]), float(prev["oi"]))
    trend_flow = float(cur["trend_net"] - prev["trend_net"])
    counter_flow = float(cur["counter_net"] - prev["counter_net"])
    backwardation = term_structure == "Backwardation"

    stage_1a = trend_flow > 0 and counter_flow < 0 and pct_delta_oi > 0.5
    stage_1b = trend_flow < 0 and counter_flow > 0 and pct_delta_oi > 0.5
    squeeze = pct_delta_oi <= -0.5 and trend_flow > 0 and backwardation
    div_short = trend_flow > 0 and counter_flow > 0
    conv_short = trend_flow < 0 and counter_flow < 0

    bias = "NEUTRAL / MISTO"
    verdict = "Flussi misti in assestamento."
    action = "Attendi una configurazione più chiara prima di aumentare l'esposizione."
    if stage_1a:
        bias = "CONVERGENZA LONG"
        verdict = "Convergenza rialzista tra Noncommercial e Commercial con OI in espansione."
        action = "Cerca conferme del prezzo sui supporti prima di aumentare l'esposizione long."
    elif stage_1b:
        bias = "DISTRIBUZIONE / SHORT"
        verdict = "Pressione ribassista con Open Interest in espansione."
        action = "Evita nuovi long e attendi un miglioramento dei flussi."
    elif squeeze:
        bias = "SHORT COVERING SQUEEZE"
        verdict = "Miglioramento speculativo con OI in contrazione e Backwardation."
        action = "Non inseguire il movimento e proteggi le posizioni già aperte."
    elif div_short:
        bias = "DIVERG. LONG ➔ SHORT"
        verdict = "Divergenza tra Noncommercial e Commercial."
        action = "Proteggi gli eventuali long e attendi una nuova convergenza."
    elif conv_short:
        bias = "CONVERGENZA SHORT"
        verdict = "Convergenza ribassista dei flussi netti."
        action = "Evita acquisti in controtendenza e attendi un miglioramento dei flussi."

    return {
        "available": True,
        "bias": bias,
        "verdict": verdict,
        "action": action,
        "report_date": pd.Timestamp(cur["date"]).date(),
        "previous_date": pd.Timestamp(prev["date"]).date(),
        "oi": float(cur["oi"]),
        "oi_delta": oi_delta,
        "pct_delta_oi": pct_delta_oi,
        "trend_flow": trend_flow,
        "counter_flow": counter_flow,
    }


# =============================================================================
# TERM STRUCTURE MANUALE
# =============================================================================
def read_term_csv(source: Any) -> dict[str, str]:
    try:
        frame = pd.read_csv(source)
    except Exception:
        return {}
    required = {"root", "term_structure"}
    if not required.issubset(frame.columns):
        return {}
    result: dict[str, str] = {}
    for _, row in frame.iterrows():
        root = str(row["root"]).strip().upper()
        value = str(row["term_structure"]).strip()
        if root and value in TERM_OPTIONS:
            result[root] = value
    return result


def bundled_term_defaults() -> dict[str, str]:
    path = Path(__file__).with_name("term_structure.csv")
    return read_term_csv(path) if path.exists() else {}


# =============================================================================
# GRAFICI
# =============================================================================
def plot_cot_index(df: pd.DataFrame, label: str) -> go.Figure:
    chart_df = df.dropna(subset=["cot_index"]).tail(180)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_df["date"], y=chart_df["cot_index"], mode="lines", name=label))
    fig.add_hrect(y0=80, y1=100, opacity=0.10, line_width=0)
    fig.add_hrect(y0=0, y1=20, opacity=0.10, line_width=0)
    fig.add_hline(y=80, line_dash="dash")
    fig.add_hline(y=50, line_dash="dot")
    fig.add_hline(y=20, line_dash="dash")
    fig.update_layout(title=f"COT Index — {label}", height=390, margin=dict(l=20, r=20, t=55, b=20), yaxis_range=[0, 100])
    return fig


def plot_net_positions(df: pd.DataFrame, trend_label: str, counter_label: str) -> go.Figure:
    chart_df = df.tail(180)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_df["date"], y=chart_df["trend_net"], mode="lines", name=trend_label))
    fig.add_trace(go.Scatter(x=chart_df["date"], y=chart_df["counter_net"], mode="lines", name=counter_label))
    fig.add_hline(y=0, line_dash="dot")
    fig.update_layout(title="Net Position", height=390, margin=dict(l=20, r=20, t=55, b=20), legend=dict(orientation="h"))
    return fig


def plot_weekly_price(weekly: pd.DataFrame, ticker: str) -> go.Figure:
    chart_df = weekly.tail(104)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["close"], mode="lines", name="Close Weekly"))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["ema21"], mode="lines", name="EMA21 Weekly"))
    fig.update_layout(title=f"Prezzo Weekly — {ticker}", height=390, margin=dict(l=20, r=20, t=55, b=20), legend=dict(orientation="h"))
    return fig


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.header("Impostazioni")
    group = st.selectbox("Famiglia", ["Tutti"] + sorted({m.group for m in MARKETS}))
    filtered = [m for m in MARKETS if group == "Tutti" or m.group == group]
    selected_label = st.selectbox("Mercato", [m.label for m in filtered])
    spec = MARKET_BY_LABEL[selected_label]

    cot_lookback = st.selectbox("COT Index lookback", [26, 52, 156, 260], index=2, format_func=lambda x: f"{x} settimane")
    oi_threshold = st.number_input("Soglia Open Interest (%)", min_value=0.0, max_value=10.0, value=0.5, step=0.1)
    yahoo_ticker = st.text_input("Ticker prezzo Yahoo", value=spec.yahoo_ticker)

    st.divider()
    st.subheader("Term Structure")
    term_defaults = bundled_term_defaults()
    uploaded_term_file = st.file_uploader("Carica CSV opzionale", type=["csv"])
    if uploaded_term_file is not None:
        term_defaults.update(read_term_csv(uploaded_term_file))

    if spec.family == "commodity":
        default_term = term_defaults.get(spec.root, "Non disponibile")
        default_index = TERM_OPTIONS.index(default_term) if default_term in TERM_OPTIONS else 0
        term_structure = st.selectbox("Curva M1–M2", TERM_OPTIONS, index=default_index)
        st.caption("La selezione resta manuale. Per un valore permanente modifica term_structure.csv nel repository.")
    else:
        term_structure = "Non applicabile"
        st.caption("Non utilizzata per finanziari, valute, tassi e crypto CME.")

    st.divider()
    show_legacy = st.toggle("Mostra modulo Legacy", value=True)
    show_debug = st.toggle("Mostra diagnostica campi", value=False)


# =============================================================================
# RECUPERO DATI
# =============================================================================
history_limit = max(cot_lookback + 12, 180)

try:
    with st.spinner("Recupero report CFTC e prezzo Weekly..."):
        specific_rows, specific_market_name, specific_resolution = fetch_market_history(
            spec.specific_report, spec, history_limit
        )
        specific_df, specific_fields = build_history_df(
            specific_rows, spec.specific_report, spec, cot_lookback
        )

        legacy_df = pd.DataFrame()
        legacy_market_name = ""
        legacy_resolution = ""
        legacy_fields: dict[str, str | None] = {}
        if show_legacy:
            legacy_rows, legacy_market_name, legacy_resolution = fetch_market_history(
                "Legacy", spec, history_limit
            )
            legacy_df, legacy_fields = build_history_df(
                legacy_rows, "Legacy", spec, cot_lookback
            )

        weekly_price, price_error = fetch_weekly_price(yahoo_ticker)
except CFTCError as exc:
    st.error(f"Errore CFTC: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Errore inatteso durante il recupero dei dati: {exc}")
    st.stop()

price_analysis = analyze_price(weekly_price)
smart = analyze_smart_money(specific_df, spec, price_analysis, float(oi_threshold))
legacy = analyze_legacy(legacy_df, term_structure) if show_legacy else {"available": False}

if not smart.get("available"):
    st.error(smart.get("final_detail", "Analisi non disponibile."))
    st.stop()


# =============================================================================
# INTESTAZIONE DATI
# =============================================================================
st.success(
    f"{spec.label} | Report {spec.specific_report} | posizioni al {smart['report_date'].strftime('%d/%m/%Y')} "
    f"| mercato CFTC: {specific_market_name} ({specific_resolution})."
)
if price_error:
    st.warning(price_error)

col1, col2, col3, col4 = st.columns(4)
col1.metric("COT Index", fmt_decimal(smart["cot_index"], 1), smart["positioning"])
col2.metric("Open Interest", fmt_number(smart["oi"]), fmt_pct(smart["pct_delta_oi"], signed=True, digits=2))
col3.metric(f"Flow {spec.trend_label} 1W", fmt_number(smart["trend_flow_1w"], signed=True), f"3W {fmt_number(smart['trend_flow_3w'], signed=True)}")
col4.metric(f"Flow {spec.counter_label} 1W", fmt_number(smart["counter_flow_1w"], signed=True), f"3W {fmt_number(smart['counter_flow_3w'], signed=True)}")


# =============================================================================
# RESPONSO PRINCIPALE
# =============================================================================
st.header("1. Responso Smart Money")
main_accent = accent_for_state(smart["final_bias"])
card(
    "BIAS FINALE — COT + PREZZO WEEKLY",
    smart["final_bias"],
    f"{smart['final_detail']}<br><b>Prezzo:</b> {price_analysis['text']}<br>"
    f"<b>Freschezza:</b> {smart['freshness']} ({smart['age_days']} giorni)",
    main_accent,
)

left, right = st.columns([1.15, 1])
with left:
    card("COSA FARE", smart["action"], smart["reason"], main_accent)
with right:
    card("LETTURA SEMPLICE", smart["last_report"], f"{smart['structure']}<br>{smart['counter_reading']}", accent_for_state(smart["last_report"]))


# =============================================================================
# QUADRO TECNICO
# =============================================================================
st.header("2. Quadro tecnico")
tech_rows = [
    {"Voce": "Famiglia mercato", "Valore": spec.market_family_label},
    {"Voce": "Report utilizzato", "Valore": spec.specific_report},
    {"Voce": "Categoria trend", "Valore": spec.trend_label},
    {"Voce": "Controparte", "Valore": spec.counter_label},
    {"Voce": "Data posizioni COT", "Valore": smart["report_date"].strftime("%d/%m/%Y")},
    {"Voce": "Codice CFTC", "Valore": smart["cftc_code"]},
    {"Voce": f"Δ {spec.trend_label} Long", "Valore": fmt_number(smart["trend_chg_l"], signed=True)},
    {"Voce": f"Δ {spec.trend_label} Short", "Valore": fmt_number(smart["trend_chg_s"], signed=True)},
    {"Voce": f"Δ {spec.counter_label} Long", "Valore": fmt_number(smart["counter_chg_l"], signed=True)},
    {"Voce": f"Δ {spec.counter_label} Short", "Valore": fmt_number(smart["counter_chg_s"], signed=True)},
    {"Voce": "COT Index", "Valore": f"{fmt_decimal(smart['cot_index'], 1)} — {smart['positioning']}"},
    {"Voce": "Term Structure", "Valore": term_structure},
    {"Voce": "Top 8 Net Long", "Valore": f"{fmt_pct(smart['conc_long'])} | Pctl {fmt_pct(smart['conc_long_rank'])}"},
    {"Voce": "Top 8 Net Short", "Valore": f"{fmt_pct(smart['conc_short'])} | Pctl {fmt_pct(smart['conc_short_rank'])}"},
    {"Voce": "Concentrazione", "Valore": smart["concentration_state"]},
]
st.dataframe(pd.DataFrame(tech_rows), width="stretch", hide_index=True)

flow_rows = pd.DataFrame(
    [
        {"Orizzonte": "1W", spec.trend_label: smart["trend_flow_1w"], spec.counter_label: smart["counter_flow_1w"]},
        {"Orizzonte": "3W", spec.trend_label: smart["trend_flow_3w"], spec.counter_label: smart["counter_flow_3w"]},
        {"Orizzonte": "6W", spec.trend_label: smart["trend_flow_6w"], spec.counter_label: smart["counter_flow_6w"]},
    ]
)
st.dataframe(flow_rows, width="stretch", hide_index=True)


# =============================================================================
# TERM STRUCTURE
# =============================================================================
if spec.family == "commodity":
    st.subheader("Term Structure — inserimento manuale")
    if term_structure == "Backwardation":
        st.success("Backwardation: il contratto vicino quota sopra il successivo. È una conferma positiva di tensione sul breve, ma non sostituisce il segnale COT.")
    elif term_structure == "Contango":
        st.warning("Contango: il contratto successivo quota sopra il vicino. La curva non offre una conferma rialzista immediata.")
    elif term_structure == "Curva piatta":
        st.info("Curva piatta: differenza M1–M2 non significativa.")
    else:
        st.info("Term Structure non impostata. Il motore Smart Money resta utilizzabile; il modulo Legacy non potrà classificare lo Short Covering con Backwardation.")


# =============================================================================
# GRAFICI
# =============================================================================
st.header("3. Grafici")
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(plot_cot_index(specific_df, spec.trend_label), width="stretch")
with chart_col2:
    st.plotly_chart(plot_net_positions(specific_df, spec.trend_label, spec.counter_label), width="stretch")

if not weekly_price.empty:
    st.plotly_chart(plot_weekly_price(weekly_price, yahoo_ticker), width="stretch")


# =============================================================================
# MODULO LEGACY
# =============================================================================
if show_legacy:
    st.header("4. Modulo Legacy di validazione")
    if legacy.get("available"):
        legacy_accent = accent_for_state(legacy["bias"])
        card(
            "ULTIMO REPORT LEGACY VS PENULTIMO",
            legacy["bias"],
            f"{legacy['verdict']}<br><b>Azione:</b> {legacy['action']}<br>"
            f"<b>Term Structure:</b> {term_structure}<br>"
            f"<b>Mercato CFTC:</b> {legacy_market_name} ({legacy_resolution})",
            legacy_accent,
        )
        l1, l2, l3, l4 = st.columns(4)
        l1.metric("Open Interest", fmt_number(legacy["oi"]), fmt_pct(legacy["pct_delta_oi"], signed=True, digits=2))
        l2.metric("Δ Open Interest", fmt_number(legacy["oi_delta"], signed=True))
        l3.metric("Flusso Noncommercial", fmt_number(legacy["trend_flow"], signed=True))
        l4.metric("Flusso Commercial", fmt_number(legacy["counter_flow"], signed=True))
    else:
        st.warning("Modulo Legacy non disponibile per il mercato selezionato.")


# =============================================================================
# ESPORTAZIONE
# =============================================================================
st.header("5. Esportazione")
summary_export = pd.DataFrame(
    [
        {
            "Mercato": spec.label,
            "Root": spec.root,
            "Report": spec.specific_report,
            "Data COT": smart["report_date"].isoformat(),
            "COT Index": smart["cot_index"],
            "Bias finale": smart["final_bias"],
            "Azione": smart["action"],
            "Prezzo Weekly": price_analysis["text"],
            "Term Structure": term_structure,
            "Flow trend 1W": smart["trend_flow_1w"],
            "Flow trend 3W": smart["trend_flow_3w"],
            "Flow trend 6W": smart["trend_flow_6w"],
            "Flow controparte 1W": smart["counter_flow_1w"],
            "Flow controparte 3W": smart["counter_flow_3w"],
            "Flow controparte 6W": smart["counter_flow_6w"],
            "Open Interest": smart["oi"],
            "Variazione OI %": smart["pct_delta_oi"],
        }
    ]
)

export_col1, export_col2 = st.columns(2)
with export_col1:
    st.download_button(
        "Scarica responso CSV",
        data=summary_export.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"cot_responso_{spec.root}_{smart['report_date'].isoformat()}.csv",
        mime="text/csv",
        width="stretch",
    )
with export_col2:
    history_export = specific_df.copy()
    history_export["date"] = history_export["date"].dt.strftime("%Y-%m-%d")
    st.download_button(
        "Scarica storico COT CSV",
        data=history_export.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"cot_storico_{spec.root}.csv",
        mime="text/csv",
        width="stretch",
    )


# =============================================================================
# DIAGNOSTICA
# =============================================================================
if show_debug:
    st.header("Diagnostica")
    st.write("Campi specifici risolti")
    st.json(specific_fields)
    if show_legacy:
        st.write("Campi Legacy risolti")
        st.json(legacy_fields)
    st.write("Ultima riga specifica normalizzata")
    st.dataframe(specific_df.tail(1), width="stretch", hide_index=True)

st.divider()
st.warning(
    "Il COT è un dato settimanale ritardato e descrive posizioni rilevate il martedì. "
    "Questa dashboard fornisce contesto e validazione, non un segnale automatico di ingresso."
)
