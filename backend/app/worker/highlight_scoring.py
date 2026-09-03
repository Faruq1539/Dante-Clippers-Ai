"""
Highlight scoring stage: chunks the transcript and asks an LLM to identify
clip-worthy moments in each chunk, with a start/end/score/reason per moment.

If the Anthropic API isn't available (no key, no billing credits, rate
limit, network issue, etc.), this falls back to a simple heuristic scorer
so the rest of the pipeline -- transcription, rendering, captions, storage
-- can still be tested end-to-end for free. Swap back to real AI scoring
once your Anthropic account has credits; see docs/tech-spec.md section 4.
"""

import json

import anthropic

from app.config import settings

MODEL = settings.anthropic_model

RUBRIC_PROMPT = """You are selecting short-form video clip candidates from a transcript.

Below is a chunk of a timestamped transcript. Identify moments that would make a
compelling standalone 15-90 second short-form clip (for TikTok/Reels/Shorts).

Look for:
- A complete, self-contained thought or story (not something that requires earlier context)
- Emotional peaks: strong reactions, laughter, surprise, tension
- Punchlines or a clear "payoff" moment
- Bold or controversial claims stated confidently
- Clear audience/host reaction (if present in the transcript)

Score each candidate from 0.0 to 1.0 for how clip-worthy it is.

Transcript chunk (timestamps in seconds):
{chunk_text}

Respond with ONLY a JSON array, no other text, in this exact format:
[
  {{"start": 12.3, "end": 45.6, "score": 0.85, "reason": "brief reason"}}
]

If nothing in this chunk is clip-worthy, respond with an empty array: []
"""


def _format_chunk(segments: list[tuple[float, float, str]]) -> str:
    return "\n".join(f"[{start:.1f}-{end:.1f}] {text}" for start, end, text in segments)


def _chunk_segments(
    segments: list[tuple[float, float, str]],
    chunk_seconds: float = 300.0,
    overlap_seconds: float = 30.0,
) -> list[list[tuple[float, float, str]]]:
    """Group segments into ~5-minute overlapping windows so we don't miss
    highlights that straddle a chunk boundary."""
    if not segments:
        return []

    chunks: list[list[tuple[float, float, str]]] = []
    chunk: list[tuple[float, float, str]] = []
    chunk_start = segments[0][0]

    for seg in segments:
        chunk.append(seg)
        if seg[1] - chunk_start >= chunk_seconds:
            chunks.append(chunk)
            overlap_start_time = seg[1] - overlap_seconds
            chunk = [s for s in chunk if s[1] >= overlap_start_time]
            chunk_start = chunk[0][0] if chunk else seg[1]

    if chunk:
        chunks.append(chunk)

    return chunks


def _heuristic_score_transcript(segments: list[tuple[float, float, str]]) -> list[dict]:
    """
    Free fallback used when the Anthropic API isn't available. Splits the
    transcript into a handful of ~30-second segments using natural gaps
    between transcript entries as cut points, with placeholder scores.
    This lets you validate the rest of the pipeline without any AI cost --
    it does NOT do real highlight detection, just mechanical segmentation.
    """
    if not segments:
        return []

    candidates = []
    target_length = 30.0
    current_start = segments[0][0]

    for i, (start, end, text) in enumerate(segments):
        if end - current_start >= target_length or i == len(segments) - 1:
            candidates.append({
                "start": current_start,
                "end": end,
                "score": 0.5,
                "reason": "heuristic fallback -- no AI scoring available",
            })
            if i + 1 < len(segments):
                current_start = segments[i + 1][0]

    return candidates[:5]


def score_transcript(segments: list[tuple[float, float, str]]) -> list[dict]:
    """Return a list of {start, end, score, reason} highlight candidates."""
    if not settings.anthropic_api_key:
        print("[highlight_scoring] No ANTHROPIC_API_KEY set -- using free heuristic fallback")
        return _heuristic_score_transcript(segments)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        chunks = _chunk_segments(segments)
        all_candidates: list[dict] = []

        for chunk in chunks:
            chunk_text = _format_chunk(chunk)
            prompt = RUBRIC_PROMPT.format(chunk_text=chunk_text)

            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            text = "".join(block.text for block in response.content if block.type == "text").strip()

            try:
                candidates = json.loads(text)
            except json.JSONDecodeError:
                continue

            all_candidates.extend(candidates)

        return all_candidates

    except Exception as e:
        # Covers billing errors, rate limits, network issues, etc. --
        # fall back to the heuristic rather than failing the whole job.
        print(f"[highlight_scoring] Anthropic API call failed, falling back to heuristic: {e}")
        return _heuristic_score_transcript(segments)
