import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

cat_agent = FastAPI(title="AI Sentiment Brain & Voter")

# Configuration
GEMINI_API_KEY = ""  # Provided by environment
SAFE_VOTE_API_URL = "http://localhost:8000/safe-vote"
MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"

# The prompt now instructs the AI to be the data-broker.
SYSTEM_PROMPT = (
    "You are a Cat API Data Broker. "
    "Task: Convert the user's chat message into a numeric vote (1-10). "
    "Crucial: You must also return the original 'image_id' and 'sub_id' sent to you. "
    "Output ONLY a JSON object with: 'vote_value' (int), 'reason' (string), 'image_id' (string), 'sub_id' (string). "
    "The 'reason' MUST include at least one of these exact terms: "
    "Amazing, Stunning, Excellent, Okay, Fine, Average, Awful, Terrible."
)


class ChatRequest(BaseModel):
    message: str
    image_id: str = "cat_default"
    sub_id: str = "user_default"


class BrainResponse(BaseModel):
    vote_value: int
    reason: str
    image_id: str
    sub_id: str


class IntegratedResponse(BaseModel):
    ai_result: BrainResponse
    vote_status: str
    gateway_response: dict = None
    error: str = None


async def _consult_brain(request: ChatRequest) -> dict:
    """Sends the ENTIRE request to the AI for processing/passthrough."""
    prompt_with_data = (
        f"USER MESSAGE: {request.message}\n"
        f"DATA TO PASS THROUGH: image_id='{request.image_id}', sub_id='{request.sub_id}'"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(MODEL_URL, json={
            "contents": [{"parts": [{"text": prompt_with_data}]}],
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "generationConfig": {"responseMimeType": "application/json"}
        }, timeout=10.0)

        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Brain connection failed")

        result = response.json()
        raw_content = result['candidates'][0]['content']['parts'][0]['text']
        return json.loads(raw_content)


@cat_agent.post("/analyze-sentiment", response_model=BrainResponse)
async def analyze_sentiment(request: ChatRequest):
    """Used for Scorecard Audits."""
    ai_data = await _consult_brain(request)
    return BrainResponse(**ai_data)


@cat_agent.post("/chat-vote", response_model=IntegratedResponse)
async def brain_vote(request: ChatRequest):
    """
    ENDPOINT: INTEGRATED ACTION
    The AI receives the data and returns it. We use the AI's version to call the Gateway.
    """
    ai_data = await _consult_brain(request)

    # AI-Broker logic: We pull the values from the AI's response, NOT the original request
    vote_value = ai_data.get("vote_value")
    target_sub_id = ai_data.get("sub_id")
    target_image_id = ai_data.get("image_id")

    # Guardrail Check
    if not isinstance(vote_value, int) or not (1 <= vote_value <= 10):
        return IntegratedResponse(
            ai_result=ai_data,
            vote_status="REJECTED_BY_BRAIN_GUARDRAIL",
            error="AI attempted to bypass numeric limits."
        )

    # Chaining to the Safe-Vote Gateway using the AI's brokered data
    async with httpx.AsyncClient() as client:
        try:
            gateway_res = await client.post(
                SAFE_VOTE_API_URL,
                json={
                    "image_id": target_image_id,
                    "sub_id": target_sub_id,
                    "value": vote_value
                }
            )
            return IntegratedResponse(
                ai_result=ai_data,
                vote_status="SUCCESS" if gateway_res.status_code == 201 else "GATEWAY_REJECTION",
                gateway_response=gateway_res.json()
            )
        except Exception as e:
            return IntegratedResponse(
                ai_result=ai_data,
                vote_status="GATEWAY_UNAVAILABLE",
                error=str(e)
            )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(cat_agent, host="0.0.0.0", port=8001)