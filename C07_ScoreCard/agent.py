from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="AI Sentiment Brain")

GEMINI_API_KEY = ""  # Provided by environment
MODEL_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={GEMINI_API_KEY}"


class ChatRequest(BaseModel):
    message: str


class BrainResponse(BaseModel):
    vote_value: int
    reason: str


@app.post("/analyze-sentiment", response_model=BrainResponse)
async def analyze_sentiment(request: ChatRequest):
    # We define 8 mandatory terms for the AI to choose from to describe the sentiment.
    # This limits indeterminacy and allows for structured "Logic Audits".
    system_prompt = (
        "You are a Cat API Sentiment Analyst. "
        "Task: Convert the user's chat message into a numeric vote (1-10) for the Cat API. "
        "Output ONLY a JSON object with keys 'vote_value' (number) and 'reason' (string). "
        "The 'reason' MUST include at least one of these exact terms to justify the score: "
        "Amazing, Stunning, Excellent, Okay, Fine, Average, Awful, Terrible."
    )

    payload = {
        "contents": [{
            "parts": [{"text": request.message}]
        }],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(MODEL_URL, json=payload, timeout=10.0)

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Brain unavailable")

            result = response.json()
            raw_content = result['candidates'][0]['content']['parts'][0]['text']

            import json
            ai_data = json.loads(raw_content)

            return BrainResponse(
                vote_value=ai_data.get("vote_value"),
                reason=ai_data.get("reason")
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)