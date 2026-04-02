import uuid
from typing import List
 
from src.application.dtos import TagDTO
from src.application.ports import AbstractUnitOfWork
from src.domain.exceptions import TagAlreadyExistsError, TagNotFoundError
from src.domain.models import Tag
 
class TagService:
    """
    Gestiona la creación y listado de etiquetas.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def create_tag(self, dto: TagDTO) -> TagDTO:
        with self.uow:
            existing = self.uow.tags.get_by_name(dto.name)
            if existing:
                raise TagAlreadyExistsError(dto.name)
 
            new_tag = Tag(id=uuid.uuid4(), name=dto.name, color=dto.color)
            self.uow.tags.add(new_tag)
            self.uow.commit()
            return TagDTO(id=new_tag.id, name=new_tag.name, color=new_tag.color)
 
    def list_tags(self) -> List[TagDTO]:
        with self.uow:
            tags = self.uow.tags.list()
            return [TagDTO(id=t.id, name=t.name, color=t.color) for t in tags]
 
    def delete_tag(self, tag_id: uuid.UUID) -> None:
        with self.uow:
            tag = self.uow.tags.get(tag_id)
            if not tag:
                raise TagNotFoundError(tag_id)
            self.uow.tags.delete(tag_id)
            self.uow.commit()