from tests.helpers import insert_application


def test_create_and_list_target_company(client):
    response = client.post(
        "/target-companies",
        json={"company": "Toast", "tier": "A", "category": "Restaurant-tech & POS"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["company"] == "Toast"
    assert body["tier"] == "A"
    assert body["already_applied"] is False

    listed = client.get("/target-companies").json()
    assert len(listed) == 1
    assert listed[0]["company"] == "Toast"


def test_create_target_company_rejects_invalid_tier(client):
    response = client.post("/target-companies", json={"company": "Toast", "tier": "Z"})
    assert response.status_code == 422


def test_create_target_company_rejects_empty_company(client):
    response = client.post("/target-companies", json={"company": "", "tier": "A"})
    assert response.status_code == 422


def test_list_target_companies_ordered_by_tier_then_insertion(client):
    client.post("/target-companies", json={"company": "Datadog", "tier": "B"})
    client.post("/target-companies", json={"company": "Toast", "tier": "A"})
    client.post("/target-companies", json={"company": "OpenAI", "tier": "D"})
    client.post("/target-companies", json={"company": "Olo", "tier": "A"})

    companies = [row["company"] for row in client.get("/target-companies").json()]
    assert companies == ["Toast", "Olo", "Datadog", "OpenAI"]


def test_already_applied_is_true_for_exact_match(client, db_session):
    insert_application(db_session, company="Toast", role="SDET")
    response = client.post("/target-companies", json={"company": "Toast", "tier": "A"})
    assert response.json()["already_applied"] is True


def test_already_applied_matches_case_insensitive_substring(client, db_session):
    # Same heuristic as the Phase 3 entity matcher, and the same
    # reason: a hand-typed target list won't spell a company exactly
    # the way it got logged as an application.
    insert_application(db_session, company="PAR Technology Corp", role="SDET")
    response = client.post("/target-companies", json={"company": "par technology", "tier": "A"})
    assert response.json()["already_applied"] is True


def test_already_applied_does_not_false_positive_on_short_name_inside_a_longer_word(
    client, db_session
):
    # Real bug found seeding the actual target list: "Olo" (3 chars)
    # matched as a substring of "techn-OLO-gy" inside "R3 Technology
    # Inc". A false "already applied" is worse here than in the Gmail
    # matcher -- it could make you skip a company you should apply to.
    insert_application(db_session, company="R3 Technology Inc", role="SDET")
    response = client.post("/target-companies", json={"company": "Olo", "tier": "A"})
    assert response.json()["already_applied"] is False


def test_already_applied_still_matches_short_name_exactly(client, db_session):
    insert_application(db_session, company="Olo", role="SDET")
    response = client.post("/target-companies", json={"company": "Olo", "tier": "A"})
    assert response.json()["already_applied"] is True


def test_already_applied_false_when_no_application_matches(client, db_session):
    insert_application(db_session, company="Acme", role="SDET")
    response = client.post("/target-companies", json={"company": "Toast", "tier": "A"})
    assert response.json()["already_applied"] is False


def test_list_target_companies_reflects_already_applied(client, db_session):
    client.post("/target-companies", json={"company": "Toast", "tier": "A"})
    insert_application(db_session, company="Toast", role="SDET")

    listed = client.get("/target-companies").json()
    assert listed[0]["already_applied"] is True


def test_delete_target_company(client):
    created = client.post("/target-companies", json={"company": "Toast", "tier": "A"}).json()

    response = client.delete(f"/target-companies/{created['id']}")
    assert response.status_code == 204
    assert client.get("/target-companies").json() == []


def test_delete_nonexistent_target_company_returns_404(client):
    response = client.delete("/target-companies/999999")
    assert response.status_code == 404
