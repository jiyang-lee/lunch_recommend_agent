# lunch_recommend_agent

## STT -> LLM -> TTS

Split modules:

- `stt.py`
- `llm.py`
- `tts.py`
- `llm_main.py`

Create the environment and install dependencies with `uv`:

```bash
uv venv
uv add openai python-dotenv gTTS sounddevice scipy
```

Set your OpenAI key:

```bash
set OPENAI_API_KEY=your_key_here
```

If you already have a `.env` file in the project root, put `OPENAI_API_KEY=...` there and the script will load it automatically.

Run with microphone input:

```bash
uv run python llm_main.py
```

Or skip STT and send text directly:

```bash
uv run python llm_main.py --text "What should I eat for lunch?"
```

TTS is played automatically after the answer is generated.

Characters such as `[`, `]`, `*`, and `/` are removed only for TTS playback.
