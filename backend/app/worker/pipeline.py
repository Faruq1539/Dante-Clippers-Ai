"""
Stubbed AI processing pipeline. Each stage is a placeholder -- wire in
real implementations per docs/tech-spec.md section 4:

  transcribe()      -> Whisper (self-hosted) or a managed ASR API
  score_highlights() -> LLM-based scoring pass over transcript chunks
  select_segments()  -> rank + de-dup top N non-overlapping segments
  render_clip()       -> FFmpeg-based reframe + burned-in captions

Keeping these as separate functions (rather than one big task) makes it
easy to swap implementations, retry a single failed stage, and unit test
each stage independently.
"""

from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class HighlightCandidate:
    start: float
    end: float
    score: float
    reason: str


def transcribe(storage_url: str) -> list[TranscriptSegment]:
    """Return timestamped transcript segments for the source video."""
    # TODO: call Whisper or a managed ASR API, return real segments.
    raise NotImplementedError("Wire up a transcription backend here")


def score_highlights(segments: list[TranscriptSegment]) -> list[HighlightCandidate]:
    """Score transcript segments for 'clippability' using an LLM pass."""
    # TODO: call an LLM with a scoring rubric prompt over chunks of the
    # transcript. See docs/tech-spec.md section 4 for the rubric ideas
    # (emotional peaks, punchlines, strong claims, audience reaction).
    raise NotImplementedError("Wire up highlight scoring here")


def select_segments(candidates: list[HighlightCandidate], max_clips: int = 10) -> list[HighlightCandidate]:
    """Pick top N non-overlapping segments, each roughly 15-90s."""
    sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
    selected: list[HighlightCandidate] = []
    for candidate in sorted_candidates:
        if len(selected) >= max_clips:
            break
        overlaps = any(not (candidate.end <= s.start or candidate.start >= s.end) for s in selected)
        if not overlaps:
            selected.append(candidate)
    return selected


def render_clip(source_storage_url: str, start: float, end: float, brand_template: dict | None = None) -> str:
    """Cut, reframe to 9:16, and burn in captions. Returns the rendered clip's storage URL."""
    # TODO: FFmpeg pipeline -- extract segment, active-speaker crop (or
    # center-crop fallback) to 9:16, overlay word-level captions styled
    # per brand_template, upload result, return its storage URL.
    raise NotImplementedError("Wire up the render pipeline here")
