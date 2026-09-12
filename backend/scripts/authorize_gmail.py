"""One-time script: run this LOCALLY on your own machine (never in CI,
never on a server) to get a Gmail refresh token for the backend's
ingestion. It needs a real browser to complete the OAuth consent
screen, which is why it can't run inside the deployed backend or a
CI job.

Prerequisites -- see backend/README.md's "Gmail OAuth setup" section
for the full walkthrough of creating these in Google Cloud Console:
  1. A Google Cloud project with the Gmail API enabled.
  2. An OAuth client of type "Desktop app", with the consent screen's
     publishing status set to Production (NOT Testing -- Testing
     mode's refresh tokens expire after 7 days, which would silently
     break the cron job every week; see DESIGN.md).
  3. That client's Client ID and Client Secret.

Run:
    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... python scripts/authorize_gmail.py

A browser window opens for you to sign in and consent. Because the
app is unverified (expected and fine for a single-user tool -- see
DESIGN.md), you'll see an "unverified app" warning; click
Advanced -> "Go to <app name> (unsafe)" to proceed, since you are the
app's own developer and only user. The script then prints a refresh
token: store it as GOOGLE_REFRESH_TOKEN in your deployment secrets
(GitHub Actions secret for the cron job, Render env var for the
backend). You should not need to run this again unless the token is
revoked.
"""

import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from app.gmail_client import GMAIL_READONLY_SCOPE


def main() -> None:
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print(
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your environment "
            "before running this script (from your Google Cloud OAuth client).",
            file=sys.stderr,
        )
        sys.exit(1)

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, scopes=[GMAIL_READONLY_SCOPE])
    credentials = flow.run_local_server(port=0)

    print("\nSuccess. Store this as GOOGLE_REFRESH_TOKEN in your secrets:\n")
    print(credentials.refresh_token)


if __name__ == "__main__":
    main()
