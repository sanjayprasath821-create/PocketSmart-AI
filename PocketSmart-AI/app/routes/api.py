from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import current_user
from app.models.db_models import (
    RecommendationHistory,
    User,
)
from app.models.schemas import (
    HomeRequest,
    PartyRequest,
)
from app.services.recommendation_service import run


router = APIRouter()

settings = get_settings()


@router.post("/generate-home")
def generate_home(
    payload: HomeRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    response = run(
        db,
        user.id,
        "home",
        payload.model_dump(),
    )

    return {
        "planner": "home",
        "response": response,
    }


@router.post("/generate-party")
def generate_party(
    payload: PartyRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    response = run(
        db,
        user.id,
        "party",
        payload.model_dump(),
    )

    return {
        "planner": "party",
        "response": response,
    }


@router.post("/generate-jewelry")
async def generate_jewelry(
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form("Elegant"),
    outfit_description: str = Form(""),
    outfit_image: UploadFile | None = File(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    image_bytes = None
    filename = None

    if outfit_image and outfit_image.filename:
        allowed_types = (
            settings.allowed_image_types.split(",")
        )

        if (
            outfit_image.content_type
            not in allowed_types
        ):
            return {
                "error": (
                    "Unsupported image type"
                )
            }

        image_bytes = await outfit_image.read()
        filename = outfit_image.filename

        if (
            len(image_bytes)
            > settings.max_upload_mb * 1024 * 1024
        ):
            return {
                "error": "Image too large"
            }

    data = {
        "budget": budget,
        "occasion": occasion,
        "style": style,
        "outfit_description": outfit_description,
        "image_filename": filename,
    }

    response = run(
        db,
        user.id,
        "jewelry",
        data,
        image_bytes,
    )

    return {
        "planner": "jewelry",
        "response": response,
    }


@router.get("/session-info")
def session_info(
    user: User = Depends(current_user),
):
    return {
        "logged_in": True,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
    }


@router.get("/session-data")
def session_data(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(RecommendationHistory)
        .filter_by(user_id=user.id)
        .count()
    )

    return {
        "user_id": user.id,
        "recommendation_count": count,
    }


@router.get("/history")
def history(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(RecommendationHistory)
        .filter_by(user_id=user.id)
        .order_by(
            RecommendationHistory.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": record.id,
            "planner": record.planner,
            "response": record.response_text,
            "created_at": (
                record.created_at.isoformat()
            ),
        }
        for record in records
    ]


@router.get("/startup")
def startup():
    return {
        "status": "ready",
        "service": "PocketSmart AI",
    }