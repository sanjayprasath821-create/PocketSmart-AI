import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Request,
    UploadFile,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import current_user
from app.models.db_models import (
    RecommendationHistory,
    User,
)
from app.services.recommendation_service import run


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

settings = get_settings()


def render(
    request: Request,
    template_name: str,
    user=None,
    **kwargs,
):
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "request": request,
            "user": user,
            **kwargs,
        },
    )


@router.get(
    "/",
    response_class=HTMLResponse,
)
def home(request: Request):
    return render(
        request,
        "index.html",
    )


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
)
def dashboard(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(RecommendationHistory)
        .filter_by(user_id=user.id)
        .order_by(
            RecommendationHistory.created_at.desc()
        )
        .limit(10)
        .all()
    )

    return render(
        request,
        "dashboard.html",
        user,
        history=history,
    )


@router.get(
    "/testimonials",
    response_class=HTMLResponse,
)
def testimonials(request: Request):
    return render(
        request,
        "testimonials.html",
    )


@router.get(
    "/home-planner",
    response_class=HTMLResponse,
)
def home_planner(
    request: Request,
    user: User = Depends(current_user),
):
    return render(
        request,
        "home_planner.html",
        user,
    )


@router.post(
    "/generate-home",
    response_class=HTMLResponse,
)
def generate_home_page(
    request: Request,
    budget: float = Form(...),
    room_type: str = Form(...),
    style: str = Form("Modern"),
    location: str = Form(""),
    items_json: str = Form("[]"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    try:
        items = json.loads(items_json)
    except Exception:
        items = []

    data = {
        "budget": budget,
        "room_type": room_type,
        "style": style,
        "location": location,
        "items": items,
    }

    response = run(
        db,
        user.id,
        "home",
        data,
    )

    return render(
        request,
        "recommendation.html",
        user,
        planner="Home Interior",
        response=response,
    )


@router.get(
    "/party-planner",
    response_class=HTMLResponse,
)
def party_planner(
    request: Request,
    user: User = Depends(current_user),
):
    return render(
        request,
        "party_planner.html",
        user,
    )


@router.post(
    "/generate-party",
    response_class=HTMLResponse,
)
def generate_party_page(
    request: Request,
    budget: float = Form(...),
    guests: int = Form(...),
    event_type: str = Form(...),
    venue: str = Form(""),
    city: str = Form(""),
    preferences: str = Form(""),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    data = {
        "budget": budget,
        "guests": guests,
        "event_type": event_type,
        "venue": venue,
        "city": city,
        "preferences": preferences,
    }

    response = run(
        db,
        user.id,
        "party",
        data,
    )

    return render(
        request,
        "recommendation.html",
        user,
        planner="Party Budget",
        response=response,
    )


@router.get(
    "/jewelry-planner",
    response_class=HTMLResponse,
)
def jewelry_planner(
    request: Request,
    user: User = Depends(current_user),
):
    return render(
        request,
        "jewelry_planner.html",
        user,
    )


@router.post(
    "/generate-jewelry",
    response_class=HTMLResponse,
)
async def generate_jewelry_page(
    request: Request,
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
            return render(
                request,
                "jewelry_planner.html",
                user,
                error=(
                    "Only JPG, PNG and WebP "
                    "images are allowed."
                ),
            )

        image_bytes = await outfit_image.read()
        filename = outfit_image.filename

        if (
            len(image_bytes)
            > settings.max_upload_mb * 1024 * 1024
        ):
            return render(
                request,
                "jewelry_planner.html",
                user,
                error="Image is too large.",
            )

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

    return render(
        request,
        "recommendation.html",
        user,
        planner="Jewelry Budget",
        response=response,
    )


@router.get(
    "/history",
    response_class=HTMLResponse,
)
def history_page(
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(RecommendationHistory)
        .filter_by(user_id=user.id)
        .order_by(
            RecommendationHistory.created_at.desc()
        )
        .all()
    )

    return render(
        request,
        "history.html",
        user,
        history=history,
    )


@router.get(
    "/recommendations-details/{id}",
    response_class=HTMLResponse,
)
def recommendation_details(
    id: int,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(RecommendationHistory)
        .filter_by(
            id=id,
            user_id=user.id,
        )
        .first()
    )

    if not record:
        return RedirectResponse(
            "/history",
            status_code=303,
        )

    return render(
        request,
        "recommendation.html",
        user,
        planner=record.planner.title(),
        response=record.response_text,
    )