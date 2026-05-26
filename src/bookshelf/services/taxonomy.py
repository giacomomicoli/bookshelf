from __future__ import annotations

from pathlib import Path

import yaml
from sqlalchemy.orm import Session

from bookshelf.domain.schemas import TaxonomyCategorySchema, TaxonomySeed
from bookshelf.repositories.books import TaxonomyRepository


class TaxonomyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = TaxonomyRepository(session)

    def list_categories(self) -> list[TaxonomyCategorySchema]:
        categories = self.repository.list_categories()
        return [TaxonomyCategorySchema.model_validate(category) for category in categories]

    def seed_from_file(self, path: str | Path) -> int:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        taxonomy = TaxonomySeed.model_validate(payload)

        count = 0
        for category_item in taxonomy.categories:
            category = self.repository.upsert_category(
                slug=category_item.slug,
                name=category_item.name,
            )
            self.repository.replace_subcategories(
                category,
                [(sub.slug, sub.name) for sub in category_item.subcategories],
            )
            count += 1

        self.session.commit()
        return count
