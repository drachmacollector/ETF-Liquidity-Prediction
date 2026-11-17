"""Candidate universe from System Specification §5.2 (US) used by the P01 probes.

The final universe is decided in P02 from the feasibility results; this list only drives probing.
"""

from __future__ import annotations

import re

# ticker -> (group, issuer_source_id)
US_CANDIDATES: dict[str, tuple[str, str]] = {
    # US_COMM_PHYS
    "GLD": ("US_COMM_PHYS", "us_iss_spdr_gold"),
    "GLDM": ("US_COMM_PHYS", "us_iss_spdr_gold"),
    "IAU": ("US_COMM_PHYS", "us_iss_ishares"),
    "SLV": ("US_COMM_PHYS", "us_iss_ishares"),
    "SIVR": ("US_COMM_PHYS", "us_iss_abrdn"),
    "PPLT": ("US_COMM_PHYS", "us_iss_abrdn"),
    "PALL": ("US_COMM_PHYS", "us_iss_abrdn"),
    # US_COMM_FUT
    "USO": ("US_COMM_FUT", "us_iss_uscf"),
    "UNG": ("US_COMM_FUT", "us_iss_uscf"),
    "BNO": ("US_COMM_FUT", "us_iss_uscf"),
    "UGA": ("US_COMM_FUT", "us_iss_uscf"),
    "USL": ("US_COMM_FUT", "us_iss_uscf"),
    "UNL": ("US_COMM_FUT", "us_iss_uscf"),
    "CPER": ("US_COMM_FUT", "us_iss_uscf"),
    "USCI": ("US_COMM_FUT", "us_iss_uscf"),
    "DBC": ("US_COMM_FUT", "us_iss_invesco"),
    "DBA": ("US_COMM_FUT", "us_iss_invesco"),
    "DBO": ("US_COMM_FUT", "us_iss_invesco"),
    "GSG": ("US_COMM_FUT", "us_iss_ishares"),
    "CORN": ("US_COMM_FUT", "us_iss_teucrium"),
    "WEAT": ("US_COMM_FUT", "us_iss_teucrium"),
    "SOYB": ("US_COMM_FUT", "us_iss_teucrium"),
    # US_BOND
    "LQD": ("US_BOND", "us_iss_ishares"),
    "HYG": ("US_BOND", "us_iss_ishares"),
    "MUB": ("US_BOND", "us_iss_ishares"),
    "EMB": ("US_BOND", "us_iss_ishares"),
    "AGG": ("US_BOND", "us_iss_ishares"),
    "TLT": ("US_BOND", "us_iss_ishares"),
    "JNK": ("US_BOND", "us_iss_ssga"),
    "BKLN": ("US_BOND", "us_iss_invesco"),
    "BND": ("US_BOND", "us_iss_vanguard"),
    # US_INTL
    "EWJ": ("US_INTL", "us_iss_ishares"),
    "EWH": ("US_INTL", "us_iss_ishares"),
    "EWZ": ("US_INTL", "us_iss_ishares"),
    "EWW": ("US_INTL", "us_iss_ishares"),
    "FXI": ("US_INTL", "us_iss_ishares"),
    "EEM": ("US_INTL", "us_iss_ishares"),
    "INDA": ("US_INTL", "us_iss_ishares"),
    "TUR": ("US_INTL", "us_iss_ishares"),
    "ERUS": ("US_INTL", "us_iss_ishares"),
    "EGPT": ("US_INTL", "us_iss_vaneck"),
    "RSX": ("US_INTL", "us_iss_vaneck"),
    "GREK": ("US_INTL", "us_iss_globalx"),
    "ASHR": ("US_INTL", "us_iss_xtrackers"),
    # US_CTRL
    "SPY": ("US_CTRL", "us_iss_ssga"),
    "DIA": ("US_CTRL", "us_iss_ssga"),
    "IVV": ("US_CTRL", "us_iss_ishares"),
    "IWM": ("US_CTRL", "us_iss_ishares"),
    "QQQ": ("US_CTRL", "us_iss_invesco"),
    "VOO": ("US_CTRL", "us_iss_vanguard"),
}

# --------------------------------------------------------------------------- India
# AMFI files the same kind of ETF under inconsistent categories (e.g., "Other Scheme - Gold ETF",
# "Exchange Traded Funds (ETFs) - Equity ETF", "Other Scheme - Other  ETFs"), so classification uses the
# scheme name, restricted to ETF categories and excluding fund-of-funds and index funds.
_IN_OVERSEAS = re.compile(
    r"NASDAQ|NYSE|FANG|S&P 500|Hang Seng|Nikkei|Japan|Taiwan|China|Global|World|US Tech|Europe|EAFE|MAFANG",
    flags=re.I,
)
_IN_DEBT = re.compile(
    r"G-?Sec|Gilt|Bharat Bond|Liquid|SDL|Bond|Overnight|1D Rate|T-?Bill|Money Market", flags=re.I
)
_IN_FOF = re.compile(r"Fund of Fund|FOF|Index Fund", flags=re.I)

# Controls chosen by NSE symbol (confirmed in P02).
IN_CONTROL_SYMBOLS = ["NIFTYBEES", "SETFNIF50", "BANKBEES", "JUNIORBEES"]


def classify_india(scheme_name: str, category: str | None) -> str | None:
    """Return IN_GOLD / IN_SILVER / IN_INTL / IN_DEBT for an ETF scheme, or None if not in scope."""
    cat = category or ""
    name = scheme_name or ""
    if "ETF" not in cat or _IN_FOF.search(name):
        return None
    if re.search(r"\bSilver\b", name, flags=re.I):
        return "IN_SILVER"
    if re.search(r"\bGold\b", name, flags=re.I) and not re.search(r"Mining|Miners", name, flags=re.I):
        return "IN_GOLD"
    if _IN_OVERSEAS.search(name) and not re.search(r"\bIndia\b", name, flags=re.I):
        return "IN_INTL"
    if "Debt ETF" in cat or _IN_DEBT.search(name):
        return "IN_DEBT"
    return None
