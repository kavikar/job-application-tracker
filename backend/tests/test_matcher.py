from app.matcher import ApplicationRecord, match_application

ACME = ApplicationRecord(id=1, company="Acme", job_url="https://acme.com/careers/123")
GLOBEX = ApplicationRecord(id=2, company="Globex", job_url="https://jobs.globex.io/456")


def test_matches_by_company_name_in_subject():
    result = match_application(
        subject="Your application to Acme",
        sender="notifications@greenhouse.io",  # third-party ATS, not acme.com
        body="",
        applications=[ACME, GLOBEX],
    )
    assert result == ACME


def test_matches_by_company_name_in_body():
    result = match_application(
        subject="Interview Confirmation",
        sender="notifications@lever.co",
        body="We're looking forward to your interview for the Acme SDET role.",
        applications=[ACME, GLOBEX],
    )
    assert result == ACME


def test_ambiguous_when_multiple_companies_mentioned_returns_none():
    # e.g. a newsletter or a forwarded thread mentioning both -- do not guess.
    result = match_application(
        subject="Acme vs Globex: which pays more?",
        sender="newsletter@example.com",
        body="",
        applications=[ACME, GLOBEX],
    )
    assert result is None


def test_no_name_match_falls_back_to_sender_domain():
    result = match_application(
        subject="Interview Confirmation",  # no company name at all
        sender="hr@acme.com",
        body="See you Thursday.",
        applications=[ACME, GLOBEX],
    )
    assert result == ACME


def test_no_match_at_all_returns_none():
    result = match_application(
        subject="Your Amazon order has shipped",
        sender="shipment@amazon.com",
        body="Track your package here.",
        applications=[ACME, GLOBEX],
    )
    assert result is None


def test_empty_applications_list_returns_none():
    result = match_application(
        subject="Your application to Acme",
        sender="careers@acme.com",
        body="",
        applications=[],
    )
    assert result is None


def test_third_party_ats_sender_domain_does_not_false_match_on_domain():
    # Sender domain fallback must not fire just because it's some
    # unrelated ATS platform's domain -- only a real job_url domain match counts.
    result = match_application(
        subject="Interview Confirmation",  # no company name
        sender="notifications@greenhouse.io",
        body="See you Thursday.",
        applications=[ACME, GLOBEX],
    )
    assert result is None
