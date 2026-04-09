"""Lunch recommendation LLM helpers."""

from __future__ import annotations

from openai import OpenAI


SYSTEM_PROMPT = """
You are a Korean lunch menu recommendation agent.

Rules:
- Keep replies short and natural.
- Understand the user's intent.
- Recommend lunch options that fit the user's situation.
- Consider budget, taste, spice level, speed, and whether they want soup, rice, or noodles.
- If information is missing, ask one short clarifying question.
- Avoid overly long explanations.
- Give 2-3 practical menu options when possible.
- Avoid markdown styling such as **bold**, [brackets], and slash-separated formatting.
- When recommendation candidate data is provided, recommend only from that data.
- Never invent restaurant names, menus, prices, categories, distances, or locations that are not present in the provided data.
- If the provided data is missing, empty, or does not contain a suitable option, say that clearly instead of making up recommendations.
- If distance information is provided, prefer closer places that fit the user's request.

Supported tasks:
- Lunch menu recommendation
- Restaurant or menu suggestion
- Budget-friendly choice
- Fast meal suggestion
- Healthy meal suggestion
- Nearby restaurant recommendation

Answer in Korean.
""".strip()


def generate_response(
    client: OpenAI,
    user_text: str,
    menu_context: str = "",
    open_only_context: str = "",
    context_source: str = "candidate database",
    note: str = "",
    model: str = "gpt-5.4-mini",
) -> str:
    context_body = open_only_context or menu_context
    data_section = (
        "\n\nData source rule:\n"
        f"For lunch recommendations, you must rely only on the provided {context_source} entries.\n"
        "If the data source is unavailable or insufficient, say so clearly and do not invent options."
    )
    if context_body:
        data_section += (
            "\n\nRecommendation candidates:\n"
            "Use the following data as the only allowed source for restaurant recommendations.\n"
            f"{context_body}"
        )
    else:
        data_section += "\n\nRecommendation candidates:\nNo candidate data available."

    if note:
        data_section += f"\n\nRuntime note:\n{note}"

    response = client.responses.create(
        model=model,
        input=f"{SYSTEM_PROMPT}{data_section}\n\nUser input: {user_text}",
    )
    return response.output_text.strip()
