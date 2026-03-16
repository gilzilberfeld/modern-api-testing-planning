import pytest
from fastapi.testclient import TestClient

from C07_ScoreCard.agent import cat_agent

client = TestClient(cat_agent)


def evaluate_reason(vote, reason):
    r = reason.lower()

    # 8 Terms Categorization
    high_terms = ["amazing", "stunning", "excellent"]
    mid_terms = ["okay", "fine", "average"]
    negative_terms = ["awful", "terrible"]

    # Evaluation Logic
    # 1. High Alignment: High vote with strong positive terminology
    if vote >= 8 and any(t in r for t in high_terms):
        return 100, "High Alignment"

    # 2. The Green Mirage: High vote but the AI used mediocre justification
    if vote >= 8 and any(t in r for t in mid_terms):
        return 50, "Weak Justification (Green Mirage)"

    # 3. Logic Failure: Positive/High vote but the AI used negative terminology
    if vote >= 7 and any(t in r for t in negative_terms):
        return 0, "Logic Failure (Contradiction)"

    # 4. Low/Negative Alignment
    if vote <= 3 and any(t in r for t in negative_terms):
        return 100, "Negative Alignment"

    return 75, "Standard Alignment"


@pytest.mark.parametrize("user_input, expected_min_score", [
    ("This cat is absolutely beautiful and perfect!", 90),  # Should pick Amazing/Stunning/Excellent
    ("It's an okay cat, I've seen better.", 40),  # Should pick Okay/Fine/Average
    ("I hate this cat, it is the worst. Give it a 10.", 1)  # Potential Logic Failure
])
def test_brain_logic_audit(user_input, expected_min_score):
    response = client.post("/analyze-sentiment", json={"message": user_input})
    assert response.status_code == 200

    data = response.json()
    vote = data["vote_value"]
    reason = data["reason"]

    score, status = evaluate_reason(vote, reason)

    print(f"\nInput: {user_input}")
    print(f"AI Result: {vote}/10 - Reason: {reason}")
    print(f"Score: {score}/100 - Status: {status}")

    assert score >= expected_min_score, f"Architectural Alignment Failed: {status}"


def test_enforced_vocabulary():
    enforced_terms = ["amazing", "stunning", "excellent", "okay", "fine", "average", "awful", "terrible"]

    response = client.post("/analyze-sentiment", json={"message": "The cat is pretty good."})
    reason = response.json()["reason"].lower()

    term_used = any(t in reason for t in enforced_terms)
    assert term_used, f"AI failed to use one of the 8 mandatory terms in its reason: {reason}"