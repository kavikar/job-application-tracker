from app.gmail_client import RawEmail, get_gmail_client
from app.main import app
from tests.fakes import FakeGmailClient


def test_post_ingest_uses_injected_gmail_client_not_a_live_call(client):
    gmail = FakeGmailClient(
        [
            RawEmail(
                message_id="msg-endpoint-1",
                subject="Thank you for applying",
                sender="careers@acme.com",
                body="We have received your application.",
            )
        ]
    )
    app.dependency_overrides[get_gmail_client] = lambda: gmail

    response = client.post("/ingest")

    assert response.status_code == 200
    assert response.json() == {
        "processed": 1,
        "ingested": 1,
        "unmatched": 1,  # no applications tracked in this test
        "skipped_no_status": 0,
    }
