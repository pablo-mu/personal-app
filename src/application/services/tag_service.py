import uuid
from typing import List
from src.application.dtos import TagDTO
from src.application.ports import AbstractUnitOfWork
from src.domain.models import Tag

class TagService:
    """
    Gestiona la creación y listado de etiquetas.
    """
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    def create_tag(self, dto: TagDTO) -> TagDTO:
        with self.uow:
            new_tag = Tag(
                id=uuid.uuid4(),
                name=dto.name,
                color=dto.color
            )
            self.uow.tags.add(new_tag)
            self.uow.commit()
            
            return TagDTO(id=new_tag.id, name=new_tag.name, color=new_tag.color)

    def list_tags(self) -> List[TagDTO]:
        with self.uow:
            tags = self.uow.tags.list()
            return [
                TagDTO(id=t.id, name=t.name, color=t.color) 
                for t in tags
            ]
