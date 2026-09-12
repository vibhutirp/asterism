"""Run the DM-only Slack Socket Mode listener.

Usage (from the repo root, with SLACK_BOT_TOKEN and SLACK_APP_TOKEN set):

    python -m backend.scripts.run_slack
"""
from __future__ import annotations

import sys

from backend.app.config import get_settings
from backend.app.dependencies import get_memory_engine
from backend.app.slack_adapter import create_slack_app


def main() -> None:
    settings = get_settings()
    if not settings.slack_bot_token or not settings.slack_app_token:
        print("SLACK_BOT_TOKEN and SLACK_APP_TOKEN must both be set (environment or .env).", file=sys.stderr)
        raise SystemExit(2)

    from slack_bolt.adapter.socket_mode import SocketModeHandler

    app = create_slack_app(get_memory_engine(), settings.slack_bot_token)
    print("Starting Slack Socket Mode listener (DM-only). Ctrl+C to stop.")
    SocketModeHandler(app, settings.slack_app_token).start()


if __name__ == "__main__":
    main()
