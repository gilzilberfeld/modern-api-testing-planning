import pytest
import asyncio
import httpx
from C04_Test_Design.gateway import app, CAT_API_KEY

@pytest.mark.asyncio
async def test_concurrent_calls_all_updates_arrive():
    """
    We fire multiple concurrent POST requests. For every 201 Created
    we receive, we expect the total count of votes to have increased by exactly 1.
    If the API returns 201 but the GET count doesn't move, we have a Race Condition.
    """
    base_url = "http://localhost:8000"
    sub_id = f"target-{int(asyncio.get_event_loop().time())}"
    image_id = "cat_123"

    async with httpx.AsyncClient() as client:
        # Get initial count
        initial_res = await client.get(
            f"https://api.thecatapi.com/v1/votes?sub_id={sub_id}",
            headers={"x-api-key": CAT_API_KEY}
        )
        initial_count = len(initial_res.json())

        # Fire 5 concurrent POST requests to our 'safe-vote' gateway.
        payload = {"image_id": image_id, "sub_id": sub_id, "value": 5}
        tasks = [client.post(f"{base_url}/safe-vote", json=payload) for _ in range(5)]

        responses = await asyncio.gather(*tasks)

        # Count how many times our API told us "Yes, I created the vote."
        success_responses = [r for r in responses if r.status_code == 201]
        reported_success_count = len(success_responses)
        print(f"API reported {reported_success_count} successful votes.")

        # We perform a GET to see the actual state of the world.
        final_res = await client.get(
            f"https://api.thecatapi.com/v1/votes?sub_id={sub_id}",
            headers={"x-api-key": CAT_API_KEY}
        )
        actual_final_count = len(final_res.json())
        actual_increment = actual_final_count - initial_count

        # Each successful POST MUST increment the GET count by exactly one.
        # If actual_increment < reported_success_count, we have a Lost Update.
        assert actual_increment == reported_success_count, \
            f"API returned {reported_success_count} successes, " \
            f"but state only incremented by {actual_increment}. Data was lost!"

        # CLEANUP: Delete the votes created
        for res in success_responses:
            vote_id = res.json().get("id")
            if vote_id:
                await client.delete(
                    f"https://api.thecatapi.com/v1/votes/{vote_id}",
                    headers={"x-api-key": CAT_API_KEY}
                )