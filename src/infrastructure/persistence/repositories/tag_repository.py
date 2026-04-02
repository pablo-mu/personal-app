from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.application.ports import AbstractTagRepository
from src.domain.models import Tag
from src.infrastructure.persistence.models import TagModel


class SQLAlchemyTagRepository(AbstractTagRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: TagModel) -> Tag:
        return Tag(id=UUID(model.id), name=model.name, color=model.color)

    def add(self, tag: Tag) -> None:
        self.session.add(TagModel(id=str(tag.id), name=tag.name, color=tag.color))

    def get(self, tag_id: UUID) -> Optional[Tag]:
        model = self.session.query(TagModel).filter_by(id=str(tag_id)).first()
        return self._to_domain(model) if model else None

    def get_by_name(self, name: str) -> Optional[Tag]:
        model = self.session.query(TagModel).filter(
            TagModel.name.ilike(name)
        ).first()
        return self._to_domain(model) if model else None

    def list(self) -> List[Tag]:
        return [self._to_domain(m) for m in self.session.query(TagModel).order_by(TagModel.name).all()]

    def update(self, tag: Tag) -> None:
        model = self.session.query(TagModel).filter_by(id=str(tag.id)).first()
        if model:
            model.name  = tag.name
            model.color = tag.color

    def delete(self, tag_id: UUID) -> None:
        self.session.query(TagModel).filter_by(id=str(tag_id)).delete()