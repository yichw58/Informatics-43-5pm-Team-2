from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──
class RegisterRequest(BaseModel):
    email: EmailStr
    displayName: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Profile ──
class ProfileUpdate(BaseModel):
    displayName: Optional[str] = Field(default=None, min_length=1, max_length=80)
    bio: Optional[str] = Field(default=None, max_length=500)


class StatusUpdate(BaseModel):
    status: str  # "open" | "busy"


class LocationUpdate(BaseModel):
    lat: float
    lng: float
    visible: bool


# ── Tags ──
class TagAction(BaseModel):
    tagId: str


# ── Connections ──
class ConnectionRequestBody(BaseModel):
    toUserId: str
    introMessage: str = Field(default="", max_length=100)


class ConnectionDecision(BaseModel):
    accepted: bool


# ── Chat ──
class MessageBody(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


# ── Privacy ──
class BlackoutZoneBody(BaseModel):
    label: str = Field(default="Home", max_length=80)
    centerLat: float
    centerLng: float
    radiusMiles: float = Field(default=0.2, gt=0, le=50)


class ScheduleBody(BaseModel):
    shareFrom: str = Field(default="08:00")
    shareUntil: str = Field(default="22:00")
    enabled: bool = False
