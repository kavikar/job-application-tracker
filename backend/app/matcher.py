"""Pure, no-I/O entity resolution: which tracked application does an
email belong to? Separate module from classifier.py on purpose -- see
DESIGN.md: "what happened" and "which application" fail in different
ways and deserve separate test tables.

ApplicationRecord is a plain dataclass, not the SQLAlchemy row from
app.repositories -- this module has no DB import, so it takes whatever
shape of data the caller has already fetched.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ApplicationRecord:
    id: int
    company: str
    job_url: str | None = None


def _extract_domain(value: str) -> str | None:
    """Works for either an email sender ("Name <a@acme.com>") or a URL
    (https://acme.com/careers/123), since both cases just need "the
    domain part" pulled out."""
    if "@" in value:
        match = re.search(r"@([\w.-]+)", value)
        domain = match.group(1) if match else None
    else:
        netloc = urlparse(value if "//" in value else f"//{value}").netloc
        domain = netloc or None
    if not domain:
        return None
    domain = domain.lower()
    return domain.removeprefix("www.")


def match_application(
    subject: str, sender: str, body: str, applications: list[ApplicationRecord]
) -> ApplicationRecord | None:
    """A false match is worse than no match: silently attributing an
    email to the wrong application corrupts that application's status
    history, while a non-match just lands the email in the
    unmatched-events review queue (see DESIGN.md) for a human to link
    by hand. So every ambiguous case below returns None rather than
    guessing.
    """
    text_blob = f"{subject}\n{body}".lower()
    name_matches = [a for a in applications if a.company.lower() in text_blob]
    if len(name_matches) == 1:
        return name_matches[0]
    if len(name_matches) > 1:
        return None  # ambiguous: more than one tracked company mentioned

    # Fallback for emails that never mention the company by name (a
    # bare "Interview Confirmation" subject sent directly from the
    # company's own domain, not through a third-party ATS).
    sender_domain = _extract_domain(sender)
    if sender_domain:
        domain_matches = [
            a
            for a in applications
            if a.job_url and _extract_domain(a.job_url) == sender_domain
        ]
        if len(domain_matches) == 1:
            return domain_matches[0]

    return None
