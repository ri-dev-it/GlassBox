from io import BytesIO


def _token(client):
    response = client.post("/api/auth/register", json={
        "full_name": "Document Test", "email": "document@example.com", "password": "strong-password-123",
    })
    return {"Authorization": f"Bearer {response.get_json()['token']}"}


def test_authenticated_document_upload_persists_record(client, app, tmp_path):
    app.config["DOCUMENT_UPLOAD_DIR"] = str(tmp_path / "private_uploads")
    headers = _token(client)
    response = client.post("/api/documents", headers=headers, data={
        "documentType": "PAN_CARD", "file": (BytesIO(b"sample pdf document"), "pan.pdf", "application/pdf"),
    })
    assert response.status_code == 201
    body = response.get_json()
    assert body["success"] is True
    assert body["document"]["filename"] == "pan.pdf"
    assert body["document"]["status"] in {"VERIFIED", "NEEDS_REVIEW"}
    pending = client.get("/api/documents/pending", headers=headers)
    assert pending.status_code == 200
    assert len(pending.get_json()["documents"]) == 1
    assert list((tmp_path / "private_uploads").rglob("*.pdf"))


def test_document_upload_rejects_missing_and_unsupported_files(client):
    headers = _token(client)
    missing = client.post("/api/documents", headers=headers, data={"documentType": "PAN_CARD"})
    assert missing.status_code == 400
    assert missing.get_json()["message"] == "Please select a document."
    unsupported = client.post("/api/documents", headers=headers, data={
        "documentType": "PAN_CARD", "file": (BytesIO(b"not allowed"), "script.js", "application/javascript"),
    })
    assert unsupported.status_code == 400
    assert "Only PDF" in unsupported.get_json()["message"]


def test_document_upload_accepts_png_and_rejects_oversized_file(client, app, tmp_path):
    app.config["DOCUMENT_UPLOAD_DIR"] = str(tmp_path / "private_uploads")
    app.config["MAX_DOCUMENT_SIZE_BYTES"] = 4
    headers = _token(client)
    png = client.post("/api/documents", headers=headers, data={
        "documentType": "ADDRESS_PROOF", "file": (BytesIO(b"png"), "address.png", "image/png"),
    })
    assert png.status_code == 201
    oversized = client.post("/api/documents", headers=headers, data={
        "documentType": "BANK_STATEMENT", "file": (BytesIO(b"12345"), "statement.pdf", "application/pdf"),
    })
    assert oversized.status_code == 400
    assert "size exceeds" in oversized.get_json()["message"]
