from app.services.chunking import PageContent, split_pages_into_chunks


def test_split_pages_into_chunks_preserves_page_numbers() -> None:
    pages = [
        PageContent(text="Alpha beta gamma delta epsilon " * 30, page_number=1),
        PageContent(text="Zeta eta theta iota kappa " * 30, page_number=2),
    ]

    chunks = split_pages_into_chunks(pages, chunk_size=90, chunk_overlap=10)

    assert len(chunks) > 2
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2
    assert all(chunk.content for chunk in chunks)