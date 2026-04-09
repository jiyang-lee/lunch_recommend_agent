"""Main entry point for the lunch recommendation voice agent."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from llm import generate_response
from menu_db import DEFAULT_MENU_CSV, load_menu_context
from stt import record_audio, transcribe_audio
from tts import play_audio, synthesize_speech


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the lunch recommendation STT -> LLM -> TTS flow."
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Skip STT and use this text directly.",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=5.0,
        help="Recording duration when using the microphone.",
    )
    parser.add_argument(
        "--transcribe-model",
        default="gpt-4o-mini-transcribe",
        help="OpenAI transcription model name.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="OpenAI model name.",
    )
    parser.add_argument(
        "--tts-lang",
        default="ko",
        help="gTTS language code.",
    )
    parser.add_argument(
        "--output-audio",
        default="sample1.mp3",
        help="Path to the generated TTS audio file.",
    )
    parser.add_argument(
        "--recording-path",
        default="recorded.wav",
        help="Temporary WAV file used during transcription.",
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Save TTS audio without playing it.",
    )
    parser.add_argument(
        "--menu-csv",
        default=DEFAULT_MENU_CSV,
        help="CSV file path for the lunch menu database.",
    )
    return parser


def main() -> int:
    load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))

    args = build_parser().parse_args()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set. Check your .env file.", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    menu_csv_path = Path(args.menu_csv)
    menu_context = load_menu_context(menu_csv_path)
    if menu_context:
        print(f"Loaded menu CSV: {menu_csv_path}")
    else:
        print(f"Menu CSV not found or empty: {menu_csv_path}")

    if args.text:
        user_text = args.text.strip()
        print(f"Using direct text input: {user_text}")
    else:
        wav_path = Path(args.recording_path)
        record_audio(args.seconds, wav_path)
        user_text = transcribe_audio(client, wav_path, args.transcribe_model)
        print(f"Transcribed text: {user_text}")

    answer = generate_response(client, user_text, menu_context, args.model)
    print("\nAssistant reply:")
    print(answer)

    output_path = Path(args.output_audio)
    spoken_text = synthesize_speech(answer, output_path, args.tts_lang)
    print(f"\nSaved TTS audio to {output_path}")
    print(f"TTS text: {spoken_text}")

    if not args.no_play:
        play_audio(output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
