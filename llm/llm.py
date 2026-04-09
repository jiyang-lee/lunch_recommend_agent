"""Lunch recommendation LLM helpers."""

from __future__ import annotations

from openai import OpenAI


SYSTEM_PROMPT = """
You are a Korean lunch menu recommendation agent.

Rules:
- Keep replies short and natural
- Understand the user's intent
- Recommend lunch options that fit the user's situation
- Consider budget, taste, spice level, speed, and whether they want soup, rice, or noodles
- If information is missing, ask one short clarifying question
- Avoid overly long explanations
- Give 2-3 practical menu options when possible
- Avoid markdown styling such as **bold**, [brackets], and slash-separated formatting
- When the user asks for lunch recommendations, recommend only restaurants or menus that exist in the CSV database
- Never invent restaurant names, menus, prices, or categories that are not present in the CSV database
- If the CSV database is missing, empty, or does not contain a suitable option, say that clearly instead of making up recommendations

Supported tasks:
- Lunch menu recommendation
- Restaurant or menu suggestion
- Budget-friendly choice
- Fast meal suggestion
- Healthy meal suggestion

Answer in Korean.
""".strip()


def generate_response(
    client: OpenAI,
    user_text: str,
    menu_context: str = "",
    open_only_context: str = "",
    model: str = "gpt-5.4-mini",
) -> str:
    db_section = (
        "\n\nCSV database rule:\n"
        "For lunch recommendations, you must rely only on the CSV database entries.\n"
        "If the CSV database is unavailable or insufficient, say so clearly and do not invent options."
    )
    if open_only_context:
        db_section += (
            "\n\nMenu database:\n"
            f"{open_only_context}"
        )
    elif menu_context:
        db_section += (
            "\n\nMenu database:\n"
            "Use the following CSV data as the only allowed source for restaurant recommendations.\n"
            f"{menu_context}"
        )
    else:
        db_section += "\n\nMenu database:\nCSV database unavailable."

    response = client.responses.create(
        model=model,
        input=f"{SYSTEM_PROMPT}{db_section}\n\nUser input: {user_text}",
    )
    return response.output_text.strip()
