from dataclasses import dataclass
from typing import Optional

from deps_message_flow.commands.common import Command

__all__ = [
    "PreprocessReferencePage",
    "PreprocessReferencePageReply",
    "DeleteFiles",
    "PerformPreprocess",
    "PerformPreprocessReply",
]

from deps_message_flow.events.common import DomainEvent


@dataclass
class PreprocessReferencePage(Command):
    template_id: str
    blob_names: list[str]


@dataclass
class PreprocessReferencePageReply(Command):
    template_id: str
    blob_names: list[str]


@dataclass
class DeleteFiles(DomainEvent):
    file_paths: list[str]


@dataclass
class PerformPreprocess(Command):
    document_id: int
    image_transformations: Optional[list[str]] = None


@dataclass
class PerformPreprocessReply(Command):
    document_id: int
    error_type: Optional[str] = None
    error_message: Optional[str] = None
