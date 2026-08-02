from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable
import io
import math
import re
import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont


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
    "Due sezioni indipendenti: analisi approfondita di un singolo future e screener settimanale di tutti i mercati. "
    "Il motore seleziona automaticamente TFF per i finanziari e Disaggregated per le commodity."
)


# =============================================================================
# COSTANTI CFTC
# =============================================================================
CFTC_DATASETS = {
    "Disaggregated": "72hh-3qpy",
    "Financial": "gpe5-46if",
}

CFTC_API_BASES = (
    "https://publicreporting.cftc.gov/resource",
    "https://publicreportinghub.cftc.gov/resource",
)

TERM_OPTIONS = ["Non disponibile", "Contango", "Backwardation", "Curva piatta"]
AI_PROMPT_FILENAME = "PROMPT.TXT"
AI_SCREENER_PROMPT_FILENAME = "PROMPT_SCREENER.TXT"
ALIGNMENT_UPPER = 80.0
ALIGNMENT_LOWER = 20.0


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
    "small_long": (
        "nonrept_positions_long",
        "nonrept_positions_long_all",
        "nonreportable_positions_long",
        "nonreportable_positions_long_all",
    ),
    "small_short": (
        "nonrept_positions_short",
        "nonrept_positions_short_all",
        "nonreportable_positions_short",
        "nonreportable_positions_short_all",
    ),
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
        raise CFTCError(f"Tipo di report non supportato: {report_type}")

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
                "small_long": to_float(record.get(fields["small_long"] or "")) if fields.get("small_long") else math.nan,
                "small_short": to_float(record.get(fields["small_short"] or "")) if fields.get("small_short") else math.nan,
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
    for column in (
        "oi", "trend_long", "trend_short", "counter_long", "counter_short",
        "small_long", "small_short", "conc_long", "conc_short",
    ):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["trend_net"] = df["trend_long"] - df["trend_short"]
    df["counter_net"] = df["counter_long"] - df["counter_short"]
    df["small_net"] = df["small_long"] - df["small_short"]

    def rolling_cot_index(series: pd.Series) -> pd.Series:
        rolling_min = series.rolling(cot_lookback, min_periods=min(26, cot_lookback)).min()
        rolling_max = series.rolling(cot_lookback, min_periods=min(26, cot_lookback)).max()
        denominator = rolling_max - rolling_min
        result = pd.Series(
            np.where(
                denominator.ne(0),
                100.0 * (series - rolling_min) / denominator,
                50.0,
            ),
            index=series.index,
            dtype="float64",
        )
        return result.clip(lower=0.0, upper=100.0)

    df["trend_index"] = rolling_cot_index(df["trend_net"])
    df["counter_index"] = rolling_cot_index(df["counter_net"])
    df["small_index"] = rolling_cot_index(df["small_net"])
    df["cot_index"] = df["trend_index"]
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
        concentration_state = "CONCENTRAZIONE TOP 8 LONG E SHORT ELEVATA — FRAGILITÀ ALTA"
    elif conc_long_high:
        concentration_state = "CONCENTRAZIONE TOP 8 LONG ELEVATA — RISCHIO LIQUIDAZIONE SE IL PREZZO SCENDE"
    elif conc_short_high:
        concentration_state = "CONCENTRAZIONE TOP 8 SHORT ELEVATA — RISCHIO SQUEEZE SE IL PREZZO SALE"
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
# COT ALIGNMENT MAP — CONTESTO STRUTTURALE
# =============================================================================
def alignment_zone(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    if value >= ALIGNMENT_UPPER:
        return "ESTREMO ALTO"
    if value <= ALIGNMENT_LOWER:
        return "ESTREMO BASSO"
    if value > 50:
        return "SOPRA LA MEDIA"
    if value < 50:
        return "SOTTO LA MEDIA"
    return "NEUTRO"


def analyze_alignment_map(df: pd.DataFrame, spec: MarketSpec) -> dict[str, Any]:
    unavailable = {
        "available": False,
        "speculative_index": math.nan,
        "counterparty_index": math.nan,
        "small_index": math.nan,
        "bull_score": 0,
        "bear_score": 0,
        "state": "DATI NON DISPONIBILI",
        "description": "Le posizioni Nonreportable / Small Traders non sono disponibili nel report selezionato.",
    }
    required = {"trend_index", "counter_index", "small_index"}
    if df.empty or not required.issubset(df.columns):
        return unavailable

    cur = df.iloc[-1]
    speculative_index = float(cur["trend_index"]) if not pd.isna(cur["trend_index"]) else math.nan
    counterparty_index = float(cur["counter_index"]) if not pd.isna(cur["counter_index"]) else math.nan
    small_index = float(cur["small_index"]) if not pd.isna(cur["small_index"]) else math.nan
    if any(pd.isna(value) for value in (speculative_index, counterparty_index, small_index)):
        return unavailable

    opposite_logic = spec.family == "commodity" or spec.is_fx

    bull_speculative = speculative_index <= ALIGNMENT_LOWER if opposite_logic else speculative_index >= ALIGNMENT_UPPER
    bull_counterparty = counterparty_index >= ALIGNMENT_UPPER
    bull_small = small_index <= ALIGNMENT_LOWER

    bear_speculative = speculative_index >= ALIGNMENT_UPPER if opposite_logic else speculative_index <= ALIGNMENT_LOWER
    bear_counterparty = counterparty_index <= ALIGNMENT_LOWER
    bear_small = small_index >= ALIGNMENT_UPPER

    bull_score = int(bull_speculative) + int(bull_counterparty) + int(bull_small)
    bear_score = int(bear_speculative) + int(bear_counterparty) + int(bear_small)

    bull_full = bull_score == 3
    bear_full = bear_score == 3
    bull_partial = bull_score == 2 and bull_score > bear_score
    bear_partial = bear_score == 2 and bear_score > bull_score
    mixed = bull_score == bear_score and bull_score >= 2

    if bull_full:
        state = "ALLINEAMENTO RIALZISTA 3/3"
    elif bear_full:
        state = "ALLINEAMENTO RIBASSISTA 3/3"
    elif bull_partial:
        state = "ALLINEAMENTO RIALZISTA 2/3"
    elif bear_partial:
        state = "ALLINEAMENTO RIBASSISTA 2/3"
    elif mixed:
        state = "SEGNALI MISTI"
    else:
        state = "NESSUN ALLINEAMENTO"

    if spec.family == "commodity":
        if bull_full:
            description = "Producer alti; Managed Money e Small Traders bassi."
        elif bear_full:
            description = "Producer bassi; Managed Money e Small Traders alti."
        elif bull_partial:
            description = "Due condizioni rialziste su tre sono agli estremi."
        elif bear_partial:
            description = "Due condizioni ribassiste su tre sono agli estremi."
        else:
            description = "Le categorie non sono contemporaneamente agli estremi."
    elif spec.is_fx:
        if bull_full:
            description = "Dealer alti; Leveraged Funds e Small Traders bassi."
        elif bear_full:
            description = "Dealer bassi; Leveraged Funds e Small Traders alti."
        elif bull_partial:
            description = "Allineamento contrarian FX rialzista parziale."
        elif bear_partial:
            description = "Allineamento contrarian FX ribassista parziale."
        else:
            description = "Le categorie valutarie non sono pienamente allineate."
    else:
        if bull_full:
            description = "Asset Manager e Leveraged Funds alti; Small Traders bassi."
        elif bear_full:
            description = "Asset Manager e Leveraged Funds bassi; Small Traders alti."
        elif bull_partial:
            description = "Consenso istituzionale rialzista parziale."
        elif bear_partial:
            description = "Consenso istituzionale ribassista parziale."
        else:
            description = "Non emerge un consenso istituzionale estremo."

    if bull_full or bear_full:
        description += " Massimo livello di allineamento COT, da confermare con flussi e prezzo."

    return {
        "available": True,
        "speculative_index": speculative_index,
        "counterparty_index": counterparty_index,
        "small_index": small_index,
        "speculative_zone": alignment_zone(speculative_index),
        "counterparty_zone": alignment_zone(counterparty_index),
        "small_zone": alignment_zone(small_index),
        "bull_score": bull_score,
        "bear_score": bear_score,
        "state": state,
        "description": description,
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


def load_operational_prompt() -> tuple[str, str]:
    """Carica le istruzioni AI da PROMPT.TXT senza memorizzarle in cache."""
    prompt_path = Path(__file__).with_name(AI_PROMPT_FILENAME)
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8").strip()
        if prompt_text:
            return prompt_text, AI_PROMPT_FILENAME
    except (OSError, UnicodeError):
        pass

    fallback = (
        "Scrivi in italiano con frasi semplici. Dichiara prima se il mercato è Long, "
        "Short, in costruzione oppure poco chiaro. Poi spiega la qualità dei flussi e "
        "indica quali conferme attendere. Non inventare dati o livelli mancanti."
    )
    return fallback, "prompt interno di emergenza"


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



def secret_value(name: str, default: str) -> str:
    try:
        value = st.secrets.get(name, default)
        return str(value) if value not in (None, "") else default
    except Exception:
        return default


# =============================================================================
# SCREENER — CLASSIFICAZIONE, PUNTEGGIO ED EXPORT EXCEL
# =============================================================================
def screener_flow_type(smart: dict[str, Any]) -> str:
    if smart.get("new_long"):
        return "NUOVI LONG"
    if smart.get("new_short"):
        return "NUOVI SHORT"
    if smart.get("short_covering"):
        return "SHORT COVERING"
    if smart.get("long_liquidation"):
        return "LIQUIDAZIONE LONG"
    if smart.get("trend_flow_1w", 0) > 0:
        return "MIGLIORAMENTO MISTO"
    if smart.get("trend_flow_1w", 0) < 0:
        return "PEGGIORAMENTO MISTO"
    return "FLUSSO NEUTRALE"


SCREENER_STATUS_OPTIONS = [
    "LONG IN COSTRUZIONE",
    "LONG CONFERMATO",
    "LONG CONFERMATO MA AFFOLLATO (NON INSEGUIRE)",
    "NEUTRALE / POCO CHIARO",
    "SHORT IN COSTRUZIONE",
    "SHORT CONFERMATO",
    "SHORT CONFERMATO MA AFFOLLATO (NON INSEGUIRE)",
]


def screener_status(
    smart: dict[str, Any],
    price: dict[str, Any],
    alignment: dict[str, Any],
) -> tuple[str, str]:
    # "Confermato ma affollato" richiede sia la conferma COT sia quella del prezzo.
    # Un estremo COT senza conferma del prezzo resta invece "in costruzione".
    if smart.get("crowded_long") and price.get("long_confirmed"):
        return "LONG CONFERMATO MA AFFOLLATO (NON INSEGUIRE)", "LONG"
    if smart.get("crowded_short") and price.get("short_confirmed"):
        return "SHORT CONFERMATO MA AFFOLLATO (NON INSEGUIRE)", "SHORT"
    if smart.get("confirmed_long") and price.get("long_confirmed"):
        return "LONG CONFERMATO", "LONG"
    if smart.get("confirmed_short") and price.get("short_confirmed"):
        return "SHORT CONFERMATO", "SHORT"

    bull_context = (
        smart.get("confirmed_long")
        or smart.get("trend_flow_1w", 0) > 0
        and (
            smart.get("trend_flow_3w", 0) > 0
            or alignment.get("bull_score", 0) >= 2
            or price.get("long_confirmed")
        )
    )
    bear_context = (
        smart.get("confirmed_short")
        or smart.get("trend_flow_1w", 0) < 0
        and (
            smart.get("trend_flow_3w", 0) < 0
            or alignment.get("bear_score", 0) >= 2
            or price.get("short_confirmed")
        )
    )

    if bull_context and not bear_context:
        return "LONG IN COSTRUZIONE", "LONG"
    if bear_context and not bull_context:
        return "SHORT IN COSTRUZIONE", "SHORT"
    return "NEUTRALE / POCO CHIARO", "NEUTRALE"


def calculate_screener_score(
    smart: dict[str, Any],
    price: dict[str, Any],
    alignment: dict[str, Any],
    oi_threshold: float,
) -> dict[str, Any]:
    status, direction = screener_status(smart, price, alignment)
    flow_type = screener_flow_type(smart)

    if "CONFERMATO" in status:
        motor_score = 30
    elif "IN COSTRUZIONE" in status:
        motor_score = 18
    else:
        motor_score = 5

    if flow_type in ("NUOVI LONG", "NUOVI SHORT"):
        flow_score = 20
    elif flow_type in ("SHORT COVERING", "LIQUIDAZIONE LONG"):
        flow_score = 5
    elif flow_type in ("MIGLIORAMENTO MISTO", "PEGGIORAMENTO MISTO"):
        flow_score = 10
    else:
        flow_score = 0

    flow_3w = float(smart.get("trend_flow_3w", 0) or 0)
    flow_6w = float(smart.get("trend_flow_6w", 0) or 0)
    if direction == "LONG":
        if flow_3w > 0 and flow_6w > 0:
            structure_score = 18
        elif flow_3w > 0 or flow_6w > 0:
            structure_score = 8
        elif flow_3w < 0 and flow_6w < 0:
            structure_score = -8
        else:
            structure_score = 0
        relevant_alignment = int(alignment.get("bull_score", 0))
        opposite_alignment = int(alignment.get("bear_score", 0))
    elif direction == "SHORT":
        if flow_3w < 0 and flow_6w < 0:
            structure_score = 18
        elif flow_3w < 0 or flow_6w < 0:
            structure_score = 8
        elif flow_3w > 0 and flow_6w > 0:
            structure_score = -8
        else:
            structure_score = 0
        relevant_alignment = int(alignment.get("bear_score", 0))
        opposite_alignment = int(alignment.get("bull_score", 0))
    else:
        structure_score = 0
        relevant_alignment = max(int(alignment.get("bull_score", 0)), int(alignment.get("bear_score", 0)))
        opposite_alignment = relevant_alignment

    alignment_score = {0: 0, 1: 4, 2: 10, 3: 15}.get(relevant_alignment, 0)
    if opposite_alignment >= 2 and opposite_alignment > relevant_alignment:
        alignment_score -= 5

    if direction == "LONG":
        if price.get("long_confirmed"):
            price_score = 15
        elif price.get("above_ema"):
            price_score = 8
        elif price.get("short_confirmed"):
            price_score = -10
        else:
            price_score = 0
    elif direction == "SHORT":
        if price.get("short_confirmed"):
            price_score = 15
        elif price.get("below_ema"):
            price_score = 8
        elif price.get("long_confirmed"):
            price_score = -10
        else:
            price_score = 0
    else:
        price_score = 0

    oi_change = smart.get("pct_delta_oi", math.nan)
    if pd.isna(oi_change):
        oi_score = 0
    elif abs(float(oi_change)) <= oi_threshold:
        oi_score = 3
    elif float(oi_change) > oi_threshold and flow_type in ("NUOVI LONG", "NUOVI SHORT"):
        oi_score = 10
    elif float(oi_change) > oi_threshold and direction != "NEUTRALE":
        oi_score = 6
    else:
        oi_score = 0

    penalty = 0
    if "AFFOLLATO" in status:
        penalty -= 8
    elif smart.get("concentration_state") == "CONCENTRAZIONE SOPRA LA NORMA":
        penalty -= 3

    age_days = int(smart.get("age_days", 0) or 0)
    if age_days > 17:
        penalty -= 30
    elif age_days > 10:
        penalty -= 10

    total = max(0, min(100, motor_score + flow_score + structure_score + alignment_score + price_score + oi_score + penalty))
    if total >= 80:
        quality = "MOLTO ALTA"
    elif total >= 65:
        quality = "ALTA"
    elif total >= 50:
        quality = "MEDIA"
    else:
        quality = "BASSA"

    return {
        "Stato": status,
        "Direzione": direction,
        "Tipo flusso": flow_type,
        "Qualità": quality,
        "Score": total,
        "Score motore": motor_score,
        "Score flusso": flow_score,
        "Score struttura": structure_score,
        "Score Alignment": alignment_score,
        "Score prezzo": price_score,
        "Score OI": oi_score,
        "Penalità": penalty,
    }


def analyze_market_for_screener(
    spec: MarketSpec,
    cot_lookback: int,
    oi_threshold: float,
) -> tuple[dict[str, Any], pd.DataFrame]:
    history_limit = max(cot_lookback + 12, 180)
    rows, market_name, resolution = fetch_market_history(spec.specific_report, spec, history_limit)
    history_df, _ = build_history_df(rows, spec.specific_report, spec, cot_lookback)
    weekly_price, price_error = fetch_weekly_price(spec.yahoo_ticker)
    price = analyze_price(weekly_price)
    smart = analyze_smart_money(history_df, spec, price, oi_threshold)
    alignment = analyze_alignment_map(history_df, spec)
    if not smart.get("available"):
        raise CFTCError(smart.get("final_detail", "Analisi non disponibile."))

    scoring = calculate_screener_score(smart, price, alignment, oi_threshold)
    matching_alignment = alignment.get("bull_score", 0) if scoring["Direzione"] == "LONG" else alignment.get("bear_score", 0) if scoring["Direzione"] == "SHORT" else max(alignment.get("bull_score", 0), alignment.get("bear_score", 0))
    price_confirmed = (
        scoring["Direzione"] == "LONG" and price.get("long_confirmed")
    ) or (
        scoring["Direzione"] == "SHORT" and price.get("short_confirmed")
    )

    row = {
        "Strumento": spec.label,
        "Root": spec.root,
        "Gruppo": spec.group,
        "Famiglia COT": spec.market_family_label,
        "Report": spec.specific_report,
        "Data COT": smart["report_date"].isoformat(),
        **scoring,
        "COT Index": round(float(smart["cot_index"]), 1) if not pd.isna(smart["cot_index"]) else math.nan,
        "Posizionamento": smart["positioning"],
        "Flow 1W": smart["trend_flow_1w"],
        "Flow 3W": smart["trend_flow_3w"],
        "Flow 6W": smart["trend_flow_6w"],
        "Flow controparte 1W": smart["counter_flow_1w"],
        "Variazione OI %": smart["pct_delta_oi"],
        "Prezzo Weekly": price["text"],
        "Prezzo confermato": bool(price_confirmed),
        "Alignment rialzista": int(alignment.get("bull_score", 0)),
        "Alignment ribassista": int(alignment.get("bear_score", 0)),
        "Alignment utile": int(matching_alignment),
        "Stato Alignment": alignment.get("state", "DATI NON DISPONIBILI"),
        "Speculativi Index": alignment.get("speculative_index", math.nan),
        "Controparte Index": alignment.get("counterparty_index", math.nan),
        "Small Traders Index": alignment.get("small_index", math.nan),
        "Concentrazione Top 8": smart["concentration_state"],
        "Bias motore": smart["final_bias"],
        "Indicazione": smart["action"],
        "Motivazione": smart["reason"],
        "Mercato CFTC": market_name,
        "Risoluzione nome": resolution,
        "Ticker Yahoo": spec.yahoo_ticker,
        "Errore prezzo": price_error or "",
    }
    return row, history_df


def screener_signature(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "empty"
    stable = frame.sort_values("Root").fillna("").astype(str)
    payload = stable.to_csv(index=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def build_screener_excel(results: pd.DataFrame, errors: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    ordered = results.sort_values(["Score", "Strumento"], ascending=[False, True]).reset_index(drop=True)
    display_columns = [
        "Strumento", "Stato", "Direzione", "Qualità", "Score", "Tipo flusso",
        "COT Index", "Alignment rialzista", "Alignment ribassista", "Variazione OI %",
        "Prezzo Weekly", "Concentrazione Top 8", "Data COT",
    ]

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        ordered[display_columns].to_excel(writer, sheet_name="Classifica generale", index=False)
        ordered[(ordered["Direzione"] == "LONG") & (ordered["Score"] >= 50)].to_excel(writer, sheet_name="Long interessanti", index=False)
        ordered[(ordered["Direzione"] == "SHORT") & (ordered["Score"] >= 50)].to_excel(writer, sheet_name="Short interessanti", index=False)
        ordered[ordered["Alignment utile"] >= 2].to_excel(writer, sheet_name="Alignment 2-3", index=False)
        ordered[ordered["Stato"].str.contains("AFFOLLATO", na=False)].to_excel(writer, sheet_name="Mercati affollati", index=False)
        ordered.to_excel(writer, sheet_name="Dati completi", index=False)
        errors.to_excel(writer, sheet_name="Errori", index=False)

        from openpyxl.formatting.rule import ColorScaleRule
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter

        header_fill = PatternFill("solid", fgColor="1F4E78")
        header_font = Font(color="FFFFFF", bold=True)
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            for column_cells in ws.columns:
                max_length = 0
                column_letter = get_column_letter(column_cells[0].column)
                for cell in column_cells[:200]:
                    value = "" if cell.value is None else str(cell.value)
                    max_length = max(max_length, min(len(value), 45))
                    cell.alignment = Alignment(vertical="top", wrap_text=False)
                ws.column_dimensions[column_letter].width = max(10, min(max_length + 2, 42))
            headers = {cell.value: cell.column for cell in ws[1]}
            if "Score" in headers and ws.max_row >= 2:
                col = get_column_letter(headers["Score"])
                ws.conditional_formatting.add(
                    f"{col}2:{col}{ws.max_row}",
                    ColorScaleRule(start_type="num", start_value=0, start_color="F8696B", mid_type="num", mid_value=60, mid_color="FFEB84", end_type="num", end_value=100, end_color="63BE7B"),
                )
            for pct_header in ("Variazione OI %",):
                if pct_header in headers:
                    col = get_column_letter(headers[pct_header])
                    for cell in ws[col][1:]:
                        cell.number_format = '0.00'

    return output.getvalue()



def _table_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Carica un font leggibile, con fallback al font predefinito di Pillow."""
    regular_candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    )
    bold_candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    )
    for candidate in bold_candidates if bold else regular_candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_image_text(
    draw: ImageDraw.ImageDraw,
    text: Any,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    """Divide il testo in righe che rientrano nella larghezza della cella."""
    value = "" if pd.isna(text) else str(text)
    if not value:
        return [""]

    lines: list[str] = []
    for paragraph in value.splitlines() or [value]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            width = draw.textbbox((0, 0), candidate, font=font)[2]
            if width <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines or [""]


def build_screener_jpg(frame: pd.DataFrame, export_label: str = "Tabella completa") -> bytes:
    """Crea un'immagine JPG della porzione selezionata della tabella visibile."""
    image_frame = frame.copy()
    if image_frame.empty:
        image_frame = pd.DataFrame({"Risultato": ["Nessun mercato visibile con i filtri correnti."]})

    preferred_widths = {
        "Posizione": 120,
        "Strumento": 270,
        "Stato": 360,
        "Qualità": 135,
        "Score": 105,
        "Tipo flusso": 205,
        "COT Index": 125,
        "Alignment rialzista": 145,
        "Alignment ribassista": 145,
        "Variazione OI %": 145,
        "Prezzo Weekly": 285,
        "Concentrazione Top 8": 590,
        "Data COT": 145,
    }
    columns = list(image_frame.columns)
    column_widths = [preferred_widths.get(column, 190) for column in columns]

    title_font = _table_font(38, bold=True)
    subtitle_font = _table_font(23)
    header_font = _table_font(22, bold=True)
    body_font = _table_font(21)

    margin = 28
    title_height = 100
    header_padding = 13
    cell_padding_x = 12
    cell_padding_y = 10
    line_height = 28
    table_width = sum(column_widths)
    canvas_width = table_width + margin * 2

    probe = Image.new("RGB", (canvas_width, 100), "white")
    probe_draw = ImageDraw.Draw(probe)

    wrapped_headers: list[list[str]] = []
    for column, width in zip(columns, column_widths):
        wrapped_headers.append(
            _wrap_image_text(probe_draw, column, header_font, width - 2 * cell_padding_x)
        )
    header_lines = max(len(lines) for lines in wrapped_headers)
    header_height = max(58, header_lines * line_height + 2 * header_padding)

    wrapped_rows: list[list[list[str]]] = []
    row_heights: list[int] = []
    for _, row in image_frame.iterrows():
        wrapped_cells: list[list[str]] = []
        max_lines = 1
        for column, width in zip(columns, column_widths):
            value = row[column]
            if column == "Score" and not pd.isna(value):
                value = f"{float(value):.0f}"
            elif column == "COT Index" and not pd.isna(value):
                value = f"{float(value):.1f}"
            elif column == "Variazione OI %" and not pd.isna(value):
                value = f"{float(value):+.2f}"
            lines = _wrap_image_text(probe_draw, value, body_font, width - 2 * cell_padding_x)
            wrapped_cells.append(lines)
            max_lines = max(max_lines, len(lines))
        wrapped_rows.append(wrapped_cells)
        row_heights.append(max(52, max_lines * line_height + 2 * cell_padding_y))

    footer_height = 45
    canvas_height = title_height + header_height + sum(row_heights) + footer_height + margin * 2
    image = Image.new("RGB", (canvas_width, canvas_height), "#F5F7FA")
    draw = ImageDraw.Draw(image)

    draw.text((margin, margin), f"COT Screener — {export_label}", font=title_font, fill="#111827")
    subtitle = f"Righe esportate: {len(frame)}   |   Generato il {date.today().isoformat()}"
    draw.text((margin, margin + 51), subtitle, font=subtitle_font, fill="#4B5563")

    x = margin
    y = margin + title_height
    for width, lines in zip(column_widths, wrapped_headers):
        draw.rectangle((x, y, x + width, y + header_height), fill="#1F2937", outline="#4B5563", width=1)
        text_y = y + (header_height - len(lines) * line_height) / 2
        for line in lines:
            draw.text((x + cell_padding_x, text_y), line, font=header_font, fill="white")
            text_y += line_height
        x += width

    y += header_height
    for row_index, (wrapped_cells, row_height) in enumerate(zip(wrapped_rows, row_heights)):
        x = margin
        row_fill = "#FFFFFF" if row_index % 2 == 0 else "#EEF2F7"
        for column, width, lines in zip(columns, column_widths, wrapped_cells):
            fill = row_fill
            if column == "Stato":
                joined = " ".join(lines)
                if "LONG CONFERMATO" in joined and "AFFOLLATO" not in joined:
                    fill = "#DCFCE7"
                elif "SHORT CONFERMATO" in joined and "AFFOLLATO" not in joined:
                    fill = "#FEE2E2"
                elif "AFFOLLATO" in joined:
                    fill = "#FEF3C7"
                elif "IN COSTRUZIONE" in joined:
                    fill = "#E0F2FE"
            draw.rectangle((x, y, x + width, y + row_height), fill=fill, outline="#CBD5E1", width=1)
            text_y = y + cell_padding_y
            for line in lines:
                draw.text((x + cell_padding_x, text_y), line, font=body_font, fill="#111827")
                text_y += line_height
            x += width
        y += row_height

    draw.text(
        (margin, canvas_height - margin - 25),
        "Lo Score ordina la qualità complessiva e non rappresenta un segnale automatico di ingresso.",
        font=subtitle_font,
        fill="#4B5563",
    )

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=92, optimize=True, subsampling=0)
    return output.getvalue()


def call_ai_provider(provider: str, model: str, prompt: str) -> str:
    if provider == "Google Gemini":
        from google import genai

        api_key = secret_value("GEMINI_API_KEY", "")
        if not api_key:
            raise KeyError("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or "Nessuna risposta ricevuta da Gemini."

    from groq import Groq

    api_key = secret_value("GROQ_API_KEY", "")
    if not api_key:
        raise KeyError("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Sei un analista COT prudente. Usa esclusivamente i dati della classifica, "
                    "non inventare livelli tecnici e non trasformare il COT in un segnale immediato di ingresso. "
                    "Rispetta obbligatoriamente la colonna Classificazione AI: ogni strumento deve comparire "
                    "in una sola sezione operativa e non può essere riclassificato."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or "Nessuna risposta ricevuta da Groq."


def load_screener_prompt_template() -> str:
    prompt_path = Path(__file__).with_name(AI_SCREENER_PROMPT_FILENAME)
    try:
        text = prompt_path.read_text(encoding="utf-8").strip()
        if text:
            return text
    except (OSError, UnicodeError):
        pass
    return (
        "Analizza i migliori {TOP_N} risultati dello screener COT. "
        "Spiega in italiano semplice perché sono in cima alla classifica, senza modificare lo Score "
        "e senza inventare livelli tecnici.\n\nDATI SCREENER\n{DATI_SCREENER}"
    )



def screener_ai_classification(status: str) -> str:
    """Assegna una sezione AI esclusiva in base allo Stato deterministico."""
    mapping = {
        "LONG CONFERMATO": "OPPORTUNITÀ LONG CONFERMATA",
        "SHORT CONFERMATO": "OPPORTUNITÀ SHORT CONFERMATA",
        "LONG IN COSTRUZIONE": "DA MONITORARE — LONG IN COSTRUZIONE",
        "SHORT IN COSTRUZIONE": "DA MONITORARE — SHORT IN COSTRUZIONE",
        "LONG CONFERMATO MA AFFOLLATO (NON INSEGUIRE)": "NON INSEGUIRE — LONG AFFOLLATO",
        "SHORT CONFERMATO MA AFFOLLATO (NON INSEGUIRE)": "NON INSEGUIRE — SHORT AFFOLLATO",
        "NEUTRALE / POCO CHIARO": "POCO CHIARO — NESSUN VANTAGGIO OPERATIVO",
    }
    return mapping.get(str(status), "POCO CHIARO — NESSUN VANTAGGIO OPERATIVO")


def build_screener_ai_prompt(top_rows: pd.DataFrame, top_n: int) -> str:
    ai_rows = top_rows.copy()
    ai_rows["Classificazione AI"] = ai_rows["Stato"].map(screener_ai_classification)
    compact_columns = [
        "Strumento", "Stato", "Classificazione AI", "Direzione", "Qualità", "Score", "Tipo flusso",
        "COT Index", "Flow 1W", "Flow 3W", "Flow 6W", "Variazione OI %",
        "Alignment rialzista", "Alignment ribassista", "Prezzo Weekly", "Concentrazione Top 8",
        "Indicazione", "Motivazione",
    ]
    table_text = ai_rows[compact_columns].to_csv(index=False)
    template = load_screener_prompt_template()
    return (
        template.replace("{TOP_N}", str(top_n))
        .replace("{DATI_SCREENER}", table_text)
        .strip()
    )


def render_screener() -> None:
    st.header("COT Screener — tutti i mercati")
    st.caption(
        "La scansione parte soltanto su richiesta. Ogni mercato usa lo stesso motore Smart Money, "
        "la stessa Alignment Map e la stessa conferma prezzo dell'analisi singola."
    )

    with st.sidebar:
        st.header("Impostazioni Screener")
        all_groups = sorted({m.group for m in MARKETS})
        selected_groups = st.multiselect("Famiglie da analizzare", all_groups, default=all_groups)
        available_markets = [m for m in MARKETS if m.group in selected_groups]
        selected_labels = st.multiselect(
            "Mercati",
            [m.label for m in available_markets],
            default=[m.label for m in available_markets],
            help="Puoi ridurre la selezione per velocizzare la prima prova.",
        )
        cot_lookback = st.selectbox(
            "COT Index lookback Screener",
            [26, 52, 156, 260],
            index=2,
            format_func=lambda x: f"{x} settimane",
            key="screener_lookback",
        )
        oi_threshold = st.number_input(
            "Soglia Open Interest Screener (%)",
            min_value=0.0,
            max_value=10.0,
            value=0.5,
            step=0.1,
            key="screener_oi_threshold",
        )
        run_scan = st.button("Avvia analisi di tutti i mercati selezionati", type="primary", width="stretch")
        st.caption("La prima scansione completa può richiedere alcuni minuti. I dati vengono poi memorizzati nella cache.")

    if run_scan:
        selected_specs = [MARKET_BY_LABEL[label] for label in selected_labels]
        if not selected_specs:
            st.warning("Seleziona almeno un mercato.")
        else:
            rows: list[dict[str, Any]] = []
            errors: list[dict[str, str]] = []
            progress = st.progress(0.0, text="Avvio screener...")
            status_box = st.empty()
            for index, spec in enumerate(selected_specs, start=1):
                status_box.info(f"Analisi {index}/{len(selected_specs)} — {spec.label}")
                try:
                    row, _ = analyze_market_for_screener(spec, int(cot_lookback), float(oi_threshold))
                    rows.append(row)
                except Exception as exc:
                    errors.append({"Strumento": spec.label, "Root": spec.root, "Errore": str(exc)})
                progress.progress(index / len(selected_specs), text=f"Completati {index}/{len(selected_specs)} mercati")
            progress.empty()
            status_box.empty()

            results_df = pd.DataFrame(rows)
            errors_df = pd.DataFrame(errors, columns=["Strumento", "Root", "Errore"])
            if not results_df.empty:
                results_df = results_df.sort_values(["Score", "Strumento"], ascending=[False, True]).reset_index(drop=True)
                results_df.insert(0, "Posizione", range(1, len(results_df) + 1))
            st.session_state["screener_results"] = results_df
            st.session_state["screener_errors"] = errors_df
            st.session_state["screener_signature"] = screener_signature(results_df)
            for key in ("screener_ai_answer", "screener_ai_context"):
                st.session_state.pop(key, None)

    results_df = st.session_state.get("screener_results", pd.DataFrame())
    errors_df = st.session_state.get("screener_errors", pd.DataFrame(columns=["Strumento", "Root", "Errore"]))
    if results_df.empty:
        st.info("Premi il pulsante nella sidebar per creare la prima classifica.")
        return

    st.success(f"Screener completato: {len(results_df)} mercati analizzati; {len(errors_df)} errori o dati mancanti.")

    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Mercati analizzati", len(results_df))
    metric2.metric("Score ≥ 65", int((results_df["Score"] >= 65).sum()))
    metric3.metric("Long", int((results_df["Direzione"] == "LONG").sum()))
    metric4.metric("Short", int((results_df["Direzione"] == "SHORT").sum()))

    st.subheader("Filtri classifica")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        direction_filter = st.selectbox("Direzione", ["TUTTI", "LONG", "SHORT", "NEUTRALE"])
    with f2:
        min_score = st.slider("Score minimo", 0, 100, 0, 5)
    with f3:
        min_alignment = st.selectbox("Alignment minimo", [0, 1, 2, 3], index=0, format_func=lambda x: f"{x}/3")
    with f4:
        price_only = st.toggle("Solo prezzo confermato", value=False)

    # Mostra sempre tutti gli stati possibili, anche quando uno stato non è presente
    # nei risultati della scansione corrente.
    status_options = SCREENER_STATUS_OPTIONS
    selected_statuses = st.multiselect("Stati", status_options, default=status_options)
    exclude_weak = st.toggle("Escludi short covering, liquidazione Long e flussi neutrali", value=False)

    filtered = results_df.copy()
    if direction_filter != "TUTTI":
        filtered = filtered[filtered["Direzione"] == direction_filter]
    filtered = filtered[filtered["Score"] >= min_score]
    filtered = filtered[filtered["Alignment utile"] >= min_alignment]
    filtered = filtered[filtered["Stato"].isin(selected_statuses)]
    if price_only:
        filtered = filtered[filtered["Prezzo confermato"]]
    if exclude_weak:
        filtered = filtered[~filtered["Tipo flusso"].isin(["SHORT COVERING", "LIQUIDAZIONE LONG", "FLUSSO NEUTRALE"])]

    visible_columns = [
        "Posizione", "Strumento", "Stato", "Qualità", "Score", "Tipo flusso",
        "COT Index", "Alignment rialzista", "Alignment ribassista", "Variazione OI %",
        "Prezzo Weekly", "Concentrazione Top 8", "Data COT",
    ]
    display_df = filtered[visible_columns].copy()
    display_df["Alignment rialzista"] = display_df["Alignment rialzista"].astype(int).astype(str) + "/3"
    display_df["Alignment ribassista"] = display_df["Alignment ribassista"].astype(int).astype(str) + "/3"
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
            "COT Index": st.column_config.NumberColumn("COT Index", format="%.1f"),
            "Variazione OI %": st.column_config.NumberColumn("Δ OI %", format="%+.2f"),
            "Alignment rialzista": "Bull",
            "Alignment ribassista": "Bear",
            "Concentrazione Top 8": st.column_config.TextColumn("Concentrazione Top 8", width="large"),
        },
    )
    st.caption(f"Risultati visibili: {len(filtered)} su {len(results_df)}. Lo Score ordina la qualità complessiva, non è un segnale automatico di ingresso.")

    with st.expander("Come viene costruito lo Score", expanded=False):
        st.write(
            "Il punteggio combina motore Smart Money, qualità del flusso, struttura 3–6W, Alignment Map, "
            "conferma del prezzo Weekly e Open Interest. Applica penalizzazioni per concentrazione e dati non recenti."
        )
        component_columns = [
            "Strumento", "Score", "Score motore", "Score flusso", "Score struttura",
            "Score Alignment", "Score prezzo", "Score OI", "Penalità",
        ]
        st.dataframe(filtered[component_columns], width="stretch", hide_index=True)

    excel_bytes = build_screener_excel(results_df, errors_df)

    # Le tre immagini rispettano i filtri correnti. Top 5 e Top 10 sono
    # semplicemente le prime righe della classifica attualmente visibile.
    jpg_top5_bytes = build_screener_jpg(display_df.head(5), "Top 5 risultati visibili")
    jpg_top10_bytes = build_screener_jpg(display_df.head(10), "Top 10 risultati visibili")
    jpg_total_bytes = build_screener_jpg(display_df, "Tabella completa visibile")

    export_col1, export_col2, export_col3, export_col4 = st.columns(4)
    with export_col1:
        st.download_button(
            "Scarica Screener Excel",
            data=excel_bytes,
            file_name=f"cot_screener_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
    with export_col2:
        st.download_button(
            "Scarica JPG Top 5",
            data=jpg_top5_bytes,
            file_name=f"cot_screener_top5_{date.today().isoformat()}.jpg",
            mime="image/jpeg",
            width="stretch",
        )
    with export_col3:
        st.download_button(
            "Scarica JPG Top 10",
            data=jpg_top10_bytes,
            file_name=f"cot_screener_top10_{date.today().isoformat()}.jpg",
            mime="image/jpeg",
            width="stretch",
        )
    with export_col4:
        st.download_button(
            "Scarica JPG Totale",
            data=jpg_total_bytes,
            file_name=f"cot_screener_totale_{date.today().isoformat()}.jpg",
            mime="image/jpeg",
            width="stretch",
        )

    if not errors_df.empty:
        with st.expander(f"Errori o dati mancanti ({len(errors_df)})", expanded=False):
            st.dataframe(errors_df, width="stretch", hide_index=True)

    st.divider()
    st.subheader("Spiegazione AI dei migliori risultati")
    st.caption("L'AI interviene una sola volta, dopo la classifica, e non modifica lo Score deterministico.")

    ai1, ai2, ai3 = st.columns([1, 1, 1])
    with ai1:
        top_n = st.radio("Numero di strumenti", [5, 10], horizontal=True, key="screener_ai_top_n")
    with ai2:
        provider = st.selectbox("Provider AI Screener", ["Google Gemini", "Groq"], key="screener_ai_provider")
    with ai3:
        if provider == "Google Gemini":
            model = st.text_input("Modello Gemini Screener", value=secret_value("GEMINI_MODEL", "gemini-3.5-flash"), key="screener_ai_model_gemini")
        else:
            model = st.text_input("Modello Groq Screener", value=secret_value("GROQ_MODEL", "openai/gpt-oss-120b"), key="screener_ai_model_groq")

    ai_source = filtered if not filtered.empty else results_df
    top_rows = ai_source.sort_values(["Score", "Strumento"], ascending=[False, True]).head(int(top_n))
    ai_context = f"{st.session_state.get('screener_signature', '')}|{top_n}|{provider}|{model}|" + ",".join(top_rows["Root"].astype(str))

    if st.button(f"Spiega con AI i primi {min(int(top_n), len(top_rows))} risultati", type="primary", width="stretch"):
        if top_rows.empty:
            st.warning("Nessun risultato disponibile con i filtri correnti.")
        else:
            prompt = build_screener_ai_prompt(top_rows, min(int(top_n), len(top_rows)))
            with st.spinner(f"Interrogo {provider}..."):
                try:
                    answer = call_ai_provider(provider, model, prompt)
                    st.session_state["screener_ai_answer"] = answer
                    st.session_state["screener_ai_context"] = ai_context
                except KeyError as exc:
                    st.error(f"Chiave API mancante nei Secrets di Streamlit: {exc}.")
                except ModuleNotFoundError as exc:
                    st.error(f"Dipendenza AI non installata: {exc}.")
                except Exception as exc:
                    st.error(f"Errore durante la comunicazione con l'AI: {exc}")

    if st.session_state.get("screener_ai_answer") and st.session_state.get("screener_ai_context") == ai_context:
        st.markdown("### Risposta dell'AI sullo Screener")
        st.write(st.session_state["screener_ai_answer"])

    st.divider()
    st.warning(
        "Lo screener serve a stabilire quali mercati meritano un approfondimento. "
        "Prima di operare apri sempre il singolo strumento e verifica il prezzo sul grafico."
    )




def render_single_analysis() -> None:
    # =============================================================================
    # SIDEBAR
    # =============================================================================
    st.header("Analisi singolo strumento")
    st.caption("Approfondimento completo di un solo future, con interrogazione AI facoltativa e risposta soltanto a video.")

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
        show_debug = st.toggle("Mostra diagnostica campi", value=False)

        st.divider()
        st.subheader("Term Structure")
        if spec.family != "commodity":
            term_structure = "Non applicabile"
            term_usage_status = "NON APPLICABILE"
            st.info("NON APPLICABILE")
            st.caption("Non viene utilizzata per indici, valute, tassi, volatilità e crypto CME.")
        else:
            term_usage_status = "OPZIONALE"
            st.info("OPZIONALE")
            st.caption("Non entra nel responso Smart Money né nell'Alignment Map. Puoi lasciarla su Non disponibile.")

            term_defaults = bundled_term_defaults()
            uploaded_term_file = st.file_uploader("Carica CSV opzionale", type=["csv"])
            if uploaded_term_file is not None:
                term_defaults.update(read_term_csv(uploaded_term_file))

            default_term = term_defaults.get(spec.root, "Non disponibile")
            default_index = TERM_OPTIONS.index(default_term) if default_term in TERM_OPTIONS else 0
            term_structure = st.selectbox("Curva M1–M2", TERM_OPTIONS, index=default_index)
            st.caption("Per salvare un valore permanente modifica term_structure.csv nel repository.")


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

            weekly_price, price_error = fetch_weekly_price(yahoo_ticker)
    except CFTCError as exc:
        st.error(f"Errore CFTC: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"Errore inatteso durante il recupero dei dati: {exc}")
        st.stop()

    price_analysis = analyze_price(weekly_price)
    smart = analyze_smart_money(specific_df, spec, price_analysis, float(oi_threshold))
    alignment = analyze_alignment_map(specific_df, spec)

    if not smart.get("available"):
        st.error(smart.get("final_detail", "Analisi non disponibile."))
        st.stop()


    # Una risposta AI appartiene sempre a un solo strumento e a una sola data COT.
    # Se cambia il mercato oppure arriva un nuovo report, la vecchia interrogazione viene eliminata.
    current_ai_data_context = f"{spec.root}|{smart['report_date'].isoformat()}"
    if st.session_state.get("_cot_ai_data_context") != current_ai_data_context:
        for state_key in ("cot_ai_answer", "cot_ai_context", "cot_ai_question"):
            st.session_state.pop(state_key, None)
        st.session_state["_cot_ai_data_context"] = current_ai_data_context


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
        f"{smart['final_detail']}<br><b>Prezzo:</b> {price_analysis['text']}",
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
        {"Voce": "Uso Term Structure", "Valore": term_usage_status},
        {"Voce": "Term Structure", "Valore": term_structure},
        {"Voce": "Top 8 Net Long", "Valore": f"{fmt_pct(smart['conc_long'])} | Pctl {fmt_pct(smart['conc_long_rank'])}"},
        {"Voce": "Top 8 Net Short", "Valore": f"{fmt_pct(smart['conc_short'])} | Pctl {fmt_pct(smart['conc_short_rank'])}"},
        {"Voce": "Concentrazione Top 8", "Valore": smart["concentration_state"]},
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
    # COT ALIGNMENT MAP
    # =============================================================================
    st.header("3. COT Alignment Map")
    st.caption(
        "Contesto strutturale calcolato sullo stesso report e sullo stesso lookback del motore Smart Money. "
        "Non misura il flusso settimanale e non sostituisce la conferma del prezzo."
    )

    if alignment["available"]:
        a1, a2, a3 = st.columns(3)
        a1.metric(
            spec.trend_label,
            fmt_decimal(alignment["speculative_index"], 1),
            alignment["speculative_zone"],
        )
        a2.metric(
            spec.counter_label,
            fmt_decimal(alignment["counterparty_index"], 1),
            alignment["counterparty_zone"],
        )
        a3.metric(
            "Nonreportable / Small Traders",
            fmt_decimal(alignment["small_index"], 1),
            alignment["small_zone"],
        )

        score_left, score_right = st.columns(2)
        score_left.metric("Allineamento rialzista", f"{alignment['bull_score']}/3")
        score_right.metric("Allineamento ribassista", f"{alignment['bear_score']}/3")

        card(
            "CONTESTO COT — ALIGNMENT MAP",
            alignment["state"],
            alignment["description"] +
            "<br><b>Regola:</b> Alignment Map prepara il contesto; Net Position conferma il flusso; il prezzo attiva l'operazione.",
            accent_for_state(alignment["state"]),
        )
    else:
        st.warning(
            "COT Alignment Map non disponibile: il dataset non ha restituito una serie valida "
            "per Nonreportable / Small Traders. Il responso Smart Money resta comunque utilizzabile."
        )


    # =============================================================================
    # TERM STRUCTURE
    # =============================================================================
    st.subheader("Term Structure")
    if term_usage_status == "NON APPLICABILE":
        st.info("NON APPLICABILE — questo mercato non richiede l'inserimento della curva M1–M2.")
    else:
        st.info("OPZIONALE — non modifica il responso Smart Money né il COT Alignment Map.")

    if spec.family == "commodity":
        if term_structure == "Backwardation":
            st.success("Backwardation: il contratto vicino quota sopra il successivo. È un'informazione aggiuntiva sulla curva, non un segnale COT.")
        elif term_structure == "Contango":
            st.warning("Contango: il contratto successivo quota sopra il vicino. È un'informazione aggiuntiva sulla curva.")
        elif term_structure == "Curva piatta":
            st.info("Curva piatta: differenza M1–M2 non significativa.")
        else:
            st.info("Valore non impostato. L'analisi Smart Money e l'Alignment Map restano complete.")


    # =============================================================================
    # GRAFICI
    # =============================================================================
    st.header("4. Grafici")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(plot_cot_index(specific_df, spec.trend_label), width="stretch")
    with chart_col2:
        st.plotly_chart(plot_net_positions(specific_df, spec.trend_label, spec.counter_label), width="stretch")

    if not weekly_price.empty:
        st.plotly_chart(plot_weekly_price(weekly_price, yahoo_ticker), width="stretch")


    # =============================================================================
    # INTERROGAZIONE AI
    # =============================================================================
    st.header("5. Analisi e interrogazione AI")
    st.caption(
        "L'AI interpreta il motore Smart Money, la qualità dei flussi e il COT Alignment Map già calcolati. "
        "Non modifica i dati e non trasforma il COT in un segnale immediato di ingresso."
    )


    def secret_value(name: str, default: str) -> str:
        try:
            value = st.secrets.get(name, default)
            return str(value) if value not in (None, "") else default
        except Exception:
            return default


    def build_ai_prompt(user_question: str, operational_prompt: str) -> tuple[str, str]:
        """Costruisce il prompt AI in due modalità automatiche.

        - Campo domanda vuoto: applica integralmente PROMPT.TXT.
        - Campo domanda compilato: ignora PROMPT.TXT e risponde soltanto alla domanda specifica.
        """
        custom_question = user_question.strip()
        use_custom_question = bool(custom_question)

        if use_custom_question:
            instruction_block = f"""
    MODALITÀ: DOMANDA SPECIFICA

    Ignora completamente il prompt operativo preimpostato contenuto in {AI_PROMPT_FILENAME}.
    Non generare automaticamente la lettura completa né il post social.
    Rispondi esclusivamente e direttamente alla domanda dell'utente riportata sotto.
    Usa soltanto i dati strutturati della dashboard e mantieni una risposta semplice, concreta e coerente con il responso deterministico.

    DOMANDA DELL'UTENTE
    {custom_question}
    """.strip()
            request_mode = "Domanda specifica — PROMPT.TXT ignorato"
        else:
            instruction_block = f"""
    MODALITÀ: ANALISI COMPLETA PREIMPOSTATA

    ISTRUZIONI OPERATIVE CARICATE DA {AI_PROMPT_FILENAME}

    {operational_prompt}

    RICHIESTA
    Applica integralmente il prompt operativo preimpostato e produci sia la lettura completa sia la versione breve per il post social.
    """.strip()
            request_mode = f"Analisi completa — {AI_PROMPT_FILENAME}"

        prompt = f"""
    {instruction_block}

    ==================================================
    FONTE DATI DISPONIBILE NELLA DASHBOARD PYTHON
    ==================================================

    In questa interrogazione non è allegato automaticamente uno screenshot.
    Usa come fonte principale esclusivamente i dati strutturati riportati sotto.
    La dashboard calcola automaticamente Smart Money Report, tabella tecnica e COT Alignment Map.
    Non calcola ancora POC, supporti o resistenze.
    Per questi elementi scrivi "dato non chiaramente leggibile" e non inventare valori o livelli.
    Quando un trigger numerico non è disponibile, descrivi soltanto la condizione necessaria.

    MERCATO
    - Strumento: {spec.label}
    - Famiglia: {spec.market_family_label}
    - Report CFTC: {spec.specific_report}
    - Categoria principale: {spec.trend_label}
    - Controparte: {spec.counter_label}
    - Data posizioni: {smart['report_date'].strftime('%d/%m/%Y')}
    - Data report precedente: {smart['previous_date'].strftime('%d/%m/%Y')}

    POSIZIONAMENTO E FLUSSI
    - COT Index: {smart['cot_index']:.1f} — {smart['positioning']}
    - Open Interest: {smart['oi']:.0f}
    - Variazione Open Interest 1W: {smart['pct_delta_oi']:+.2f}%
    - Delta {spec.trend_label} Long: {smart['trend_chg_l']:+.0f}
    - Delta {spec.trend_label} Short: {smart['trend_chg_s']:+.0f}
    - Flusso {spec.trend_label}: 1W {smart['trend_flow_1w']:+.0f}, 3W {smart['trend_flow_3w']:+.0f}, 6W {smart['trend_flow_6w']:+.0f}
    - Delta {spec.counter_label} Long: {smart['counter_chg_l']:+.0f}
    - Delta {spec.counter_label} Short: {smart['counter_chg_s']:+.0f}
    - Flusso {spec.counter_label}: 1W {smart['counter_flow_1w']:+.0f}, 3W {smart['counter_flow_3w']:+.0f}, 6W {smart['counter_flow_6w']:+.0f}
    - Concentrazione Top 8: {smart['concentration_state']}
    - Top 8 Long: {fmt_pct(smart['conc_long'])}, percentile {fmt_pct(smart['conc_long_rank'])}
    - Top 8 Short: {fmt_pct(smart['conc_short'])}, percentile {fmt_pct(smart['conc_short_rank'])}

    COT ALIGNMENT MAP
    - Disponibile: {"SÌ" if alignment['available'] else "NO"}
    - {spec.trend_label}: {fmt_decimal(alignment['speculative_index'], 1)} — {alignment.get('speculative_zone', 'N/A')}
    - {spec.counter_label}: {fmt_decimal(alignment['counterparty_index'], 1)} — {alignment.get('counterparty_zone', 'N/A')}
    - Nonreportable / Small Traders: {fmt_decimal(alignment['small_index'], 1)} — {alignment.get('small_zone', 'N/A')}
    - Allineamento rialzista: {alignment['bull_score']}/3
    - Allineamento ribassista: {alignment['bear_score']}/3
    - Stato: {alignment['state']}
    - Lettura: {alignment['description']}

    PREZZO WEEKLY
    - Stato: {price_analysis['text']}
    - Dettaglio: {price_analysis['detail']}

    TERM STRUCTURE
    - Stato d'uso: {term_usage_status}
    - Valore manuale: {term_structure}

    RESPONSO DETERMINISTICO SMART MONEY
    - Bias finale: {smart['final_bias']}
    - Dettaglio: {smart['final_detail']}
    - Ultimo report: {smart['last_report']}
    - Struttura 3-6W: {smart['structure']}
    - Lettura controparte: {smart['counter_reading']}
    - Cosa fare: {smart['action']}
    - Motivazione: {smart['reason']}

    VINCOLI FINALI DELLA DASHBOARD
    - Il responso deterministico è il punto di partenza: non contraddirlo senza dichiarare chiaramente il limite dei dati.
    - Usa i valori calcolati dell'Alignment Map; non inventare screenshot, POC, supporti, resistenze o livelli tecnici.
    - Distingui nuovi Long, nuovi Short, short covering, liquidazione Long e flusso misto usando i delta disponibili.
    - Un COT Index estremo descrive affollamento relativo, non un segnale automatico di inversione.
    - Considera la Term Structure soltanto secondo lo stato d'uso indicato.
    - Il COT non è un segnale immediato di ingresso.
    - In modalità domanda specifica, rispondi soltanto a quella domanda senza applicare formato, sezioni o output imposti da {AI_PROMPT_FILENAME}.
    """.strip()

        return prompt, request_mode


    operational_prompt, operational_prompt_source = load_operational_prompt()
    with st.expander(f"Prompt operativo preimpostato — {operational_prompt_source}", expanded=False):
        st.caption(
            "Il testo viene caricato automaticamente a ogni esecuzione. Per aggiornarlo modifica "
            f"{AI_PROMPT_FILENAME} nel repository, senza intervenire sul codice Python."
        )
        st.code(operational_prompt, language=None)

    ai_col1, ai_col2 = st.columns([1, 1])
    with ai_col1:
        ai_provider = st.selectbox("Provider AI", ["Google Gemini", "Groq"], key="ai_provider")
    with ai_col2:
        if ai_provider == "Google Gemini":
            ai_model = st.text_input(
                "Modello Gemini",
                value=secret_value("GEMINI_MODEL", "gemini-3.5-flash"),
                key="ai_model_gemini",
            )
        else:
            ai_model = st.text_input(
                "Modello Groq",
                value=secret_value("GROQ_MODEL", "openai/gpt-oss-120b"),
                key="ai_model_groq",
            )

    with st.form("cot_ai_form"):
        ai_question = st.text_area(
            "Domanda specifica — se compilata sostituisce PROMPT.TXT",
            placeholder=(
                "Lascia vuoto per ottenere l'analisi completa prevista da PROMPT.TXT. "
                "Scrivi una domanda per ignorare PROMPT.TXT e ricevere soltanto una risposta mirata, "
                "per esempio: concentrati solo sulla qualità dei flussi dell'ultimo report."
            ),
            help=(
                "Campo vuoto: viene applicato PROMPT.TXT. Campo compilato: PROMPT.TXT viene ignorato "
                "e l'AI risponde esclusivamente alla domanda inserita."
            ),
            height=105,
            key="cot_ai_question",
        )
        ai_submit = st.form_submit_button("Genera analisi con AI", type="primary", width="stretch")

    if ai_submit:
        prompt_ai, ai_request_mode = build_ai_prompt(ai_question, operational_prompt)
        with st.spinner(f"Interrogo {ai_provider}..."):
            try:
                if ai_provider == "Google Gemini":
                    from google import genai

                    api_key = secret_value("GEMINI_API_KEY", "")
                    if not api_key:
                        raise KeyError("GEMINI_API_KEY")
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(model=ai_model, contents=prompt_ai)
                    answer = response.text or "Nessuna risposta ricevuta da Gemini."
                else:
                    from groq import Groq

                    api_key = secret_value("GROQ_API_KEY", "")
                    if not api_key:
                        raise KeyError("GROQ_API_KEY")
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model=ai_model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Sei un analista COT prudente. Rispetta rigorosamente i dati forniti, "
                                    "non inventare informazioni e non sostituire il responso deterministico. "
                                    "Segui la modalità dichiarata nel messaggio utente: quando è DOMANDA SPECIFICA, "
                                    "ignora il prompt operativo preimpostato e rispondi soltanto alla domanda."
                                ),
                            },
                            {"role": "user", "content": prompt_ai},
                        ],
                        temperature=0.2,
                    )
                    answer = response.choices[0].message.content or "Nessuna risposta ricevuta da Groq."

                st.session_state["cot_ai_answer"] = answer
                st.session_state["cot_ai_context"] = (
                    f"{spec.root}|{smart['report_date'].isoformat()}|{ai_provider}|{ai_model}|{ai_request_mode}"
                )
            except KeyError as exc:
                st.error(
                    f"Chiave API mancante nei Secrets di Streamlit: {exc}. "
                    "Configura GEMINI_API_KEY oppure GROQ_API_KEY."
                )
            except ModuleNotFoundError as exc:
                st.error(
                    f"Dipendenza AI non installata: {exc}. Aggiorna requirements.txt con google-genai e groq."
                )
            except Exception as exc:
                error_text = str(exc)
                if "503" in error_text or "UNAVAILABLE" in error_text.upper():
                    st.warning("Il provider AI è temporaneamente non disponibile. Riprova più tardi o seleziona l'altro provider.")
                else:
                    st.error(f"Errore durante la comunicazione con l'AI: {exc}")

    saved_ai_context = st.session_state.get("cot_ai_context", "")
    if st.session_state.get("cot_ai_answer") and saved_ai_context.startswith(current_ai_data_context + "|"):
        st.markdown("### Risposta dell'AI")
        st.write(st.session_state["cot_ai_answer"])
        st.caption("Contesto usato: " + saved_ai_context)


    # =============================================================================
    # DATI STORICI
    # =============================================================================
    with st.expander("Dati storici COT ed esportazione", expanded=False):
        st.caption("La risposta AI resta soltanto a video. Qui puoi scaricare esclusivamente lo storico numerico COT del mercato selezionato.")
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
        st.write("Ultima riga specifica normalizzata")
        st.dataframe(specific_df.tail(1), width="stretch", hide_index=True)

    st.divider()
    st.warning(
        "Il COT è un dato settimanale ritardato e descrive posizioni rilevate il martedì. "
        "Questa dashboard fornisce contesto e validazione, non un segnale automatico di ingresso."
    )


# =============================================================================
# NAVIGAZIONE PRINCIPALE
# =============================================================================
with st.sidebar:
    st.header("Navigazione")
    app_section = st.radio(
        "Sezione",
        ["Analisi singolo strumento", "COT Screener"],
        index=0,
        help="Le due sezioni sono indipendenti: la prima approfondisce un mercato, la seconda crea la classifica completa.",
    )
    st.divider()

if app_section == "Analisi singolo strumento":
    render_single_analysis()
else:
    render_screener()
