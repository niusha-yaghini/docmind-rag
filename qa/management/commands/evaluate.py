"""Measure retrieval quality (no LLM involved):  python manage.py evaluate

Loads the evaluation corpus (eval/corpus.json) as temporary documents, runs every question in eval/questions.json
through four retrieval strategies and prints hit rate@k and MRR for each. The temporary documents are removed
afterwards (pass --keep to leave them in the index).
"""
import json
import logging
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test.utils import override_settings

from documents.models import Chunk, Document
from documents.services import ingest as ingest_module
from documents.services.ingest import process_document, split_text
from qa.evaluation import first_hit_rank, score
from qa.retriever import HybridRetriever, reciprocal_rank_fusion

PREFIX = "[eval] "
STRATEGIES = ["vector only", "keyword only", "hybrid (RRF)", "hybrid + rerank"]


class Command(BaseCommand):
    help = "Evaluate retrieval (hit rate@k, MRR) with and without hybrid search and reranking."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--keep", action="store_true", help="Keep the evaluation documents in the index.")
        parser.add_argument("--verbose", action="store_true", help="Show the rank of the right chunk for every question.")
        parser.add_argument("--k", type=int, default=5, help="Chunks retrieved per question (default 5).")

    def handle(self, *args, **options) -> None:
        folder = Path(settings.BASE_DIR) / "eval"
        try:
            corpus = json.loads((folder / "corpus.json").read_text(encoding="utf-8"))
            questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CommandError(f"Missing evaluation data: {exc.filename}") from exc

        logging.getLogger("httpx").setLevel(logging.WARNING)  # one log line per API call drowns the output
        Document.objects.filter(title__startswith=PREFIX).delete()  # leftovers of an interrupted run
        lookup = self._embed_everything(corpus, questions)
        # Everything is embedded already: indexing and searching below read from `lookup` and make no API calls.
        with (
            mock.patch.object(ingest_module, "embed_texts", lambda texts: [lookup[t] for t in texts]),
            mock.patch("qa.retriever.embed_query", lambda text: lookup[text]),
        ):
            try:
                ids = self._load_corpus(corpus)
                results = self._run(questions, ids, options["k"])
            finally:
                if not options["keep"]:  # also removes half-indexed documents when something failed midway
                    Document.objects.filter(title__startswith=PREFIX).delete()
        self._report(questions, results, options["k"], verbose=options["verbose"])

    def _embed_everything(self, corpus: list[dict], questions: list[dict]) -> dict[str, list[float]]:
        """Embed all chunks and all questions in ONE request. Free OpenRouter models allow only a few dozen
        requests a day, so one request per document or per question would use the quota up."""
        texts = list(dict.fromkeys(
            [piece for item in corpus for piece in split_text(item["text"])] + [q["question"] for q in questions]
        ))
        try:
            vectors = ingest_module.embed_texts(texts)
        except Exception as exc:
            raise CommandError(
                f"Embedding failed: {exc}\nIf this is a 429 rate limit, the daily quota of the free embedding model "
                "is used up: try again after it resets, or add credits on OpenRouter."
            ) from exc
        self.stdout.write(f"Embedded {len(texts)} texts in one request.")
        return dict(zip(texts, vectors))

    def _load_corpus(self, corpus: list[dict]) -> list[int]:
        ids = []
        for item in corpus:
            document = process_document(Document.objects.create(title=PREFIX + item["title"], full_text=item["text"]))
            if document.status != Document.Status.INDEXED:
                raise CommandError(f"Could not index '{item['title']}': {document.error}")
            ids.append(document.pk)
        self.stdout.write(f"Indexed {len(ids)} evaluation documents ({Chunk.objects.filter(document_id__in=ids).count()} chunks).")
        return ids

    def _run(self, questions: list[dict], ids: list[int], k: int) -> dict[str, list[int | None]]:
        """ranks[strategy][i] = rank of the right chunk for question i (None = not in the top k)."""
        from qa import retriever as retriever_module

        ranks: dict[str, list[int | None]] = {name: [] for name in STRATEGIES}
        self.rerank_ran = True
        retriever = HybridRetriever(k=k, document_ids=ids)
        for number, item in enumerate(questions, start=1):
            text, expect = item["question"], item["expect"]
            self.stdout.write(f"\rquestion {number}/{len(questions)}", ending="")
            vector_ids = retriever._vector_ids(retriever_module.embed_query(text))
            keyword_ids = retriever._fts_ids(text)
            fused_ids = [i for i, _ in reciprocal_rank_fusion([vector_ids, keyword_ids], k=settings.RRF_K)]
            for name, chunk_ids in (
                ("vector only", vector_ids[:k]),
                ("keyword only", keyword_ids[:k]),
                ("hybrid (RRF)", fused_ids[:k]),
            ):
                ranks[name].append(first_hit_rank(self._contents(chunk_ids), expect))
            with override_settings(RERANK_ENABLED=True):
                docs = retriever.invoke(text)
            self.rerank_ran &= all("rerank_score" in doc.metadata for doc in docs)
            ranks["hybrid + rerank"].append(first_hit_rank([doc.page_content for doc in docs], expect))
        self.stdout.write("")
        return ranks

    @staticmethod
    def _contents(chunk_ids: list[int]) -> list[str]:
        by_id = Chunk.objects.in_bulk(chunk_ids)
        return [by_id[i].content for i in chunk_ids]

    def _report(self, questions: list[dict], ranks: dict[str, list[int | None]], k: int, *, verbose: bool) -> None:
        width = max(len(name) for name in STRATEGIES)
        self.stdout.write(f"\nRetrieval quality on {len(questions)} questions (top {k} chunks per question)\n")
        self.stdout.write(f"{'strategy':<{width}}  hit@1   hit@3   hit@5    MRR")
        for name in STRATEGIES:
            s = score(ranks[name])
            self.stdout.write(f"{name:<{width}}  {s.hit_at_1:5.0%}   {s.hit_at_3:5.0%}   {s.hit_at_5:5.0%}   {s.mrr:5.3f}")
        if not self.rerank_ran:
            self.stdout.write(self.style.WARNING(
                "\nWARNING: the reranker model was unavailable, so 'hybrid + rerank' is just the hybrid order."
            ))
        if verbose:
            self.stdout.write("\nRank of the right chunk per question ('-' = not retrieved):")
            self.stdout.write(f"{'#':>2}  " + "  ".join(f"{n[:12]:>12}" for n in STRATEGIES) + "  question")
            for i, item in enumerate(questions):
                cells = "  ".join(f"{(ranks[n][i] or '-')!s:>12}" for n in STRATEGIES)
                self.stdout.write(f"{i + 1:>2}  {cells}  {item['question']}")
