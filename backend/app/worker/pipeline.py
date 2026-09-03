"""
AI processing pipeline. Per docs/tech-spec.md section 4:

  transcribe()       -> faster-whisper (self-hosted) -- see transcription.py
  score_highlights()  -> LLM-based scoring pass       -- see highlight_scoring.py
  select_segments()   -> rank + de-dup top N non-overlapping segments
  render_clip()        -> FFmpeg reframe + burned-in captions

Kept as separate functions (rather than one big task) so it's easy to
swap implementations, retry a single failed stage, and unit test each
stage independently.
"""

import os
import subprocess
from dataclasses import dataclass

from app.services import storage
from app.worker import transcription, highlight_scoring, captions


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
    """Download the source video and return timestamped transcript segments."""
    local_path = storage.download_to_temp(storage_url)
    try:
        raw_segments = transcription.transcribe_audio(local_path)
    finally:
        storage.cleanup(local_path, local_path + ".wav")

    return [TranscriptSegment(start=s, end=e, text=t) for s, e, t in raw_segments]


def score_highlights(segments: list[TranscriptSegment]) -> list[HighlightCandidate]:
    """Score transcript segments for 'clippability' using an LLM pass."""
    raw = [(s.start, s.end, s.text) for s in segments]
    candidates = highlight_scoring.score_transcript(raw)

    return [
        HighlightCandidate(
            start=float(c["start"]),
            end=float(c["end"]),
            score=float(c["score"]),
            reason=c.get("reason", ""),
        )
        for c in candidates
        if c["end"] > c["start"] and (c["end"] - c["start"]) <= 120
    ]


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


def _caption_style_args(brand_template: dict | None) -> str:
    """Build an ASS force_style string from a brand template config."""
    brand_template = brand_template or {}
    font = brand_template.get("font", "Arial")
    primary_color = brand_template.get("primary_color", "#FFFFFF")
    outline_color = brand_template.get("accent_color", "#000000")

    def to_ass_color(hex_color: str) -> str:
        hex_color = hex_color.lstrip("#")
        r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
        return f"&H00{b}{g}{r}"

    return (
        f"FontName={font},FontSize=14,"
        f"PrimaryColour={to_ass_color(primary_color)},"
        f"OutlineColour={to_ass_color(outline_color)},"
        f"BorderStyle=1,Outline=2,Alignment=2,MarginV=60"
    )


def render_clip(
    source_storage_url: str,
    start: float,
    end: float,
    brand_template: dict | None = None,
    transcript_segments: list[TranscriptSegment] | None = None,
) -> str:
    """
    Cut the segment, reframe to 9:16 (center-crop), burn in captions, and
    upload the result. Returns the rendered clip's storage URL.
    """
    source_path = storage.download_to_temp(source_storage_url)
    duration = end - start

    srt_path = source_path + ".srt"
    output_path = source_path + "_clip.mp4"

    try:
        if transcript_segments:
            raw = [(s.start, s.end, s.text) for s in transcript_segments]
            srt_content = captions.build_srt(raw, start, end)
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)

        style = _caption_style_args(brand_template)

        vf_parts = [
            "crop=ih*9/16:ih",
            "scale=1080:1920",
        ]
        if transcript_segments and os.path.exists(srt_path):
            # Windows fix: double up backslashes (ffmpeg's filter-string
            # parser treats a single backslash as an escape character),
            # escape the drive-letter colon, and wrap the whole path in
            # quotes so the parser treats it as one token.
            escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:")
            vf_parts.append(f"subtitles='{escaped_srt}':force_style='{style}'")

        vf = ",".join(vf_parts)

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(start), "-to", str(end),
                    "-i", source_path,
                    "-vf", vf,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "128k",
                    output_path,
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            stderr_text = e.stderr.decode("utf-8", errors="replace") if e.stderr else "(no stderr captured)"
            raise RuntimeError(f"ffmpeg failed: {stderr_text}") from e

        return storage.upload_file(output_path, key_prefix="clips")

    finally:
        storage.cleanup(source_path, srt_path, output_path)
