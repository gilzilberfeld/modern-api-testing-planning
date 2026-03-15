import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient

from C04_Test_Design.gateway import CAT_API_URL, app

client = TestClient(app)


@respx.template
def mock_cat_api(route: respx.Route):
    """Template for mocking the Cat API endpoint"""
    return route.post(CAT_API_URL)


@respx.mock
def test_valid_input_successful_vote():
    cat_api_route = (respx.post(CAT_API_URL)
                     .mock(return_value=Response(201,
                         json={"id": 100, "message": "SUCCESS"})))

    payload = {"image_id": "cat1", "sub_id": "user1", "value": 5}
    response = client.post("/safe-vote", json=payload)

    assert response.status_code == 201
    assert response.json()["message"] == "SUCCESS"
    assert cat_api_route.called


@respx.mock
def test_invalid_input_return_error():
    cat_api_route = (respx.post(CAT_API_URL)
                     .mock(return_value=Response(201)))

    payload = {"image_id": "cat1", "sub_id": "user1", "value": 11}  # Out of range
    response = client.post("/safe-vote", json=payload)

    assert response.status_code == 400
    assert "Sentiment Value must be between 1 and 10" in response.json()["detail"]
    assert not cat_api_route.called


@respx.mock
def test_connectivity_failure_return_error():
    respx.post(CAT_API_URL).side_effect = Exception("Connection Refused")

    payload = {"image_id": "cat1", "sub_id": "user1", "value": 5}
    response = client.post("/safe-vote", json=payload)

    assert response.status_code in [503, 500]
    assert "failure" in response.json()["detail"].lower()


@respx.mock
def test_catapi_return_error_translate():
    respx.post(CAT_API_URL).mock(return_value=Response(500))

    payload = {"image_id": "cat1", "sub_id": "user1", "value": 5}
    response = client.post("/safe-vote", json=payload)

    assert response.status_code == 502
    assert "Upstream Cat API is currently unavailable" in response.json()["detail"]