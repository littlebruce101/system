"""
main.py — Builder Agent

You describe what you want. The agent figures out how to build it
and returns working code plus instructions to run it.

Usage:
    python main.py "build me a script that renames all my files by date"
    python main.py "make a webpage that shows a countdown timer"
    python main.py "write a python script that backs up a folder every hour"

Requirements:
    pip install openai python-dotenv
"""

import argparse
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

BUILDER_PROMPT = """You are a builder agent. Your only job is to build what the user asks for.

Rules:
1. Always return working code — not pseudocode, not examples, actual runnable code.
2. After the code, add a short "How to run" section with exact commands.
3. If the request needs multiple files, show each one clearly labeled.
4. If something is unclear, make a reasonable assumption and state it briefly.
5. Do not explain concepts. Do not add caveats. Just build it.
6. Use the simplest language and tools that get the job done.
7. If the user asks for a script, default to Python unless they specify otherwise.
8. If the user asks for a webpage, return clean HTML/CSS/JS in a single file unless they specify otherwise.

Format:
- Code block first
- "How to run:" section after
- Nothing else unless critical
"""


def build(request: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": BUILDER_PROMPT},
            {"role": "user", "content": request},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="Builder agent — describe it, get code")
    parser.add_argument("request", help="What you want built")
    parser.add_argument("--save", metavar="FILE", help="Save output to a file")
    args = parser.parse_args()

    print("Building...\n")
    result = build(args.request)
    print(result)

    if args.save:
        with open(args.save, "w") as f:
            f.write(result)
        print(f"\nSaved to {args.save}")


if __name__ == "__main__":
    main()
