"""
Shared vector space for both the RAG baseline and the capability-based (LCD)
retriever.

Both retrieval strategies use the *same* fitted TF-IDF vectorizer (same
vocabulary, same IDF weights, same similarity function). The only difference
between them is WHICH text is embedded and compared:

  - RAG:  cosine( TFIDF(problem.statement), TFIDF(card.rag_text()) )
          -- raw natural-language similarity, jargon and all.

  - LCD:  cosine( capability_vector(problem.statement),
                  capability_vector(card.capability_text()) )
          where capability_vector(text) = [ cosine(TFIDF(text), TFIDF(g))
                                             for g in CAPABILITY_GLOSSARY ]
          -- similarity projected through a 45-dim domain-neutral basis.

Holding the vectorizer fixed between the two conditions means any measured
difference is attributable to the *representation* (raw text vs. capability
projection), not to one retriever getting a better embedding model than the
other. That is the controlled variable the experiment is testing.
"""

from __future__ import annotations

from typing import List, Sequence
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .ontology import CAPABILITY_GLOSSARY


class VectorSpace:
    def __init__(self, corpus_texts: Sequence[str]):
        all_texts = list(corpus_texts) + list(CAPABILITY_GLOSSARY)
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        self.vectorizer.fit(all_texts)
        self._glossary_matrix = self.vectorizer.transform(CAPABILITY_GLOSSARY)  # (45, V) sparse

    # ---- raw text space ----
    def text_vector(self, text: str):
        return self.vectorizer.transform([text])

    def text_similarity(self, text_a: str, text_b: str) -> float:
        va = self.text_vector(text_a)
        vb = self.text_vector(text_b)
        return float(cosine_similarity(va, vb)[0][0])

    # ---- capability space (projected through the glossary basis) ----
    def capability_vector(self, text: str) -> np.ndarray:
        v = self.text_vector(text)
        sims = cosine_similarity(v, self._glossary_matrix)[0]
        return sims  # shape (45,)

    def capability_similarity(self, text_a: str, text_b: str) -> float:
        ca = self.capability_vector(text_a)
        cb = self.capability_vector(text_b)
        denom = np.linalg.norm(ca) * np.linalg.norm(cb)
        if denom == 0:
            return 0.0
        return float(np.dot(ca, cb) / denom)

    def top_glossary_axes(self, text: str, k: int = 5):
        """Return the k glossary phrases this text projects onto most strongly.
        Used by the Abstractor / demo trace to show *why* a match was made."""
        cv = self.capability_vector(text)
        idx = np.argsort(-cv)[:k]
        return [(CAPABILITY_GLOSSARY[i], float(cv[i])) for i in idx]


def build_vector_space(cards, problems) -> VectorSpace:
    texts = []
    for c in cards:
        texts.append(c.rag_text())
        texts.append(c.capability_text())
    for p in problems:
        texts.append(p.statement)
    return VectorSpace(texts)
