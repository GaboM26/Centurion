"""Base model helpers."""

from pydantic import BaseModel, ConfigDict


class CenturionBaseModel(BaseModel):
    """Base model that tolerates extra fields from the API."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)
