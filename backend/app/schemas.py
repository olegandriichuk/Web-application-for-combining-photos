from pydantic import BaseModel

class ItemBase(BaseModel):
    title: str
    description: str = ""

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

class ItemRead(ItemBase):
    id: int
    class Config:
        from_attributes = True
