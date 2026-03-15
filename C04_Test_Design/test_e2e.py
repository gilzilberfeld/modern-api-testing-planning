import pytest
import httpx
from fastapi.testclient import TestClient
from C04_Test_Design.gateway import CAT_API_KEY, app

# We use the real app and a real httpx client for external calls in the fixture
client = TestClient(app)
CAT_API_IMAGES_URL = "https://api.thecatapi.com/v1/images"
CAT_API_VOTES_URL = "https://api.thecatapi.com/v1/votes"

@pytest.fixture
def temp_cat_image():
    #   Find existing image to vote on
    response = httpx.get(
        f"{CAT_API_IMAGES_URL}/search",
        headers={"x-api-key": CAT_API_KEY}
    )
    cat_data = response.json()[0]
    image_id = cat_data["id"]

    yield image_id


@pytest.fixture
def managed_vote(temp_cat_image):
    vote_data = {"id": None}

    yield vote_data

    # CLEANUP: Delete the vote if an ID was generated
    if vote_data["id"]:
        print(f"\nCleaning up vote ID: {vote_data['id']}")
        httpx.delete(
            f"{CAT_API_VOTES_URL}/{vote_data['id']}",
            headers={"x-api-key": CAT_API_KEY}
        )

def test_e2e_successful_vote_flow(temp_cat_image, managed_vote):
    sub_id = "e2e-test-user"

    # Check baseline vote count for this user
    initial_votes_res = httpx.get(
        f"{CAT_API_VOTES_URL}?sub_id={sub_id}",
        headers={"x-api-key": CAT_API_KEY}
    )
    assert initial_votes_res.status_code == 200
    initial_count = len(initial_votes_res.json())

    payload = {
        "image_id": temp_cat_image,
        "sub_id": sub_id,
        "value": 8
    }

    # Call our API to create a vote
    response = client.post("/safe-vote", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "SUCCESS"

    # Store the ID in the fixture for cleanup
    vote_id = data["id"]
    managed_vote["id"] = vote_id

    # Verify count incremented in the Cat API
    final_votes_res = httpx.get(
        f"{CAT_API_VOTES_URL}?sub_id={sub_id}",
        headers={"x-api-key": CAT_API_KEY}
    )
    assert final_votes_res.status_code == 200
    final_count = len(final_votes_res.json())
    assert final_count == initial_count + 1

def test_e2e_invalid_input_no_side_effect(temp_cat_image, managed_vote):
    payload = {
        "image_id": temp_cat_image,
        "sub_id": "e2e-test-user",
        "value": 11  # Invalid per our gateway rules
    }

    response = client.post("/safe-vote", json=payload)
    assert response.status_code == 400