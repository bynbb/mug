"""Documents.Application.Documents.AddDocument: command DTO."""

from pydantic import BaseModel


class AddDocumentCommand(BaseModel):
    title: str
    body: str | None = None