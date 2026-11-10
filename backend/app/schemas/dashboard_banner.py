from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DashboardBannerLocale = Literal[
    "es", "ast"
]


class DashboardBannerTranslation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=160)
    subtitle: str = Field(max_length=240)
    description: str = Field(max_length=2000)

    @field_validator("title", "subtitle", "description")
    @classmethod
    def strip_nonblank_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Banner text must not be blank")
        return value


class DashboardBannerStoredTranslations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    es: DashboardBannerTranslation
    ast: DashboardBannerTranslation


class DashboardBannerTranslations(DashboardBannerStoredTranslations):
    pass


class DashboardBannerTranslateRequest(DashboardBannerTranslation):
    source_locale: DashboardBannerLocale


class DashboardBannerTranslationResponse(BaseModel):
    translations: DashboardBannerTranslations


class DashboardBannerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_locale: DashboardBannerLocale
    is_active: bool
    translations: DashboardBannerTranslations


class DashboardBannerPublicResponse(BaseModel):
    revision: int
    translations: DashboardBannerStoredTranslations


class DashboardBannerAdminResponse(DashboardBannerPublicResponse):
    source_locale: DashboardBannerLocale
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardBannerDismissRequest(BaseModel):
    revision: int = Field(ge=1)
