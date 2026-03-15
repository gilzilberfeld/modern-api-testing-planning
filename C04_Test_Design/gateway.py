from fastapi import FastAPI, HTTPException, status
import httpx
import uvicorn
from pydantic import BaseModel, Field

app = FastAPI(title="SafeVote Gateway")

CAT_API_URL = "https://api.thecatapi.com/v1/votes"
CAT_API_KEY = "DEMO-API-KEY"  # Placeholder


class VoteRequest(BaseModel):
    image_id: str = Field(..., example="asdf")
    sub_id: str = Field(..., example="my-user-123")
    value: int = Field(..., description="The value of the vote (1-10)")


@app.post("/safe-vote", status_code=status.HTTP_201_CREATED)
async def create_safe_vote(vote: VoteRequest):

    if not (1 <= vote.value <= 10):
        raise HTTPException(
            status_code=400,
            detail="Sentiment Value must be between 1 and 10"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CAT_API_URL,
                headers={"x-api-key": CAT_API_KEY},
                json={
                    "image_id": vote.image_id,
                    "sub_id": vote.sub_id,
                    "value": vote.value
                },
                timeout=5.0
            )

            # Handle Downstream Errors
            if response.status_code >= 500:
                raise HTTPException(
                    status_code=502,
                    detail="Upstream Cat API is currently unavailable"
                )

            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Upstream error: {response.text}"
                )

            return response.json()

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Connectivity failure: Unable to reach voting service"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Upstream request timed out"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)