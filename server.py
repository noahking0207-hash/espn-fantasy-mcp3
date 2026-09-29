import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ESPN Fantasy Data")

BASE = "https://lm-api-reads.fantasy.espn.com"
SPORT = os.getenv("ESPN_SPORT", "ffl")
SEASON = int(os.getenv("ESPN_SEASON", "2026"))
LEAGUE_ID = os.getenv("ESPN_LEAGUE_ID", "")
ESPN_S2 = os.getenv("ESPN_S2", "")
ESPN_SWID = os.getenv("ESPN_SWID", "")
API_KEY = os.getenv("MCP_API_KEY", "")
TIMEOUT = float(os.getenv("ESPN_TIMEOUT", "20"))


def _auth_headers() -> dict[str, str]:
    return {"Accept": "application/json"}


def _cookies() -> dict[str, str]:
    c = {}
    if ESPN_S2:
        c["espn_s2"] = ESPN_S2
    if ESPN_SWID:
        c["SWID"] = ESPN_SWID
    return c


def _check_server_key(provided: str | None) -> None:
    if API_KEY and provided != API_KEY:
        raise ValueError("Unauthorized")


def _league_url() -> str:
    if not LEAGUE_ID:
        raise ValueError("ESPN_LEAGUE_ID is not configured")
    return f"{BASE}/apis/v3/games/{SPORT}/seasons/{SEASON}/segments/0/leagues/{LEAGUE_ID}"


async def _get(view: str, headers: dict[str, str] | None = None, params: dict[str, str] | None = None) -> Any:
    h = _auth_headers()
    if headers:
        h.update(headers)
    p = dict(params or {})
    p["view"] = view
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(_league_url(), params=p, headers=h, cookies=_cookies())
        r.raise_for_status()
        return r.json()


async def _get_players(filter_obj: dict[str, Any], scoring_period_id: int | None = None) -> Any:
    if not LEAGUE_ID:
        raise ValueError("ESPN_LEAGUE_ID is not configured")
    url = _league_url()
    params: dict[str, str] = {"view": "kona_player_info"}
    if scoring_period_id is not None:
        params["scoringPeriodId"] = str(scoring_period_id)
    headers = {"X-Fantasy-Filter": json.dumps(filter_obj, separators=(",", ":"))}
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(url, params=params, headers=headers, cookies=_cookies())
        r.raise_for_status()
        return r.json()


@mcp.tool()
async def get_league(authorization: str | None = None) -> dict[str, Any]:
    """Return league settings, teams, standings, and current status."""
    _check_server_key(authorization)
    data = await _get("mSettings")
    # mSettings can return either an object or a one-element array depending on ESPN surface.
    return data[0] if isinstance(data, list) and data else data


@mcp.tool()
async def get_teams_and_rosters(authorization: str | None = None) -> dict[str, Any]:
    """Return all league teams with roster/ownership data."""
    _check_server_key(authorization)
    teams = await _get("mTeam")
    rosters = await _get("mRoster")
    return {"teams": teams, "rosters": rosters}


@mcp.tool()
async def get_matchups(authorization: str | None = None, scoring_period_id: int | None = None) -> dict[str, Any]:
    """Return matchup and score context for the requested scoring period."""
    _check_server_key(authorization)
    params = {}
    if scoring_period_id is not None:
        params["scoringPeriodId"] = str(scoring_period_id)
    return {"matchups": await _get("mMatchup", params=params),
            "scores": await _get("mMatchupScore", params=params)}


@mcp.tool()
async def get_standings(authorization: str | None = None) -> dict[str, Any]:
    """Return league standings/power context."""
    _check_server_key(authorization)
    return await _get("mStandings")


@mcp.tool()
async def get_free_agents(authorization: str | None = None, scoring_period_id: int | None = None, limit: int = 100) -> dict[str, Any]:
    """Return available free agents/waiver players, ranked by ESPN ownership."""
    _check_server_key(authorization)
    limit = max(1, min(int(limit), 500))
    filt = {"players": {
        "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
        "limit": limit,
        "sortPercOwned": {"sortPriority": 4, "sortAsc": False},
    }}
    return await _get_players(filt, scoring_period_id)


@mcp.tool()
async def get_player_pool(authorization: str | None = None, scoring_period_id: int | None = None, limit: int = 200) -> dict[str, Any]:
    """Return a broader active player pool for comparison and valuation."""
    _check_server_key(authorization)
    limit = max(1, min(int(limit), 500))
    filt = {"players": {
        "filterActive": {"value": True},
        "limit": limit,
        "sortPercOwned": {"sortPriority": 4, "sortAsc": False},
    }}
    return await _get_players(filt, scoring_period_id)


@mcp.tool()
async def get_transactions(authorization: str | None = None) -> dict[str, Any]:
    """Return recent league transactions/trends where ESPN exposes them."""
    _check_server_key(authorization)
    return await _get("mTransactions2")


@mcp.tool()
async def get_draft(authorization: str | None = None) -> dict[str, Any]:
    """Return draft and roster-ownership history where available."""
    _check_server_key(authorization)
    return await _get("mDraftDetail")


@mcp.tool()
async def get_status(authorization: str | None = None) -> dict[str, Any]:
    """Return current ESPN fantasy league status/week context."""
    _check_server_key(authorization)
    return await _get("mStatus")


if __name__ == "__main__":
    # Streamable HTTP is the transport expected by portable Agent Plugins MCP configuration.
    mcp.run(transport="streamable-http")
