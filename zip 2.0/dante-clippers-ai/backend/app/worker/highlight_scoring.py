"""
Highlight scoring stage: chunks the transcript and asks an LLM to identify
clip-worthy moments in each chunk, with a start/end/score/reason per moment.

This is the core "AI smart highlighting" feature from the product spec --
worth iterating on the prompt/rubric a lot as you see real output quality.
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
            # start next chunk `overlap_seconds` before this one ended
            overlap_start_time = seg[1] - overlap_seconds
            chunk = [s for s in chunk if s[1] >= overlap_start_time]
            chunk_start = chunk[0][0] if chunk else seg[1]

    if chunk:
        chunks.append(chunk)

    return chunks


def score_transcript(segments: list[tuple[float, float, str]]) -> list[dict]:
    """Return a list of {start, end, score, reason} highlight candidates."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set -- required for highlight scoring")

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
            # Model didn't return clean JSON for this chunk -- skip it
            # rather than failing the whole job. Worth logging/alerting
            # on in production so you can tighten the prompt.
            continue

        all_candidates.extend(candidates)

    return all_candidates
