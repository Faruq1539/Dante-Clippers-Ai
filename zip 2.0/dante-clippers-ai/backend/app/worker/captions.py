"""
Builds an .srt subtitle file for a clip, from the subset of transcript
segments that fall within [clip_start, clip_end], with timestamps
re-based to start at 0 for the clip itself.
"""


def _format_srt_timestamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(
    segments: list[tuple[float, float, str]],
    clip_start: float,
    clip_end: float,
) -> str:
    lines = []
    index = 1

    for start, end, text in segments:
        # keep only segments that overlap the clip window
        if end <= clip_start or start >= clip_end:
            continue

        rel_start = max(0.0, start - clip_start)
        rel_end = min(clip_end - clip_start, end - clip_start)
        if rel_end <= rel_start:
            continue

        lines.append(str(index))
        lines.append(f"{_format_srt_timestamp(rel_start)} --> {_format_srt_timestamp(rel_end)}")
        lines.append(text)
        lines.append("")
        index += 1

    return "\n".join(lines)
