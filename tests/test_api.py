from fastapi.testclient import TestClient

from bookshelf.api.app import create_app
from bookshelf.api.dependencies import get_db_session
from bookshelf.services.taxonomy import TaxonomyService
from tests.support import TAXONOMY_PATH


def test_api_health_and_book_flow(session_factory) -> None:
    with session_factory() as session:
        TaxonomyService(session).seed_from_file(TAXONOMY_PATH)

    app = create_app()

    def override_get_db_session():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    client = TestClient(app)

    health_response = client.get("/health")
    categories_response = client.get("/api/v1/categories")
    create_response = client.post(
        "/api/v1/books",
        json={
            "name": "Never Let Me Go",
            "authors": ["Kazuo Ishiguro"],
            "category_slug": "narratives",
            "sub_category_slug": "contemporary-fiction",
            "purchase_urls": ["https://example.com/books/never-let-me-go"],
            "reading_status": "unread",
            "note": "Queued for a first read.",
        },
    )
    unread_response = client.get("/api/v1/books", params={"status": "unread"})
    get_response = client.get(f"/api/v1/books/{create_response.json()['id']}")
    update_response = client.patch(
        f"/api/v1/books/{create_response.json()['id']}",
        json={
            "authors": ["Kazuo Ishiguro", "Guest Editor"],
            "reading_status": "read",
            "clear_note": True,
        },
    )
    filtered_response = client.get(
        "/api/v1/books",
        params={"status": "read", "page": 1, "page_size": 10},
    )
    delete_response = client.delete(f"/api/v1/books/{create_response.json()['id']}")
    missing_response = client.get(f"/api/v1/books/{create_response.json()['id']}")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert categories_response.status_code == 200
    assert any(item["slug"] == "narratives" for item in categories_response.json())
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Never Let Me Go"
    assert create_response.json()["authors"] == ["Kazuo Ishiguro"]
    assert unread_response.status_code == 200
    assert unread_response.json()["items"][0]["name"] == "Never Let Me Go"
    assert unread_response.json()["page"] == 1
    assert get_response.status_code == 200
    assert get_response.json()["id"] == create_response.json()["id"]
    assert get_response.json()["authors"] == ["Kazuo Ishiguro"]
    assert update_response.status_code == 200
    assert update_response.json()["authors"] == ["Kazuo Ishiguro", "Guest Editor"]
    assert update_response.json()["reading_status"] == "read"
    assert update_response.json()["note"] is None
    assert filtered_response.status_code == 200
    assert filtered_response.json()["total_items"] == 1
    assert filtered_response.json()["items"][0]["authors"] == ["Kazuo Ishiguro", "Guest Editor"]
    assert filtered_response.json()["items"][0]["reading_status"] == "read"
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404

    app.dependency_overrides.clear()
