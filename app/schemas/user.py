from pydantic import BaseModel
from typing import Literal

class MasterUser(BaseModel):
    username: str
    role: Literal["master"] = "master"