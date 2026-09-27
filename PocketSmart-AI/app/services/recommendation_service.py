import json

from app.models.db_models import RecommendationHistory
from app.services.gemini_utils import generate


def run(
    db,
    user_id,
    planner,
    data,
    image=None,
):
    text = generate(
        planner,
        data,
        image,
    )

    record = RecommendationHistory(
        user_id=user_id,
        planner=planner,
        request_json=json.dumps(data),
        response_text=text,
    )

    db.add(record)
    db.commit()

    return text