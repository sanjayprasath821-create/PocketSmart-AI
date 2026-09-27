from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class HomeItem(BaseModel):
    category: str
    quantity: int = Field(
        1,
        ge=1,
        le=100,
    )


class HomeRequest(BaseModel):
    budget: float = Field(gt=0)

    room_type: str

    style: str = "Modern"

    items: list[HomeItem] = []

    location: str = ""


class PartyRequest(BaseModel):
    budget: float = Field(gt=0)

    guests: int = Field(
        gt=0,
        le=10000,
    )

    event_type: str

    venue: str = ""

    city: str = ""

    preferences: str = ""