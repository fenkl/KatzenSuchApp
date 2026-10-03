"""Pydantic schemas for KatzenSuchApp API."""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ListingBase(BaseModel):
    url: str
    platform: str
    city: Optional[str] = None
    title: str
    description: Optional[str] = None
    age: Optional[int] = None
    extracted_at: Optional[datetime] = None
    url_hash: str
    processed: int = 0


class ClassificationResponse(BaseModel):
    url_hash: str
    url: Optional[str] = None
    platform: Optional[str] = None
    alter_ok: int
    alter_jahre: Optional[int] = None
    einzelgaenger: int
    freigang_noetig: int
    confidence: float
    reason: Optional[str] = None
    classified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ListingResponse(ListingBase):
    id: Optional[int] = None
    confidence: Optional[float] = None
    alter_ok: Optional[int] = None
    einzelgaenger: Optional[int] = None
    freigang_noetig: Optional[int] = None
    classification: Optional[ClassificationResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PlatformResponse(BaseModel):
    id: Optional[int] = None
    name: str
    base_url: Optional[str] = None
    enabled: int = 1

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    version: str
    db_path: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    active: bool

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None
    access_token: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    group_id: Optional[int] = None


class MarkProcessedRequest(BaseModel):
    url: str
    platform: str


class ScraperConfigBase(BaseModel):
    platform_name: str
    base_url: str = ""
    listing_selector: str = ""
    detail_selector: str = ""
    pagination_param: str = ""
    city_param: str = ""
    enabled: int = 1
    handler_class: str = ""
    login_required: int = 0


class ScraperConfigCreate(ScraperConfigBase):
    pass


class ScraperConfigUpdate(BaseModel):
    base_url: str = ""
    listing_selector: str = ""
    detail_selector: str = ""
    pagination_param: str = ""
    city_param: str = ""
    enabled: int = 1
    handler_class: str = ""
    login_required: int = 0


class ScraperConfigResponse(ScraperConfigBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FeatureRequestBase(BaseModel):
    platform_name: str
    start_url: str
    example_listing_url: str = ""
    description: str = ""
    created_by: str = ""
    status: str = "open"


class FeatureRequestCreate(BaseModel):
    platform_name: str
    start_url: str
    example_listing_url: str = ""
    description: str = ""
    created_by: str = ""


class FeatureRequestUpdate(BaseModel):
    status: Optional[str] = None
    description: Optional[str] = None


class FeatureRequestResponse(FeatureRequestBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

