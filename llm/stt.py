"""Speech-to-text helpers."""

from __future__ import annotations

from pathlib import Path

from openai import OpenAI


def record_audio(
    seconds: float,
    wav_path: Path,
    sample_rate: int = 16000,
) -> None:
    import sounddevice as sd
    from scipy.io.wavfile import write as write_wav

    print(f"Recording for {seconds:.1f} seconds...")
    audio = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    write_wav(str(wav_path), sample_rate, audio)
    print(f"Saved recording to {wav_path}")


def transcribe_audio(
    client: OpenAI,
    wav_path: Path,
    model: str = "gpt-4o-mini-transcribe",
) -> str:
    with wav_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="text",
        )

    return transcription.strip()
