from enum import Enum
from pydantic import BaseModel


class Status(Enum):
    success = 'success'
    warning = 'warning'
    error = 'error'


class Feedback(BaseModel):
    status: Status
    message: str


class Detection(BaseModel):
    type: Feedback | None = None
    sky_direction: Feedback | None = None
