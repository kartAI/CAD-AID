from enum import Enum
from pydantic import BaseModel


class Detection:
    plantegning: bool
    snitt: bool
    situasjonskart: bool
    fasade: bool

