"""Retrieval evaluation: did the passage that holds the answer come back, and how high?

A question is "answered" by a chunk when the chunk contains the question's `expect` phrase (case-insensitive).
Matching on text instead of chunk ids keeps the evaluation valid when the chunk size changes.
"""
from dataclasses import dataclass


def first_hit_rank(contents: list[str], expect: str) -> int | None:
    """1-based position of the first retrieved chunk that contains `expect`, or None."""
    needle = expect.lower()
    for rank, content in enumerate(contents, start=1):
        if needle in content.lower():
            return rank
    return None


@dataclass(frozen=True)
class Scores:
    questions: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float


def score(ranks: list[int | None]) -> Scores:
    """Hit rate@k = share of questions whose right chunk is in the top k.
    MRR = mean of 1/rank (0 when the chunk was not retrieved at all)."""
    n = len(ranks)
    if n == 0:
        return Scores(0, 0.0, 0.0, 0.0, 0.0)

    def hit(k: int) -> float:
        return sum(1 for r in ranks if r is not None and r <= k) / n

    return Scores(n, hit(1), hit(3), hit(5), sum(1 / r for r in ranks if r) / n)
