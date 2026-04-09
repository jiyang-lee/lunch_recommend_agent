"""Text-to-speech helpers."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from gtts import gTTS


_TTS_REMOVE_TABLE = str.maketrans("", "", "[]*/`")


def sanitize_text_for_tts(text: str) -> str:
    cleaned = text.translate(_TTS_REMOVE_TABLE)
    cleaned = re.sub(r"[_#>-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "I prepared a lunch recommendation."


def synthesize_speech(text: str, output_path: Path, lang: str = "ko") -> str:
    tts_text = sanitize_text_for_tts(text)
    gTTS(text=tts_text, lang=lang).save(str(output_path))
    return tts_text


def play_audio(output_path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(output_path))
        return

    if sys.platform == "darwin":
        subprocess.run(["open", str(output_path)], check=False)
        return

    subprocess.run(["xdg-open", str(output_path)], check=False)
