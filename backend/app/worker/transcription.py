"""
Transcription stage using faster-whisper (self-hosted, CTranslate2-based
Whisper implementation -- much lighter on GPU/CPU than the original
openai-whisper package).

If you'd rather use a managed ASR API instead of self-hosting, swap the
body of `transcribe_audio` for an API call and keep the same return shape
-- everything downstream only depends on (start, end, text) tuples.
"""

import subprocess

from app.config import settings


def _extract_audio(video_path: str) -> str:
    """Extract a 16kHz mono WAV from the source video -- what Whisper wants."""
    audio_path = video_path + ".wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-ac", "1", "-ar", "16000",
            "-f", "wav", audio_path,
        ],
        check=True,
        capture_output=True,
    )
    return audio_path


def transcribe_audio(video_path: str) -> list[tuple[float, float, str]]:
    """Return a list of (start_seconds, end_seconds, text) segments."""
    from faster_whisper import WhisperModel

    audio_path = _extract_audio(video_path)

    # "base" is a reasonable default for a first pass -- accurate enough
    # for highlight scoring, fast enough to keep processing cost down.
    # Bump to "small"/"medium" if transcript quality is the bottleneck.
    model = WhisperModel(settings.whisper_model_size, device="auto", compute_type="auto")

    segments, _info = model.transcribe(audio_path, vad_filter=True)

    return [(seg.start, seg.end, seg.text.strip()) for seg in segments]
