from app.text import keywords, relevance, split_sentences


def test_keywords_removes_stopwords_and_duplicates() -> None:
    assert keywords("What is the impact of AI on the AI economy?") == ["impact", "ai", "economy"]


def test_split_sentences_drops_short_fragments() -> None:
    text = "Short one. This sentence is definitely long enough to be kept around. Tiny."
    assert split_sentences(text) == ["This sentence is definitely long enough to be kept around."]


def test_relevance_is_fraction_of_terms() -> None:
    assert relevance("Quantum computers use qubits", ["quantum", "qubits", "cats", "dogs"]) == 0.5
    assert relevance("anything", []) == 0.0
