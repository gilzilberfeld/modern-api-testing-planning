import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient
from jsonschema import validate, ValidationError
from C04_Test_Design.gateway import app, CAT_API_URL

client = TestClient(app)

# THE CONTRACT: This is what our documentation (and planning) says the API should return.
# We set 'additionalProperties' to False to catch "Ghost Fields".
STRICT_SAFE_VOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "message": {"type": "string"}
    },
    "required": ["id", "message"],
    "additionalProperties": False
}

@respx.mock
def test_strict_schema_success():
    clean_response = {"id": 100, "message": "SUCCESS"}
    respx.post(CAT_API_URL).mock(return_value=Response(201, json=clean_response))

    payload = {"image_id": "cat1", "sub_id": "user1", "value": 5}
    response = client.post("/safe-vote", json=payload)

    validate(instance=response.json(), schema=STRICT_SAFE_VOTE_SCHEMA)

@respx.mock
def test_downstream_drift_detection():
    # The downstream Cat API (simulated) has been upgraded.
    # It now returns extra fields we never asked for and didn't plan to support.
    ai_drifted_response = {
        "id": 123,
        "message": "SUCCESS",
        "ai_sentiment_score": 0.98,  # GHOST FIELD
        "internal_model_ref": "gpt-4-turbo"  # GHOST FIELD
    }

    respx.post(CAT_API_URL).mock(return_value=Response(201, json=ai_drifted_response))

    payload = {"image_id": "cat1", "sub_id": "user1", "value": 5}
    response = client.post("/safe-vote", json=payload)

    # 1. THE "MIRAGE": A standard functional test passes!
    assert response.status_code == 201
    assert response.json()["message"] == "SUCCESS"

    # 2. THE REALITY: Our Strategy-Based Schema Check
    # This will raise a ValidationError because of the extra fields.
    validate(instance=response.json(), schema=STRICT_SAFE_VOTE_SCHEMA)


