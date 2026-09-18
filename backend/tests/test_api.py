from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_seed_and_patient_lifecycle():
    # 1. Seed demo patient
    seed_res = client.post("/api/patients/seed-demo")
    assert seed_res.status_code == 200
    patient = seed_res.json()
    assert patient["name"] == "Sarah Jenkins"
    assert patient["patient_reference"] == "PAT-2026-0814"
    patient_id = patient["patient_id"]

    # 2. Get patient details
    p_res = client.get(f"/api/patients/{patient_id}")
    assert p_res.status_code == 200
    assert p_res.json()["document_count"] == 5

    # 3. Get timeline
    timeline_res = client.get(f"/api/patients/{patient_id}/timeline")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert timeline["total_events"] > 5
    assert len(timeline["timeline_events"]) > 5

    first_ev = timeline["timeline_events"][0]
    assert first_ev["supporting_text"] is not None
    assert first_ev["source_document_name"] is not None

    # 4. Get event detail
    ev_id = first_ev["event_id"]
    ev_res = client.get(f"/api/events/{ev_id}")
    assert ev_res.status_code == 200
    assert ev_res.json()["event_id"] == ev_id

    # 5. Get intelligence summary
    summary_res = client.get(f"/api/patients/{patient_id}/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["changes_count"] >= 1
    assert summary["conflicts_count"] >= 1
    assert summary["gaps_count"] >= 1
    assert summary["relationships_count"] >= 1

    # 6. Get journey graph
    journey_res = client.get(f"/api/patients/{patient_id}/journey")
    assert journey_res.status_code == 200
    journey = journey_res.json()
    assert len(journey["nodes"]) > 0
    assert len(journey["edges"]) > 0

    # 7. Test QA
    qa_res = client.post(f"/api/patients/{patient_id}/ask", json={"question": "What is the patient's HbA1c level?"})
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["has_sufficient_evidence"] is True
    assert len(qa_data["citations"]) > 0

    # 8. Test Document View and Download endpoints for all documents
    docs_res = client.get(f"/api/patients/{patient_id}/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) == 5

    for doc in docs:
        doc_id = doc["document_id"]
        orig_fn = doc["original_filename"]

        # View endpoint (inline)
        v_res = client.get(f"/api/documents/{doc_id}/view")
        assert v_res.status_code == 200
        assert v_res.headers["content-type"] == "application/pdf"
        assert f'inline; filename="{orig_fn}"' in v_res.headers["content-disposition"]
        assert len(v_res.content) > 0

        # Download endpoint (attachment)
        d_res = client.get(f"/api/documents/{doc_id}/download")
        assert d_res.status_code == 200
        assert d_res.headers["content-type"] == "application/pdf"
        assert f'attachment; filename="{orig_fn}"' in d_res.headers["content-disposition"]
        assert len(d_res.content) > 0

        # Legacy /file endpoint with disposition param
        f_inline = client.get(f"/api/documents/{doc_id}/file?disposition=inline")
        assert f_inline.status_code == 200
        assert "inline" in f_inline.headers["content-disposition"]

        f_att = client.get(f"/api/documents/{doc_id}/file")
        assert f_att.status_code == 200
        assert "attachment" in f_att.headers["content-disposition"]

    # 9. Test 404 error handling on missing documents
    bad_view = client.get("/api/documents/invalid-uuid-0000/view")
    assert bad_view.status_code == 404
    assert "not found" in bad_view.json()["detail"].lower()

    bad_dl = client.get("/api/documents/invalid-uuid-0000/download")
    assert bad_dl.status_code == 404
    assert "not found" in bad_dl.json()["detail"].lower()
