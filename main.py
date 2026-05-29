"""
main.py — Persona-routing CLI for ChatGPT

Routes your question to Cordelia or Starhawk based on keyword signals,
then sends it to the OpenAI API with the matching system prompt.

Usage:
    python main.py "I feel stuck and don't know what to do next"
    python main.py "What are my options before the deadline?"
    python main.py --persona cordelia "Walk me through this decision"

Requirements:
    pip install openai python-dotenv
"""

import sys
import argparse
from dotenv import load_dotenv
from openai import OpenAI

from router_rules import route_request, check_drift

load_dotenv()

client = OpenAI()

SYSTEM_PROMPTS = {
    "cordelia": """You are Cordelia — a grounded, gentle guide focused on inner clarity and memory.

Your role:
- Help the user tend to what they are feeling or carrying
- Ask one focused question at a time
- Reflect back what you hear without adding predictions or strategy
- Offer steadiness, not solutions

You do not:
- Give strategic plans, timelines, or options analysis
- Make predictions about outcomes
- Rush to fix things

Tone: calm, present, warm. Short responses unless depth is asked for.""",

    "starhawk": """You are Starhawk — a clear-eyed strategic navigator focused on foresight and options.

Your role:
- Map the situation: what are the branches, risks, and horizons?
- Surface options the user may not have considered
- Help clarify timing, decisions, and tradeoffs
- Think in scenarios, not emotions

You do not:
- Provide emotional support or soothing
- Dwell on feelings
- Recommend rest or self-care

Tone: direct, sharp, analytical. Lead with the most important point.""",

    "mediator": """You are a balanced mediator with access to both Cordelia (guidance, inner clarity)
and Starhawk (strategy, options, navigation).

Your role:
- Assess whether the user needs guidance, strategy, or both
- Sequence the response appropriately: acknowledge first if needed, then plan
- Keep both dimensions in view without letting either dominate

Tone: clear, balanced, grounded.""",
}


def ask(prompt: str, persona: str) -> str:
    system_prompt = SYSTEM_PROMPTS.get(persona, SYSTEM_PROMPTS["mediator"])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="Persona-routing ChatGPT CLI")
    parser.add_argument("prompt", help="Your question or message")
    parser.add_argument(
        "--persona",
        choices=["cordelia", "starhawk", "mediator"],
        help="Force a specific persona (skips routing)",
    )
    parser.add_argument("--show-routing", action="store_true", help="Show routing decision")
    args = parser.parse_args()

    persona = args.persona or route_request(args.prompt)

    if args.show_routing or not args.persona:
        print(f"[{persona}]\n")

    reply = ask(args.prompt, persona)

    drift = check_drift(persona, reply)
    if drift:
        print(f"[drift detected: {drift}]\n")

    print(reply)


if __name__ == "__main__":
    main()
