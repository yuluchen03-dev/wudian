from app.services import classics_service


def test_classics_catalog_has_at_least_100_books():
    books = classics_service.get_books()

    assert len(books) >= 100


def test_classics_catalog_keeps_ids_unique_and_core_books_available():
    books = classics_service.get_books()
    ids = [book["id"] for book in books]
    titles = {book["title"] for book in books}

    assert len(ids) == len(set(ids))
    assert {"论语", "孟子", "大学", "中庸", "道德经", "庄子", "史记"}.issubset(titles)
