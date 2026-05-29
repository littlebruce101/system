# builder-agent

Describe what you want. Get working code.

## Setup

```bash
git clone https://github.com/littlebruce101/system.git
cd system
pip install openai python-dotenv
cp .env.example .env
# add your OpenAI API key to .env
```

## Usage

```bash
python main.py "build me a script that renames all my files by date"
python main.py "make a webpage with a countdown timer"
python main.py "write a script that backs up a folder every hour"
python main.py "build a to-do list app in the terminal"
```

Save the output directly to a file:

```bash
python main.py "build a script that monitors a folder for new files" --save monitor.py
```

## What it does

- Returns working, runnable code — not examples or pseudocode
- Adds exact "how to run" instructions
- Defaults to Python for scripts, single-file HTML for webpages
- Uses `gpt-4o` for best code quality
