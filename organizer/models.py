from pydantic import BaseModel, Field
from typing import List, Optional


class FlatFileItem(BaseModel):
    path: str = Field(
        description="Full path of the file or folder. Folders end with '/', files do not. "
        "Example: 'src/utils/math.go' (file), 'src/utils/' (folder)"
    )
    hash: Optional[str] = Field(
        default=None,
        description="MD5 or other hash of file contents. Present only for files.",
    )
    size: Optional[int] = Field(
        default=None, description="Size of the file in bytes. Present only for files."
    )


class OrganizationStrategy(BaseModel):
    name: str = Field(
        description="The organization strategy used for the items, e.g., 'by_name'."
    )
    items: List[FlatFileItem]


class LLMResponseSchema(BaseModel):
    strategies: List[OrganizationStrategy]
