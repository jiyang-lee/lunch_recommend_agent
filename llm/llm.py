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


def extract_search_keyword(
    client: OpenAI,
    user_text: str,
    model: str = "gpt-5.4-mini",
    base_location: str = "울산 북구 송정",
) -> str:
    """사용자 질문에서 카카오맵 검색용 키워드를 추출합니다."""
    prompt = (
        f"다음 사용자 질문을 보고, 카카오맵에서 음식점 검색에 쓸 짧은 한국어 키워드를 만들어줘.\n"
        f"규칙:\n"
        f"- 사용자 질문에 특정 장소나 지역이 언급되면 반드시 그 장소/지역을 키워드에 포함해.\n"
        f"- 사용자가 지역을 따로 언급하지 않았을 때만 기본 지역 '{base_location}'을 사용해.\n"
        f"- 음식 종류, 분위기 등 검색에 유용한 조건도 키워드에 포함해.\n"
        f"- 키워드만 출력해, 설명이나 부가 문장 없이.\n\n"
        f"질문: {user_text}"
    )
    resp = client.responses.create(model=model, input=prompt)
    return resp.output_text.strip()


def extract_place_count(user_text: str, default: int = 3) -> int:
    """사용자 질문에서 요청 개수를 파싱합니다."""
    import re
    # 한국어 숫자 매핑
    korean_nums = {"하나": 1, "한": 1, "두": 2, "세": 3, "넷": 4, "다섯": 5,
                  "여섯": 6, "일곡": 7, "여덟": 8, "아홉": 9, "열": 10}
    for word, num in korean_nums.items():
        if re.search(rf"{word}\s*(개|곳)", user_text):
            return min(num, 15)
    # 아라비아 숫자
    match = re.search(r"(\d+)\s*(개|곳)", user_text)
    if match:
        return min(int(match.group(1)), 15)
    return default


def generate_response_with_places(
    client: OpenAI,
    user_text: str,
    places: list[dict],
    model: str = "gpt-5.4-mini",
) -> str:
    """카카오맵 검색 결과를 바탕으로 추천 답변을 생성합니다."""
    places_text = "\n".join(
        [
            f"{i + 1}. {p['name']} | 주소: {p['address']}"
            + (f" | 전화: {p['phone']}" if p.get("phone") else "")
            + (f" | 카테고리: {p['category']}" if p.get("category") else "")
            for i, p in enumerate(places)
        ]
    )
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"카카오맵 검색 결과 (반드시 이 가게들 중에서만 추천하세요):\n"
        f"{places_text}\n\n"
        f"사용자 질문: {user_text}"
    )
    resp = client.responses.create(model=model, input=prompt)
    return resp.output_text.strip()


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
