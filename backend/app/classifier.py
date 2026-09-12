"""Pure, no-I/O email classification. No Gmail import here on purpose
-- see DESIGN.md's tradeoff #3: this is a deterministic function
tested with a fixed input/output table, not live inbox data.

These are starter rules based on common ATS phrasing (Greenhouse,
Lever, Workday, generic HR templates), not tuned against a real
inbox yet -- that correction pass happens next, against real subject
lines, and will mean editing the keyword lists below, not the
priority-ordering logic.
"""

from app.statuses import Status

# Checked in this order, first match wins. Order matters more than
# any individual keyword: a post-interview rejection email routinely
# contains "thank you for interviewing with us" right next to
# "unfortunately, we will not be moving forward" -- if INTERVIEW_INVITE
# were checked before REJECTED, that email would be misfiled as a new
# interview invite instead of a rejection. Decisive/terminal signals
# (rejected, offer) are checked before the more common, weaker-signal
# categories (interview_invite, then application_received last, since
# "thank you for applying" boilerplate can show up as a fragment in
# other email types too).
REJECTED_KEYWORDS = [
    "unfortunately",
    "will not be moving forward",
    "have decided not to move forward",
    "decided to move forward with other candidates",
    "not moving forward with your candidacy",
    "pursue other candidates",
    "candidates whose qualifications",
    "not been selected",
    "wish you the best in your job search",
    "wish you the best in your future endeavors",
    "position has been filled",
]

OFFER_KEYWORDS = [
    "pleased to offer",
    "excited to offer",
    "offer of employment",
    "extend an offer",
    "job offer",
    "offer letter",
]

INTERVIEW_KEYWORDS = [
    "schedule an interview",
    "schedule a call",
    "schedule a time",
    "phone screen",
    "would like to interview",
    "interview invitation",
    "next steps in our process",
    "book a time",
    "set up a call",
    "technical interview",
    "onsite interview",
]

APPLICATION_RECEIVED_KEYWORDS = [
    "we have received your application",
    "we've received your application",
    "thank you for applying",
    "thank you for your interest in",
    "your application has been submitted",
    "your application has been received",
    "we received your application",
]

_RULES_IN_PRIORITY_ORDER = [
    (Status.REJECTED, REJECTED_KEYWORDS),
    (Status.OFFER, OFFER_KEYWORDS),
    (Status.INTERVIEW_INVITE, INTERVIEW_KEYWORDS),
    (Status.APPLICATION_RECEIVED, APPLICATION_RECEIVED_KEYWORDS),
]


def classify(subject: str, body: str, sender: str) -> Status | None:
    """sender is accepted (per the original spec: keyword/sender
    matching) but not yet used by any rule below -- reserved for the
    inbox-tuning pass, e.g. treating known ATS notification domains as
    a confidence signal. Kept in the signature now rather than added
    later so tuning doesn't require an API change."""
    text_blob = f"{subject}\n{body}".lower()
    for status, keywords in _RULES_IN_PRIORITY_ORDER:
        if any(keyword in text_blob for keyword in keywords):
            return status
    return None
