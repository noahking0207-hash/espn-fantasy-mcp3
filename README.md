# ESPN Fantasy MCP Connector

A read-only MCP server for pulling ESPN Fantasy data into a ChatGPT plugin.

## What it exposes

- `get_league`: settings and league configuration
- `get_teams_and_rosters`: every team and roster
- `get_matchups`: matchup and scoring context
- `get_standings`: standings
- `get_free_agents`: waiver/free-agent pool
- `get_player_pool`: broader active player pool
- `get_transactions`: recent transactions
- `get_draft`: draft detail
- `get_status`: current league/week status

## Private ESPN leagues

ESPN's unofficial Fantasy API commonly requires the `espn_s2` and `SWID` cookies for private leagues. Put them in environment variables; never commit them to source control.

## Run locally

```bash
cp .env.example .env
# Fill in .env
pip install -r requirements.txt
set -a && source .env && set +a
python server.py
```

The MCP server listens on the default FastMCP streamable HTTP endpoint.

## Deploy

The included Dockerfile is suitable for a container host such as Railway, Render, Fly.io, or another HTTPS-capable service. Set the environment variables from `.env.example` in the host's secret/environment configuration.

The final ChatGPT plugin needs the service's HTTPS MCP URL in its `mcp.json`, for example:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "espn-fantasy": {
      "type": "streamable-http",
      "url": "https://YOUR-HOST.example/mcp"
    }
  }
}
```

This server is intentionally read-only. It does not expose ESPN mutation endpoints for trades, add/drop, or lineup changes.
