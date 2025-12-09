from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from src.application.ports import AbstractTagRepository
from src.domain.models import Tag
from src.infrastructure.persistence.models import TagModel

class SQLAlchemyTagRepository(AbstractTagRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, tag: Tag) -> None:
        model = TagModel(
            id=str(tag.id),
            name=tag.name,
            color=tag.color,
            icon=tag.icon
        )
        self.session.add(model)

    def get(self, tag_id: UUID) -> Optional[Tag]:
        model = self.session.query(TagModel).filter_by(id=str(tag_id)).first()
        if not model: 
            return None
        return self._to_domain(model)

    def list(self) -> List[Tag]:
        models = self.session.query(TagModel).all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: TagModel) -> Tag:
        """
        Método helper (Factory/Mapper) para convertir modelo DB -> Entidad Dominio.
        """
        return Tag(id=UUID(model.id), name=model.name, color=model.color, icon=model.icon)

    def update(self, tag: Tag) -> None:
        model = self.session.query(TagModel).filter_by(id=str(tag.id)).first()
        if model:
            model.name = tag.name
            model.color = tag.color
            model.icon = tag.icon

    def delete(self, tag_id: UUID) -> None:
        self.session.query(TagModel).filter_by(id=str(tag_id)).delete()
