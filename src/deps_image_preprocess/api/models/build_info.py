from pydantic import BaseModel, ConfigDict, Field


class BuildInfoModel(BaseModel):
    build_tag: str = Field(default="", alias="buildTag")
    build_date: str = Field(default="", alias="buildDate")
    commit_hash: str = Field(default="", alias="commitHash")

    model_config = ConfigDict(populate_by_name=True)
