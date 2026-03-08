"""
api/macro_utils.py
宏觀流動性監控模組

方法論基礎：
- Lyn Alden (2024) "Bitcoin: A Global Liquidity Barometer"
  - BTC 與全球流動性的 12 個月方向相關性達 83%，高於所有主要資產類別
  - 全球 M2（美元計價）是最佳流動性代理指標
  - 短期偏離可能由鏈上估值極端或特殊事件導致
- Arthur Hayes: Net Liquidity = Fed Balance Sheet (WALCL) - TGA - ON RRP
  - TGA 下降 = 財政部支出 = 流動性注入
  - RRP 下降 = 資金從 Fed 回流市場
- Michael Howell (Cross Border Capital): 全球央行資產負債表驅動風險資產價格

指標說明：
  Net Liquidity | WALCL-TGA-RRP | 週更 | 83% 方向相關(12M) | ★★★ Lyn Alden
  VIX           | Yahoo/FRED    | 即時 | 恐慌→拋售風險資產  | ★★ 通用風險指標
  SOFR          | NY Fed        | 日更 | 高利率→融資壓力    | ★★ Pozsar 框架
  USDJPY        | Yahoo         | 即時 | 套利平倉→賣壓      | ★★ 2024/8 實證
  US10Y         | Yahoo         | 即時 | 高殖利率→資金流出  | ★☆ 間接影響
  M2 YoY        | FRED          | 週更 | 擴張→風險資產上漲  | ★★★ Lyn Alden 核心
  10Y-2Y Spread | FRED          | 日更 | 倒掛→衰退預期      | ★☆ 長期指標
  DXY           | FRED          | 日更 | 美元弱→全球流動性升 | ★★ Lyn Alden 框架

資料源（免費 + 即時）：
- SOFR: NY Fed API（日更，比 FRED 快）
- TGA: Fiscal Data Treasury API（日更，比 FRED WDTGAL 快）
- VIX / USDJPY / US10Y: Yahoo Finance（盤中即時）
- WALCL / RRP: 仍從 FRED 讀（週更，無法加速）
- M1 / M2 / 10Y-2Y / DXY: FRED（日/週更）
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# ─── HTTP Helpers ─────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def _get(url: str, params: dict = None, timeout: int = 10) -> dict | None:
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"GET {url} failed: {e}")
        return None


# ─── Data Sources ─────────────────────────────────────────────────────────────


def get_sofr() -> Optional[Dict]:
    """
    SOFR from NY Fed API.
    Updates: next business day after market close (~08:00 ET).
    Returns: {"date": "2026-02-24", "rate": 4.30}
    """
    url = "https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json"
    data = _get(url)
    if not data:
        return None
    try:
        ref = data["refRates"][0]
        return {"date": ref["effectiveDate"], "rate": float(ref["percentRate"])}
    except (KeyError, IndexError, ValueError) as e:
        logger.warning(f"SOFR parse error: {e}")
        return None


def get_tga_daily() -> Optional[Dict]:
    """
    Treasury General Account daily balance from Fiscal Data API.
    Faster than FRED WDTGAL (D+1 vs D+5).
    Returns: {"date": "2026-02-24", "balance_billion": 823.4}
    """
    url = (
        "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
        "/v1/accounting/dts/operating_cash_balance"
    )
    params = {
        "fields": "record_date,open_today_bal,account_type",
        "filter": "account_type:eq:Treasury General Account (TGA) Opening Balance",
        "sort": "-record_date",
        "page[size]": "3",
    }
    data = _get(url, params=params)
    if not data:
        return None
    try:
        rows = data.get("data", [])
        if not rows:
            return None
        row = rows[0]
        balance_millions = float(row["open_today_bal"])
        return {
            "date": row["record_date"],
            "balance_billion": round(balance_millions / 1000, 2),
        }
    except (KeyError, ValueError) as e:
        logger.warning(f"TGA parse error: {e}")
        return None


def get_yahoo_price(symbol: str) -> Optional[float]:
    """
    Fetch latest price from Yahoo Finance (no API key needed).
    Symbols: ^VIX, USDJPY=X, ^TNX (US 10Y), ^IRX (US 3M), ^MOVE
    Returns: float price or None
    """
    encoded = requests.utils.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
    params = {"interval": "1d", "range": "2d"}
    data = _get(url, params=params)
    if not data:
        return None
    try:
        meta = data["chart"]["result"][0]["meta"]
        return float(meta["regularMarketPrice"])
    except (KeyError, IndexError, TypeError) as e:
        logger.warning(f"Yahoo Finance {symbol} parse error: {e}")
        return None


def get_yahoo_price_history(symbol: str, days: int = 10) -> List[float]:
    """
    Get price history for weekly change calculation.
    Returns list of closes (ascending date).
    """
    encoded = requests.utils.quote(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
    params = {"interval": "1d", "range": f"{days}d"}
    data = _get(url, params=params)
    if not data:
        return []
    try:
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        return [c for c in closes if c is not None]
    except (KeyError, IndexError, TypeError):
        return []


# ─── Signal Computation ───────────────────────────────────────────────────────


def compute_macro_signal(
    net_liq: Optional[float],
    net_liq_prev_week: Optional[float],
    sofr: Optional[float],
    vix: Optional[float],
    usdjpy: Optional[float],
    usdjpy_prev_week: Optional[float],
) -> Dict:
    """
    XinGPT-style macro signal for crypto contract trading.

    Score: -100 (extreme risk-off) to +100 (risk-on)
    Stance: BEARISH / CAUTIOUS / NEUTRAL / BULLISH
    """
    score = 0
    triggers = []

    # ── 1. Net Liquidity Weekly Change ────────────────────────────────────────
    if net_liq is not None and net_liq_prev_week is not None and net_liq_prev_week != 0:
        liq_change_pct = (net_liq - net_liq_prev_week) / abs(net_liq_prev_week) * 100

        if liq_change_pct <= -5:
            score -= 30
            triggers.append({
                "type": "DANGER",
                "indicator": "net_liquidity",
                "msg": f"淨流動性週降 {liq_change_pct:.1f}%（>5% 警戒線）",
                "action": "加密減倉預警",
            })
        elif liq_change_pct <= -2:
            score -= 15
            triggers.append({
                "type": "WARNING",
                "indicator": "net_liquidity",
                "msg": f"淨流動性週降 {liq_change_pct:.1f}%",
                "action": "謹慎持倉",
            })
        elif liq_change_pct >= 3:
            score += 20
            triggers.append({
                "type": "POSITIVE",
                "indicator": "net_liquidity",
                "msg": f"淨流動性週增 {liq_change_pct:.1f}%",
                "action": "流動性寬鬆，利多加密",
            })
    else:
        liq_change_pct = None

    # ── 2. SOFR ───────────────────────────────────────────────────────────────
    if sofr is not None:
        if sofr > 5.5:
            score -= 25
            triggers.append({
                "type": "DANGER",
                "indicator": "sofr",
                "msg": f"SOFR {sofr:.2f}% 突破 5.5%（融資壓力）",
                "action": "做空信號",
            })
        elif sofr > 5.0:
            score -= 10
            triggers.append({
                "type": "WARNING",
                "indicator": "sofr",
                "msg": f"SOFR {sofr:.2f}%（偏高）",
                "action": "注意融資成本",
            })

    # ── 3. VIX ────────────────────────────────────────────────────────────────
    if vix is not None:
        if vix > 30:
            score -= 20
            triggers.append({
                "type": "DANGER",
                "indicator": "vix",
                "msg": f"VIX {vix:.1f}（極度恐慌）",
                "action": "風險資產止損",
            })
        elif vix > 25:
            score -= 10
            triggers.append({
                "type": "WARNING",
                "indicator": "vix",
                "msg": f"VIX {vix:.1f}（恐慌上升）",
                "action": "降低槓桿",
            })
        elif vix < 15:
            score += 10

    # ── 4. USDJPY（日元套利風險）────────────────────────────────────────────
    if usdjpy is not None and usdjpy_prev_week is not None and usdjpy_prev_week != 0:
        jpy_change_pct = (usdjpy - usdjpy_prev_week) / abs(usdjpy_prev_week) * 100

        if jpy_change_pct <= -2:
            # 日元升值 = 套利平倉已發生 = 風險資產賣壓
            score -= 20
            triggers.append({
                "type": "DANGER",
                "indicator": "usdjpy",
                "msg": f"USDJPY 週降 {abs(jpy_change_pct):.1f}%（日元大升，套利平倉）",
                "action": "警戒風險資產賣壓",
            })
        elif jpy_change_pct >= 2:
            # 日元貶值 = 套利持續 = 潛在未來風險
            score -= 15
            triggers.append({
                "type": "WARNING",
                "indicator": "usdjpy",
                "msg": f"USDJPY 週升 {jpy_change_pct:.1f}%（日元貶值，套利倉位累積）",
                "action": "注意未來平倉風險",
            })
    else:
        jpy_change_pct = None

    # ── 5. Determine Stance ───────────────────────────────────────────────────
    if score <= -40:
        stance = "BEARISH"
        crypto_action = "禁止多頭，可做空"
    elif score <= -20:
        stance = "CAUTIOUS"
        crypto_action = "謹慎，偏空操作"
    elif score >= 20:
        stance = "BULLISH"
        crypto_action = "宏觀支持，可考慮多頭"
    else:
        stance = "NEUTRAL"
        crypto_action = "宏觀中性，依技術面操作"

    return {
        "score": score,
        "stance": stance,
        "crypto_action": crypto_action,
        "triggers": triggers,
        "computed_inputs": {
            "net_liq_weekly_change_pct": round(liq_change_pct, 2) if liq_change_pct is not None else None,
            "usdjpy_weekly_change_pct": round(jpy_change_pct, 2) if jpy_change_pct is not None else None,
        },
    }


# ─── Full Snapshot Builder ────────────────────────────────────────────────────


def build_macro_snapshot(walcl_billion: Optional[float], rrp_billion: Optional[float]) -> Dict:
    """
    Fetch all fast data sources and compute a full macro snapshot.

    Args:
        walcl_billion: Fed total assets from DB (most recent FRED weekly value)
        rrp_billion: ON RRP from DB (most recent FRED daily value)

    Returns:
        Complete snapshot dict ready for DB storage and API response.
    """
    today = date.today().isoformat()

    # ── Fetch fast sources ────────────────────────────────────────────────────
    sofr_data = get_sofr()
    tga_data = get_tga_daily()

    vix = get_yahoo_price("^VIX")
    usdjpy = get_yahoo_price("USDJPY=X")
    us10y = get_yahoo_price("^TNX")

    # USDJPY history for weekly change
    usdjpy_history = get_yahoo_price_history("USDJPY=X", days=10)
    usdjpy_prev_week = usdjpy_history[-8] if len(usdjpy_history) >= 8 else None

    # ── Net Liquidity ─────────────────────────────────────────────────────────
    tga_billion = tga_data["balance_billion"] if tga_data else None

    net_liq = None
    if walcl_billion is not None and tga_billion is not None and rrp_billion is not None:
        net_liq = walcl_billion - tga_billion - rrp_billion

    # We'd need historical net_liq to compute weekly change.
    # Caller should provide net_liq_prev_week from DB.
    # For now, set to None (filled by endpoint when DB history is available).
    net_liq_prev_week = None

    sofr = sofr_data["rate"] if sofr_data else None

    signal = compute_macro_signal(
        net_liq=net_liq,
        net_liq_prev_week=net_liq_prev_week,
        sofr=sofr,
        vix=vix,
        usdjpy=usdjpy,
        usdjpy_prev_week=usdjpy_prev_week,
    )

    snapshot = {
        "date": today,
        "sofr": sofr,
        "tga_billion": tga_billion,
        "vix": vix,
        "usdjpy": usdjpy,
        "us10y": us10y,
        "net_liq_billion": net_liq,
        "net_liq_weekly_change_pct": signal["computed_inputs"]["net_liq_weekly_change_pct"],
        "macro_score": signal["score"],
        "macro_stance": signal["stance"],
        "crypto_action": signal["crypto_action"],
        "triggers": signal["triggers"],
        "raw_data": {
            "sofr_source": sofr_data,
            "tga_source": tga_data,
            "walcl_billion": walcl_billion,
            "rrp_billion": rrp_billion,
            "usdjpy_prev_week": usdjpy_prev_week,
        },
    }

    return snapshot
