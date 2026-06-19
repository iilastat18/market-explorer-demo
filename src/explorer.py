from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


REGIONS = ["US", "Europe", "Asia"]
SECTORS = ["Software", "Semis", "Industrials", "Payments", "Healthcare", "Energy", "Consumer", "Utilities"]
PROFILES: dict[str, dict[str, float]] = {
    "Balanced": {"liquidity": 0.30, "momentum": 0.30, "quality": 0.20, "value": 0.20},
    "Liquidity First": {"liquidity": 0.45, "momentum": 0.20, "quality": 0.20, "value": 0.15},
    "Momentum": {"liquidity": 0.20, "momentum": 0.45, "quality": 0.15, "value": 0.20},
    "Defensive": {"liquidity": 0.25, "momentum": 0.10, "quality": 0.40, "value": 0.25},
}

_ADJECTIVES = [
    "Northbridge",
    "Atlas",
    "Silver",
    "Prime",
    "Summit",
    "Vertex",
    "Meridian",
    "Cobalt",
    "Harbor",
    "Aurora",
    "Keystone",
    "Bluecrest",
]
_NOUNS = {
    "Software": "Systems",
    "Semis": "Semiconductors",
    "Industrials": "Automation",
    "Payments": "Payments",
    "Healthcare": "Health",
    "Energy": "Energy",
    "Consumer": "Retail",
    "Utilities": "Grid",
}
_SECTOR_CODES = {
    "Software": "SW",
    "Semis": "SM",
    "Industrials": "IN",
    "Payments": "PY",
    "Healthcare": "HC",
    "Energy": "EN",
    "Consumer": "CS",
    "Utilities": "UT",
}
_REGION_CODES = {"US": "U", "Europe": "E", "Asia": "A"}


@dataclass(frozen=True)
class ExplorerSnapshot:
    universe: pd.DataFrame
    region_summary: pd.DataFrame
    sector_summary: pd.DataFrame


def _scaled(series: pd.Series, invert: bool = False) -> pd.Series:
    lo = float(series.min())
    hi = float(series.max())
    if np.isclose(lo, hi):
        values = pd.Series(50.0, index=series.index)
    else:
        values = ((series - lo) / (hi - lo)) * 100
    if invert:
        values = 100 - values
    return values.clip(0, 100).round(2)


def _symbol_seed(symbol: str) -> int:
    return sum((idx + 1) * ord(char) for idx, char in enumerate(symbol))


def build_universe(seed: int = 24, n_assets: int = 72) -> ExplorerSnapshot:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []

    for idx in range(n_assets):
        region = REGIONS[idx % len(REGIONS)]
        sector = SECTORS[(idx * 3) % len(SECTORS)]
        adjective = _ADJECTIVES[idx % len(_ADJECTIVES)]
        name = f"{adjective} {_NOUNS[sector]}"
        symbol = f"{_REGION_CODES[region]}{_SECTOR_CODES[sector]}{idx + 1:02d}"

        market_cap = float(np.clip(rng.lognormal(mean=2.8, sigma=0.55), 3.5, 385.0))
        adv = float(np.clip(market_cap * rng.uniform(0.5, 1.8), 8.0, 220.0))
        spread = float(np.clip(28 - np.log1p(adv) * 4.3 + rng.normal(0, 1.8), 4.5, 38.0))
        vol = float(np.clip(rng.normal(26, 8), 9, 58))
        beta = float(np.clip(rng.normal(1.03, 0.23), 0.55, 1.85))
        momentum_1m = float(np.clip(rng.normal(2.0, 8.5), -18, 24))
        momentum_3m = float(np.clip(momentum_1m * rng.uniform(1.3, 2.6) + rng.normal(0, 4), -28, 42))
        relative_value = float(np.clip(rng.normal(0, 12), -24, 26))
        earnings_revision = float(np.clip(rng.normal(1.4, 5.0), -12, 15))
        flow_signal = float(np.clip(rng.normal(0.4, 1.3), -2.6, 3.2))
        short_interest = float(np.clip(rng.normal(4.5, 2.4), 0.3, 18.0))
        price = float(np.clip(rng.lognormal(mean=3.9, sigma=0.45), 14, 420))

        market_cap_bucket = (
            "Mega Cap" if market_cap >= 120 else "Large Cap" if market_cap >= 35 else "Mid Cap" if market_cap >= 12 else "Small Cap"
        )
        liquidity_tier = "Tier 1" if adv >= 90 else "Tier 2" if adv >= 45 else "Tier 3"

        rows.append(
            {
                "symbol": symbol,
                "company": name,
                "region": region,
                "sector": sector,
                "price": round(price, 2),
                "market_cap_b": round(market_cap, 2),
                "market_cap_bucket": market_cap_bucket,
                "adv_usd_m": round(adv, 2),
                "spread_bps": round(spread, 1),
                "vol_20d_pct": round(vol, 1),
                "beta": round(beta, 2),
                "momentum_1m_pct": round(momentum_1m, 1),
                "momentum_3m_pct": round(momentum_3m, 1),
                "relative_value_pct": round(relative_value, 1),
                "earnings_revision_pct": round(earnings_revision, 1),
                "flow_signal": round(flow_signal, 2),
                "short_interest_pct": round(short_interest, 1),
                "liquidity_tier": liquidity_tier,
            }
        )

    universe = pd.DataFrame(rows)
    universe["liquidity_score"] = (
        _scaled(universe["adv_usd_m"]) * 0.65
        + _scaled(universe["spread_bps"], invert=True) * 0.25
        + _scaled(universe["market_cap_b"]) * 0.10
    ).round(2)
    universe["momentum_score"] = (
        _scaled(universe["momentum_1m_pct"]) * 0.45
        + _scaled(universe["momentum_3m_pct"]) * 0.35
        + _scaled(universe["flow_signal"]) * 0.20
    ).round(2)
    universe["quality_score"] = (
        _scaled(universe["vol_20d_pct"], invert=True) * 0.45
        + _scaled(universe["beta"], invert=True) * 0.25
        + _scaled(universe["earnings_revision_pct"]) * 0.30
    ).round(2)
    universe["value_score"] = (
        _scaled(universe["relative_value_pct"]) * 0.65
        + _scaled(universe["short_interest_pct"], invert=True) * 0.35
    ).round(2)

    scored = score_universe(universe, profile="Balanced")
    scored["signal_tag"] = scored.apply(signal_tag, axis=1)
    scored["score_note"] = scored.apply(score_note, axis=1)

    region_summary = (
        scored.groupby("region", as_index=False)
        .agg(
            names=("symbol", "count"),
            avg_score=("radar_score", "mean"),
            avg_adv=("adv_usd_m", "mean"),
            avg_spread=("spread_bps", "mean"),
            avg_momentum=("momentum_1m_pct", "mean"),
        )
        .round(2)
    )
    sector_summary = (
        scored.groupby(["region", "sector"], as_index=False)
        .agg(
            avg_score=("radar_score", "mean"),
            avg_adv=("adv_usd_m", "mean"),
            avg_spread=("spread_bps", "mean"),
        )
        .round(2)
    )
    return ExplorerSnapshot(universe=scored, region_summary=region_summary, sector_summary=sector_summary)


def score_universe(universe: pd.DataFrame, profile: str) -> pd.DataFrame:
    weights = PROFILES[profile]
    scored = universe.copy()
    scored["radar_score"] = (
        scored["liquidity_score"] * weights["liquidity"]
        + scored["momentum_score"] * weights["momentum"]
        + scored["quality_score"] * weights["quality"]
        + scored["value_score"] * weights["value"]
    ).round(2)
    scored["rank"] = scored["radar_score"].rank(method="dense", ascending=False).astype(int)
    return scored.sort_values(["rank", "radar_score", "adv_usd_m"], ascending=[True, False, False]).reset_index(drop=True)


def signal_tag(row: pd.Series) -> str:
    if row["momentum_score"] >= 70 and row["liquidity_score"] >= 60:
        return "Trending Liquid"
    if row["quality_score"] >= 72 and row["vol_20d_pct"] <= 20:
        return "Defensive Compounder"
    if row["value_score"] >= 70 and row["momentum_score"] < 55:
        return "Re-rating Watch"
    if row["spread_bps"] >= 20 or row["adv_usd_m"] < 25:
        return "Needs Care"
    return "Core Screen"


def score_note(row: pd.Series) -> str:
    drivers: list[str] = []
    if row["liquidity_score"] >= 70:
        drivers.append("deep liquidity")
    if row["momentum_score"] >= 70:
        drivers.append("strong momentum")
    if row["quality_score"] >= 70:
        drivers.append("stable quality")
    if row["value_score"] >= 70:
        drivers.append("valuation support")
    if not drivers:
        drivers.append("balanced but mixed signals")
    return ", ".join(drivers[:2])


def price_history(symbol: str, periods: int = 90) -> pd.DataFrame:
    rng = np.random.default_rng(_symbol_seed(symbol))
    dates = pd.date_range(end="2026-06-18", periods=periods, freq="B")
    base = float(np.clip(rng.lognormal(mean=4.0, sigma=0.33), 20, 260))
    returns = rng.normal(0.0008, 0.018, size=periods)
    prices = [base]
    for step in returns[1:]:
        prices.append(max(8.0, prices[-1] * (1 + step)))
    volume = np.clip(rng.normal(1.2, 0.35, size=periods), 0.5, 2.4)
    history = pd.DataFrame(
        {
            "date": dates,
            "close": np.round(prices, 2),
            "volume_index": np.round(volume * 100, 1),
        }
    )
    history["drawdown_pct"] = ((history["close"] / history["close"].cummax()) - 1).mul(100).round(2)
    history["return_pct"] = history["close"].pct_change().fillna(0).mul(100).round(2)
    return history


def factor_breakdown(row: pd.Series) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"pillar": "Liquidity", "score": float(row["liquidity_score"])},
            {"pillar": "Momentum", "score": float(row["momentum_score"])},
            {"pillar": "Quality", "score": float(row["quality_score"])},
            {"pillar": "Value", "score": float(row["value_score"])},
        ]
    )


def filter_universe(
    universe: pd.DataFrame,
    *,
    regions: Iterable[str],
    sectors: Iterable[str],
    buckets: Iterable[str],
    min_adv: float,
    max_spread: float,
    min_score: float,
) -> pd.DataFrame:
    frame = universe.copy()
    if regions:
        frame = frame.loc[frame["region"].isin(list(regions))]
    if sectors:
        frame = frame.loc[frame["sector"].isin(list(sectors))]
    if buckets:
        frame = frame.loc[frame["market_cap_bucket"].isin(list(buckets))]
    frame = frame.loc[frame["adv_usd_m"] >= min_adv]
    frame = frame.loc[frame["spread_bps"] <= max_spread]
    frame = frame.loc[frame["radar_score"] >= min_score]
    return frame.reset_index(drop=True)
