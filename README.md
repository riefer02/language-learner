# Korean Language Learner

> **Status: functional early prototype.** This repository provides translation, text-to-speech, a phrase library, short generated conversations, and a working FSRS review loop with a 30-item starter deck and progress view. It does **not** yet include real per-user accounts, Hangul onboarding, pronunciation feedback, scene roleplay, or PWA/offline support. See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the honest current state, [`docs/ROADMAP.md`](docs/ROADMAP.md) for execution status, and [`docs/KIKU_BLUEPRINT.md`](docs/KIKU_BLUEPRINT.md) for the product redesign.

An application for learning Korean that includes both a command-line interface and a web application. Translate English phrases to Korean, generate pronunciation audio, and browse saved phrases and conversations.

## Features

### CLI Tool

- Translates English text to Korean using OpenAI's `gpt-4.1-nano` model
- Generates natural-sounding Korean speech using OpenAI's Text-to-Speech (TTS) API
- Saves audio output as MP3 files in the `audio_output/` directory
- Accepts input either interactively or as a command-line argument

### Web Application

- **Onboarding:** `/welcome` captures goal, daily time, experience, and timezone, then teaches a first spoken 안녕하세요 with local-only recording
- **Hangul bootcamp:** `/learn/hangul` has seven lessons (letters, vowels/blocks, batchim, double batchim, real-world text, connected speech, and a final reading check) with 88 interactive drills
- **Learn loop:** `/learn` shows what is due, `/learn/review` presents a retrieval card and grades it with FSRS-6 in a 3/10/25-minute session, and `/learn/progress` shows practiced cards and recent reviews
- **Mission scenes:** `/learn/scenes` has four scripted Korean roleplays (café, directions, pharmacy, workplace intro) with tolerant answer matching, hints, resumable progress, voice or typed answers, and a debrief that adds three chunks to the review deck
- **Can-do proof:** completing a scene creates a dated “I can…” artifact on `/learn/progress` and surfaces the next mission on Today
- **Weekly recap:** `/learn/progress` shows 7-day review activity, new cards, can-dos, active days, a 30-day Good/Easy recall signal, and 7+/30+ day delayed-retention rates
- **Sound Gym:** `/learn/sound-gym` has minimal-pair perception drills and production prompts with local recording and transcript-based speech checks (not an accent grade; raw audio is not stored)
- **Alpha metrics:** `flask metrics` prints activation, users with reviews, speech attempts, and D1/D7
- **Starter deck:** `flask seed-content` adds 30 Korean items and creates review cards for the local learner
- **Daily guardrail:** 10 new cards per day by default; review cards come first
- User-friendly interface for English-to-Korean translation
- Audio playback of Korean pronunciations
- Paginated phrase library
- Generated conversation scenarios with per-line and merged audio
- SQLite storage for phrases, conversations, lines, items, and review state

**Still planned:** real per-user accounts, placement testing, phoneme-level pronunciation feedback, native-reviewed seed audio, scene/roleplay debriefs, can-do progress, and PWA/offline. See [`docs/KIKU_BLUEPRINT.md`](docs/KIKU_BLUEPRINT.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).

### Conversational Scenarios

- Generate short, realistic Korean conversations (2–4 lines, 2 speakers) from a scenario prompt
- Each line is spoken by a different voice and saved as an individual audio file
- All lines are merged into a single audio file for playback as a full conversation
- Accessible via the web interface: create, list, and view conversations
- Conversations and their lines are stored in the database (see `Conversation` and `ConversationLine` models)

## Prerequisites

- Python 3.11 or newer (3.12 recommended)
- An OpenAI API key
- `ffmpeg` for conversation audio merging
- Flask and related packages (see `requirements.txt`)

## Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd korean-language-learner
   ```

2. **Create a `.env` file:**
   Create a file named `.env` in the project root directory and add your OpenAI API key:

   ```
   OPENAI_API_KEY='your_openai_api_key_here'
   ```

   _(This file is ignored by Git via `.gitignore`)_

3. **Set up the environment and install dependencies:**
   It's recommended to use a virtual environment.

   ```bash
   make install
   ```

   This command will:

   - Create a Python virtual environment named `venv`
   - Activate the environment
   - Install the required packages listed in `requirements.txt`

   _Alternatively, you can set up the virtual environment and install packages manually:_

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   flask init-db
   ```
   Or using the Makefile:
   ```bash
   make init-db
   ```

   `flask init-db` applies Alembic migrations. The app no longer creates tables
   automatically at startup, so a fresh checkout needs this step (or
   `flask db upgrade`) before the first request.

## Usage

### CLI Tool

Make sure your virtual environment is active (`source venv/bin/activate` or use the `make` commands).

- **Interactive Mode:**

  ```bash
  make run
  ```

  The script will prompt you to enter an English phrase.

- **With a Phrase Argument:**

  ```bash
  make runp phrase="I want to learn Korean"
  ```

  Replace "I want to learn Korean" with your desired phrase.

- **Directly with Python:**
  ```bash
  python hangul.py  # Interactive mode
  python hangul.py "Where is the library?"  # With argument
  ```

### Web Application

To run the web application:

1. Ensure your virtual environment is active
2. Start the Flask development server:
   ```bash
   python run.py
   ```
3. Seed the starter review deck (idempotent):
   ```bash
   flask seed-content
   ```
4. Optional: pre-generate audio for the review deck. This spends API credits,
   so check the dry run first:
   ```bash
   flask generate-item-audio --dry-run
   flask generate-item-audio
   ```
5. Open your web browser and navigate to `http://localhost:5000`
6. Start at **Learn**. The first visit opens a two-minute onboarding flow and a first spoken sentence; after that, the daily review loop is ready. Use **Hangul** for the reading bootcamp, or **Conversations** to create and study conversational scenarios.

## Project Structure

- `/app` - Web application components
  - `/services` - Backend services for translation, audio, conversation generation
  - `/static` - Static assets (CSS, JS, audio files)
  - `/templates` - HTML templates (including conversations UI)
  - `/utils` - Utility functions (including audio merging)
- `/audio_output` - Generated audio files from the CLI tool
- `hangul.py` - CLI tool entry point
- `run.py` - Web application entry point
- `config.py` - Configuration settings
- `korean_learner.db` - SQLite database

## Development Checks

```bash
make install-dev   # runtime + test/lint dependencies
make test          # pytest
make lint          # ruff
flask metrics      # alpha activation/retention summary
```

The test suite does not call OpenAI and does not need a real API key. It uses a
temporary SQLite database and a fake OpenAI client.

## Security Notes

- The app binds to `127.0.0.1` by default. Do not expose it publicly without
  authentication and HTTPS.
- For a non-local deployment, set `REQUIRE_AUTH=true`, `APP_PASSWORD`, and
  `SECRET_KEY`, and put the app behind a TLS-terminating proxy.
- Set `TRUST_PROXY=true` only behind a trusted proxy so client IPs and rate
  limits are correct.
- Rotate any API key that has ever been committed or shared. Keys belong in
  `.env` (ignored by git) or the deployment secret manager.
- Audio is stored under `app/static/audio` for local development. The
  `flask media-audit` command reports orphans and missing files;
  `flask media-gc --delete` removes orphans older than a day.

## Cleaning Up

To remove the virtual environment, audio output directory, and compiled Python files:

```bash
make clean
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### Audio Merging (ffmpeg)

The conversation feature requires [ffmpeg](https://ffmpeg.org/) to be installed and available in your system PATH for audio merging. If you see errors related to audio file reading or merging, ensure ffmpeg is installed:

- **macOS:**
  ```sh
  brew install ffmpeg
  ```
- **Ubuntu/Debian:**
  ```sh
  sudo apt-get install ffmpeg
  ```
- **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your PATH.
