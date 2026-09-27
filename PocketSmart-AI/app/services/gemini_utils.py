import json

from app.config import get_settings


settings = get_settings()


def money(value: float) -> str:
    return f"₹{value:,.2f}"


def mock_home(data: dict) -> str:
    budget = data["budget"]

    allocation = {
        "Furniture": round(budget * 0.40, 2),
        "Lighting": round(budget * 0.15, 2),
        "Decor": round(budget * 0.20, 2),
        "Utilities": round(budget * 0.15, 2),
        "Reserve": round(budget * 0.10, 2),
    }

    items = "\n".join(
        f"- {item['category']} × {item['quantity']}"
        for item in data.get("items", [])
    )

    if not items:
        items = "- General room essentials"

    return (
        f"HOME INTERIOR PLAN — "
        f"{data['room_type']} / "
        f"{data.get('style', 'Modern')}\n\n"
        f"Budget: {money(budget)}\n\n"
        f"Allocation:\n"
        f"{json.dumps(allocation, indent=2)}\n\n"
        f"Requested items:\n"
        f"{items}\n\n"
        "Suggested approach:\n"
        "1. Prioritize essential furniture.\n"
        "2. Reserve part of the budget for lighting.\n"
        "3. Add decorative pieces after essentials.\n"
        "4. Keep a contingency reserve.\n\n"
        "Compare equivalent products on Amazon and IKEA. "
        "Prices, stock and seller details must be verified "
        "on the live platforms."
    )


def mock_party(data: dict) -> str:
    budget = data["budget"]
    guests = data["guests"]

    allocation = {
        "Catering": round(budget * 0.45, 2),
        "Venue": round(budget * 0.25, 2),
        "Decoration": round(budget * 0.15, 2),
        "Entertainment": round(budget * 0.10, 2),
        "Reserve": round(budget * 0.05, 2),
    }

    per_guest = budget / guests

    return (
        f"PARTY PLAN — {data['event_type']}\n\n"
        f"Budget: {money(budget)}\n"
        f"Guests: {guests}\n"
        f"Approx. budget per guest: "
        f"{money(per_guest)}\n\n"
        f"Allocation:\n"
        f"{json.dumps(allocation, indent=2)}\n\n"
        f"Venue: {data.get('venue') or 'Flexible'}\n"
        f"City: {data.get('city') or 'Not specified'}\n"
        f"Preferences: "
        f"{data.get('preferences') or 'None'}\n\n"
        "Compare food/catering through Swiggy or Zomato "
        "and accommodation through OYO where relevant. "
        "Verify current availability and prices."
    )


def mock_jewelry(data: dict) -> str:
    return (
        f"JEWELRY PLAN — "
        f"{data['occasion']} / "
        f"{data.get('style', 'Elegant')}\n\n"
        f"Budget: {money(data['budget'])}\n\n"
        f"Outfit description: "
        f"{data.get('outfit_description') or 'Not provided'}\n\n"
        f"Outfit image supplied: "
        f"{'Yes' if data.get('image_filename') else 'No'}\n\n"
        "Suggested allocation:\n"
        "- Earrings: 30–35%\n"
        "- Necklace/Pendant: 35–40%\n"
        "- Bracelet/Bangles: 15–20%\n"
        "- Reserve: remaining budget\n\n"
        "Consider occasion, outfit color, neckline, "
        "style preference and overall balance.\n\n"
        "Compare matching styles on Amazon and Flipkart "
        "and verify material, seller and return policy."
    )


def build_prompt(
    planner: str,
    data: dict,
) -> str:
    return f"""
You are PocketSmart AI, a budget-aware
recommendation assistant.

Planner:
{planner}

User input:
{json.dumps(data, ensure_ascii=False, indent=2)}

Create a practical recommendation plan.

Requirements:

1. Respect the total budget.
2. Show useful category allocations.
3. Give estimated price ranges where appropriate.
4. Do not claim live inventory unless it is actually provided.
5. Treat Amazon, Flipkart, IKEA, Swiggy,
   Zomato, OYO and similar platforms as places
   users can compare and verify.
6. Clearly state that live prices and availability
   must be verified.
7. For jewelry, consider the outfit description.
8. If an outfit image is supplied, analyze visible
   colors, patterns and styling only.
9. Keep the answer structured and easy to read.
10. Avoid inventing specific live product listings.
""".strip()


def generate(
    planner: str,
    data: dict,
    image: bytes | None = None,
) -> str:

    fallback_functions = {
        "home": mock_home,
        "party": mock_party,
        "jewelry": mock_jewelry,
    }

    fallback = fallback_functions[planner]

    if settings.mock_ai or not settings.gemini_api_key:
        return fallback(data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.gemini_api_key
        )

        parts = [
            build_prompt(
                planner,
                data,
            )
        ]

        if image:
            parts.append(
                types.Part.from_bytes(
                    data=image,
                    mime_type="image/jpeg",
                )
            )

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=parts,
        )

        text = getattr(
            response,
            "text",
            None,
        )

        if not text:
            raise RuntimeError(
                "Empty Gemini response"
            )

        return text.strip()

    except Exception as exc:
        fallback_text = fallback(data)

        return (
            fallback_text
            + "\n\n"
            + f"[Fallback used: "
            f"{type(exc).__name__}]"
        )