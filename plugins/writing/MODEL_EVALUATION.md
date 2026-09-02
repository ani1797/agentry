# Writing agent model evaluation

Candidates: `grok-4` (xAI) and `gemini-2.5-pro` (Google), the two model
families best suited to creative and professional writing.

## Criteria

| Quality | Grok 4 | Gemini 2.5 Pro |
|---|---|---|
| Voice & personality | Distinct, opinionated, willing to take a stance | Polished, even-handed, defaults to a safe editorial tone |
| Professional/diplomatic tone | Can read as blunt or informal | Consistently measured and credible |
| Long-document structure & consistency | Good, but favors punchy, informal sections | Strong narrative and structural consistency over long documents |
| Factual grounding / hallucination avoidance | Solid, but leans toward confident phrasing | Strong; more conservative when evidence is thin |
| Best fit | Personality-driven, argumentative short/long form | Structured, accuracy-critical, professional-register writing |

## Per-agent decision

| Agent | Model | Reason |
|---|---|---|
| `inkwell` (Substack essays) | `grok-4` | Essays need a distinct, opinionated voice and willingness to take a clear stance; this is Grok's strength. |
| `signal` (LinkedIn posts) | `gemini-2.5-pro` | The agent must avoid manufactured controversy and engagement bait and stay credible and professional; Gemini's measured, diplomatic tone fits better than Grok's bluntness. |
| `wayfinder` (Diátaxis docs) | `gemini-2.5-pro` | Technical documentation depends on structural consistency and conservative, unembellished factual claims across long documents, where Gemini is stronger. |
