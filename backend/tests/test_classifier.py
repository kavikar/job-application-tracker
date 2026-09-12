from app.classifier import classify
from app.statuses import Status


def test_classifies_application_received():
    result = classify(
        subject="Thank you for applying to Acme",
        body="We have received your application for the SDET role.",
        sender="careers@acme.com",
    )
    assert result == Status.APPLICATION_RECEIVED


def test_classifies_interview_invite():
    result = classify(
        subject="Let's schedule an interview",
        body="We would like to schedule a call to discuss next steps.",
        sender="recruiting@acme.com",
    )
    assert result == Status.INTERVIEW_INVITE


def test_classifies_rejection():
    result = classify(
        subject="Update on your application",
        body="Unfortunately, we have decided to move forward with other candidates.",
        sender="careers@acme.com",
    )
    assert result == Status.REJECTED


def test_classifies_offer():
    result = classify(
        subject="Job offer from Acme",
        body="We are pleased to offer you the position of SDET.",
        sender="hr@acme.com",
    )
    assert result == Status.OFFER


def test_returns_none_for_unrelated_email():
    result = classify(
        subject="Your Amazon order has shipped",
        body="Track your package here.",
        sender="shipment@amazon.com",
    )
    assert result is None


def test_is_case_insensitive():
    result = classify(
        subject="UNFORTUNATELY",
        body="WE HAVE DECIDED TO MOVE FORWARD WITH OTHER CANDIDATES.",
        sender="careers@acme.com",
    )
    assert result == Status.REJECTED


def test_post_interview_rejection_is_classified_as_rejected_not_interview():
    # The adversarial case the priority ordering exists for: a real
    # rejection email that also thanks you for having interviewed.
    result = classify(
        subject="Your interview with Acme",
        body=(
            "Thank you for taking the time to interview with our team. "
            "Unfortunately, we will not be moving forward with your candidacy "
            "at this time."
        ),
        sender="careers@acme.com",
    )
    assert result == Status.REJECTED


def test_offer_after_final_interview_is_classified_as_offer_not_interview():
    result = classify(
        subject="Great news!",
        body="After your final interview, we are pleased to offer you the position.",
        sender="hr@acme.com",
    )
    assert result == Status.OFFER


def test_rejection_containing_thank_you_for_your_interest_is_rejected_not_received():
    # Pattern found checking real LinkedIn job-application-rejection
    # emails: the subject line ("Your application to <role> at <company>")
    # is identical to LinkedIn's application-submitted notification, and
    # the body opens with "thank you for your interest" (an
    # application_received keyword) immediately before the actual
    # rejection sentence. Without REJECTED being checked first, this
    # would be misclassified as application_received.
    result = classify(
        subject="Your application to QA Engineer at Acme",
        body=(
            "Thank you for your interest in the QA Engineer position at Acme. "
            "Unfortunately, we will not be moving forward with your application, "
            "but we appreciate your time and interest in Acme."
        ),
        sender="jobs-noreply@linkedin.com",
    )
    assert result == Status.REJECTED
