import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal, init_db
from app.demo_data.synthetic_dataset import seed_demo_patient_in_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()
    db = SessionLocal()
    seed_demo_patient_in_db(db)
    db.close()


def test_get_patient_milestones():
    patients = client.get("/api/patients").json()
    assert len(patients) > 0
    patient_id = patients[0]["patient_id"]

    res = client.get(f"/api/patients/{patient_id}/milestones")
    assert res.status_code == 200
    milestones = res.json()
    assert len(milestones) >= 5
    for m in milestones:
        assert "title" in m
        assert "milestone_type" in m
        assert "document_name" in m
        assert "source_page" in m
        assert "supporting_text" in m


def test_get_patient_action_chains():
    patients = client.get("/api/patients").json()
    patient_id = patients[0]["patient_id"]

    res = client.get(f"/api/patients/{patient_id}/chains")
    assert res.status_code == 200
    chains = res.json()
    assert len(chains) >= 2
    titles = [c["chain_title"] for c in chains]
    assert any("Glycemic" in t for t in titles)
    assert any("Cardiorenal" in t for t in titles)
    for c in chains:
        assert len(c["nodes"]) >= 3
        for node in c["nodes"]:
            assert "description" in node
            assert "supporting_text" in node


def test_update_conflict_status_workspace():
    patients = client.get("/api/patients").json()
    patient_id = patients[0]["patient_id"]

    conflicts = client.get(f"/api/patients/{patient_id}/conflicts").json()
    assert len(conflicts) > 0
    conflict_id = conflicts[0]["conflict_id"]

    # Update to under_review
    patch_res = client.patch(
        f"/api/patients/{patient_id}/conflicts/{conflict_id}/status",
        json={"status": "under_review", "resolution_notes": "Allergy committee reviewing documentation."}
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "under_review"
    assert updated["resolution_notes"] == "Allergy committee reviewing documentation."

    # Update to resolved
    patch_res2 = client.patch(
        f"/api/patients/{patient_id}/conflicts/{conflict_id}/status",
        json={"status": "resolved", "resolution_notes": "Confirmed true Penicillin allergy from family."}
    )
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "resolved"


def test_timeline_priority_and_evidence_filters():
    patients = client.get("/api/patients").json()
    patient_id = patients[0]["patient_id"]

    # Critical priority filter
    res_crit = client.get(f"/api/patients/{patient_id}/timeline?priority=Critical")
    assert res_crit.status_code == 200
    crit_timeline = res_crit.json()
    crit_events = crit_timeline["timeline_events"]
    assert len(crit_events) > 0
    for ev in crit_events:
        assert ev["importance_priority"] == "Critical"
        assert ev["importance_reason"] is not None

    # Strong evidence filter
    res_strong = client.get(f"/api/patients/{patient_id}/timeline?evidence_level=Strong")
    assert res_strong.status_code == 200
    strong_timeline = res_strong.json()
    strong_events = strong_timeline["timeline_events"]
    assert len(strong_events) > 0
    for ev in strong_events:
        assert ev["evidence_level"] == "Strong"


def test_evidence_grounded_qa_extended_capabilities():
    patients = client.get("/api/patients").json()
    patient_id = patients[0]["patient_id"]

    # 1. Trajectory Question
    res1 = client.post(f"/api/patients/{patient_id}/ask", json={"question": "What is the trajectory of Metformin across all documents?"})
    assert res1.status_code == 200
    ans1 = res1.json()
    assert "Metformin" in ans1["answer"]
    assert len(ans1["citations"]) > 0

    # 2. Major Changes Question
    res2 = client.post(f"/api/patients/{patient_id}/ask", json={"question": "What were the major changes in treatment?"})
    assert res2.status_code == 200
    ans2 = res2.json()
    assert "Metformin" in ans2["answer"] or "Insulin" in ans2["answer"]

    # 3. Conflicts Question
    res3 = client.post(f"/api/patients/{patient_id}/ask", json={"question": "Are there any contradictions or conflicts in the records?"})
    assert res3.status_code == 200
    ans3 = res3.json()
    assert "Penicillin" in ans3["answer"] or "Allergy" in ans3["answer"]

    # 4. Gaps Question
    res4 = client.post(f"/api/patients/{patient_id}/ask", json={"question": "Are there any documentation gaps or missing intervals?"})
    assert res4.status_code == 200
    ans4 = res4.json()
    assert "gap" in ans4["answer"].lower() or "documentation" in ans4["answer"].lower()

    # 5. Unsupported Evidence Refusal Question
    res5 = client.post(f"/api/patients/{patient_id}/ask", json={"question": "Does the patient have a history of brain surgery or oncology chemotherapy?"})
    assert res5.status_code == 200
    ans5 = res5.json()
    assert ans5["has_sufficient_evidence"] is False
    assert "sufficient evidence" in ans5["answer"].lower() or "not find" in ans5["answer"].lower() or "no documentation" in ans5["answer"].lower()
