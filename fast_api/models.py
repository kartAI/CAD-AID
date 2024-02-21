from enum import Enum
from pydantic import BaseModel


class Status(Enum):
    success = 'success'
    warning = 'warning'
    error = 'error'


class Feedback(BaseModel):
    status: Status
    message: str


class Detection:
    plantegning: bool
    snitt: bool
    situasjonskart: bool
    fasade: bool


class Validation(BaseModel):
    sky_direction: Feedback | None = None
    scale: Feedback | None = None
