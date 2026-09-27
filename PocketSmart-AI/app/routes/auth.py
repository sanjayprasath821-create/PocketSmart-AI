from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import User
from app.models.schemas import (
    UserCreate,
    UserLogin,
)
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/register",
    response_class=HTMLResponse,
)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "request": request,
        },
    )


@router.post("/register")
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(User)
        .filter(
            User.email == payload.email.lower()
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(
            payload.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Registration successful",
        "user_id": user.id,
    }


@router.post("/register-form")
def register_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "request": request,
                "error": (
                    "Password must be at least "
                    "6 characters."
                ),
            },
        )

    existing = (
        db.query(User)
        .filter(
            User.email == email.lower()
        )
        .first()
    )

    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "request": request,
                "error": (
                    "Email already registered."
                ),
            },
        )

    user = User(
        name=name.strip(),
        email=email.lower(),
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()

    return RedirectResponse(
        "/login?registered=1",
        status_code=303,
    )


@router.get(
    "/login",
    response_class=HTMLResponse,
)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
        },
    )


@router.post("/login-form")
def login_form(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.email == email.lower()
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            password,
            user.password_hash,
        )
    ):
        return RedirectResponse(
            "/login?error=Invalid%20email%20or%20password",
            status_code=303,
        )

    token = create_access_token(user.id)

    response = RedirectResponse(
        "/dashboard",
        status_code=303,
    )

    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )

    return response


@router.post("/token")
def token(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(
            User.email == payload.email.lower()
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    return {
        "access_token": create_access_token(
            user.id
        ),
        "token_type": "bearer",
    }


@router.get("/logout")
def logout():
    response = RedirectResponse(
        "/login",
        status_code=303,
    )

    response.delete_cookie(
        "access_token"
    )

    return response