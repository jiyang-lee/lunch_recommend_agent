# lunch_recommend_agent

## STT -> LLM -> TTS

Split modules:

- `stt.py`
- `llm.py`
- `menu_db.py`
- `tts.py`
- `llm_main.py`
- `streamlit_app.py`

Create the environment and install dependencies with `uv`:

```bash
uv venv
uv add openai python-dotenv gTTS sounddevice scipy streamlit
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

Run the Streamlit chat dashboard:

```bash
uv run streamlit run streamlit_app.py
```

Or skip STT and send text directly:

```bash
uv run python llm_main.py --text "What should I eat for lunch?"
```

TTS is played automatically after the answer is generated.

Characters such as `[`, `]`, `*`, and `/` are removed only for TTS playback.

If you have a CSV menu database, place it at `restaurants.csv` in the project root,
or pass a custom path with `--menu-csv your_file.csv`.
