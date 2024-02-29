from enum import Enum
from pydantic import BaseModel


class Detection:
    drawing_types: list | None
    file_name: str
    cardinal_direction: str | None
    scale: str | None
    room_names: str | None
    #plantegning: bool
    #snitt: bool
    #situasjonskart: bool
    #fasade: bool
