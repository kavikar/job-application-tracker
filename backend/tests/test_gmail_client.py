from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.gmail_client import extract_text


def test_prefers_plain_text_when_substantial():
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText("We have received your application for the SDET role.", "plain"))
    msg.attach(MIMEText("<p>We have received your application for the SDET role.</p>", "html"))

    assert "received your application" in extract_text(msg)


def test_falls_back_to_html_when_plain_text_is_effectively_empty():
    # The exact real-world shape found checking a real LinkedIn
    # rejection email during Phase 3 validation: the plain-text part
    # decodes to near-nothing (just footer boilerplate), while the
    # actual message text -- including the rejection sentence -- only
    # exists in the HTML part.
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText("Unsubscribe | Help", "plain"))
    msg.attach(
        MIMEText(
            "<html><body><style>.x{color:red}</style>"
            "<p>Unfortunately, we will not be moving forward with your application.</p>"
            "</body></html>",
            "html",
        )
    )

    result = extract_text(msg)
    assert "unfortunately" in result.lower()
    assert "will not be moving forward" in result.lower()
    assert "<p>" not in result  # tags stripped
    assert "color:red" not in result  # style block stripped, not just tags


def test_non_multipart_plain_message():
    msg = MIMEText("Thank you for applying to Acme.", "plain")
    assert "Thank you for applying" in extract_text(msg)


def test_non_multipart_html_only_message():
    msg = MIMEText("<p>Thank you for applying to Acme.</p>", "html")
    assert extract_text(msg).strip() == "Thank you for applying to Acme."
