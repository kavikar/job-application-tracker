from app.gmail_client import RawEmail


class FakeGmailClient:
    """Stands in for GmailClient in tests -- no network call, no real
    OAuth credentials needed. Duck-types the one method run_ingestion
    actually calls."""

    def __init__(self, messages: list[RawEmail]):
        self._messages = messages
        self.queries_received: list[str] = []

    def list_recent_messages(self, query: str) -> list[RawEmail]:
        self.queries_received.append(query)
        return self._messages
