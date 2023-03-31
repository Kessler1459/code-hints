from pydantic import BaseModel


class Call(BaseModel):
    id: str
    path_: str
    line_number: int
    file_name: str
    url: str

class Message(BaseModel):
    message: str
