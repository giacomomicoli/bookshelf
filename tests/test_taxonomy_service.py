from bookshelf.services.taxonomy import TaxonomyService
from tests.support import TAXONOMY_PATH


def test_seed_taxonomy_from_yaml(session) -> None:
    service = TaxonomyService(session)

    seeded_count = service.seed_from_file(TAXONOMY_PATH)
    categories = service.list_categories()

    assert seeded_count == 14
    assert len(categories) == 14
    assert any(category.slug == "essays" for category in categories)
    assert any(category.slug == "science-fiction" for category in categories)
