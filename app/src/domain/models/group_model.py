from pydantic import BaseModel

from app.src.domain.models.group_standing import GroupStanding


class GroupTable(BaseModel):
    group: str
    standings: list[GroupStanding]