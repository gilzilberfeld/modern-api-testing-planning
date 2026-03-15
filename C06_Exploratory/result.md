Based on the prompt above, here are the charters for the Safe-Vote ecosystem:

## Charter #1: The Latency Ripple

- Target: The safe-vote timeout handling logic.

- Resources: Postman, a network throttling tool (like Charles Proxy or Chrome DevTools).

- To Discover: How the gateway behaves when the Cat API is "slow but not dead" (e.g., a 4.9s response time when our timeout is 5s). Does the gateway leak internal stack traces or hang connections when multiple slow requests pile up?

## Charter #2: Metadata Poisoning & Sentiment Drift

- Target: The ```sub_id``` and ```image_id``` input fields.

- Resources: Burp Suite or Manual Input Fuzzing.

- To Discover: If we can "poison" the sentiment logic by using special characters, emojis, or SQL injection strings in the ```sub_id```. Does the Cat API's analysis engine try to "execute" or "interpret" this metadata in a way that creates unexpected tags or errors?

## Charter #3: The "Zombie Vote" State

- Target: Vote persistence and deletion lifecycle.

- Resources: Direct access to Cat API ```GET /votes``` vs. Our API logs.

- To Discover: If a vote can exist in a "Zombie State"—where our gateway returns an error (like a timeout) but the Cat API actually processed the vote anyway. We want to find cases where our "Success" report is out of sync with the downstream reality.

## Charter #4: The Identity Mirror

- Target: Authentication and Header propagation.

- Resources: Custom header manipulation in Python/Requests.

- To Discover: What happens if we pass a valid Cat API key but an invalid ```sub_id```, or vice versa? Does our gateway's error mapping hide security vulnerabilities (like PII leakage) that occur when the downstream API rejects a request?

## Charter #5: The Recursive Loop

- Target: Large volume bursts on single entities.

- Resources: The Concurrency Test script (C05).

- To Discover: Beyond just the "Lost Update" situation, how does the system recover after a collision? If we break the increment logic once, does the system stay "corrupted," or does a subsequent "GET" trigger a cache refresh that fixes the state? (Observing the "Self-Healing" capability of the logic).