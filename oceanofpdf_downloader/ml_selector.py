import os

import joblib
from loguru import logger
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository

MODEL_VERSION = 2
MIN_SAMPLES_PER_CLASS = 3


class SentenceTransformerEmbedder(BaseEstimator, TransformerMixin):
  """Thin sklearn-compatible wrapper around a sentence-transformers model.

  The underlying transformer is loaded lazily and excluded from pickling so
  that joblib only serialises the model name and the fitted classifier weights,
  not the full transformer checkpoint.
  """

  def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
    self.model_name = model_name
    self._model = None

  def _load(self):
    if self._model is None:
      from sentence_transformers import SentenceTransformer
      logger.info("Loading sentence transformer model '{}'", self.model_name)
      self._model = SentenceTransformer(self.model_name)
    return self._model

  def fit(self, X, y=None):
    self._load()
    return self

  def transform(self, X):
    return self._load().encode(list(X), show_progress_bar=False)

  def __getstate__(self):
    state = self.__dict__.copy()
    state["_model"] = None  # don't pickle transformer weights
    return state


class MLSelector:
  def __init__(self, config) -> None:
    self.config = config
    self._pipeline = None

  def _book_to_text(self, book) -> str:
    return f"{book.title} {book.genre} {book.language}"

  def train(self, repo: BookRepository) -> None:
    positives = repo.get_books_by_state(BookState.DONE)
    negatives = (
      repo.get_books_by_state(BookState.SKIPPED)
      + repo.get_books_by_state(BookState.BLACKLISTED)
    )

    if len(positives) < MIN_SAMPLES_PER_CLASS:
      raise ValueError(
        f"Need at least {MIN_SAMPLES_PER_CLASS} DONE books, got {len(positives)}"
      )
    if len(negatives) < MIN_SAMPLES_PER_CLASS:
      raise ValueError(
        f"Need at least {MIN_SAMPLES_PER_CLASS} SKIPPED/BLACKLISTED books, got {len(negatives)}"
      )

    extra_negative_titles = self._load_negative_examples()
    if extra_negative_titles:
      logger.info("Loaded {} extra negative example(s) from {}", len(extra_negative_titles), self.config.ml_negative_examples_path)

    extra_positive_titles = self._load_positive_examples()
    if extra_positive_titles:
      logger.info("Loaded {} extra positive example(s) from {}", len(extra_positive_titles), self.config.ml_positive_examples_path)

    # Negatives file overrides DONE books (wrongly auto-selected).
    if extra_negative_titles:
      neg_titles_lower = {t.lower() for t in extra_negative_titles}
      conflicting = [b for b in positives if b.title.lower() in neg_titles_lower]
      if conflicting:
        logger.warning(
          "{} DONE book(s) overridden as negative by ml_negatives.txt: {}",
          len(conflicting), [b.title for b in conflicting],
        )
        positives = [b for b in positives if b.title.lower() not in neg_titles_lower]

    # Positives file overrides SKIPPED/BLACKLISTED books (wrongly dismissed).
    if extra_positive_titles:
      pos_titles_lower = {t.lower() for t in extra_positive_titles}
      conflicting = [b for b in negatives if b.title.lower() in pos_titles_lower]
      if conflicting:
        logger.warning(
          "{} SKIPPED/BLACKLISTED book(s) overridden as positive by ml_positives.txt: {}",
          len(conflicting), [b.title for b in conflicting],
        )
        negatives = [b for b in negatives if b.title.lower() not in pos_titles_lower]

    extra_negative_texts = [f"{t} Unknown Unknown" for t in extra_negative_titles]
    extra_positive_texts = [f"{t} Unknown Unknown" for t in extra_positive_titles]
    texts = (
      [self._book_to_text(b) for b in positives]
      + extra_positive_texts
      + [self._book_to_text(b) for b in negatives]
      + extra_negative_texts
    )
    labels = (
      [1] * (len(positives) + len(extra_positive_texts))
      + [0] * (len(negatives) + len(extra_negative_texts))
    )

    pipeline = Pipeline([
      ("embed", SentenceTransformerEmbedder(self.config.ml_sentence_transformer_model)),
      ("clf", LogisticRegression(class_weight="balanced", max_iter=1000)),
    ])
    pipeline.fit(texts, labels)

    model_dir = os.path.dirname(self.config.ml_model_path)
    if model_dir:
      os.makedirs(model_dir, exist_ok=True)
    joblib.dump({"version": MODEL_VERSION, "pipeline": pipeline}, self.config.ml_model_path)
    self._pipeline = pipeline
    logger.info(
      "ML model trained: {} positive, {} negative — saved to {}",
      len(positives), len(negatives), self.config.ml_model_path,
    )

  def load(self) -> bool:
    if not os.path.exists(self.config.ml_model_path):
      return False
    data = joblib.load(self.config.ml_model_path)
    if data.get("version") != MODEL_VERSION:
      logger.warning(
        "ML model version mismatch (got {}, expected {}) — retrain with --train",
        data.get("version"), MODEL_VERSION,
      )
      return False
    self._pipeline = data["pipeline"]
    return True

  def _load_negative_examples(self) -> list[str]:
    """Returns raw title strings from the negatives file (comments and blank lines excluded)."""
    return self._load_examples_file(self.config.ml_negative_examples_path)

  def _load_positive_examples(self) -> list[str]:
    """Returns raw title strings from the positives file (comments and blank lines excluded)."""
    return self._load_examples_file(self.config.ml_positive_examples_path)

  def _load_examples_file(self, path: str) -> list[str]:
    if not path or not os.path.exists(path):
      return []
    titles = []
    with open(path, encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
          titles.append(line)
    return titles

  def predict(self, book: Book) -> bool:
    if self._pipeline is None:
      raise RuntimeError("Model not loaded — call load() or train() first")
    text = self._book_to_text(book)
    prob = self._pipeline.predict_proba([text])[0][1]
    return float(prob) >= self.config.ml_confidence_threshold

  def score(self, book: Book) -> float:
    """Return raw P(positive) without applying the threshold."""
    if self._pipeline is None:
      raise RuntimeError("Model not loaded — call load() or train() first")
    text = self._book_to_text(book)
    return float(self._pipeline.predict_proba([text])[0][1])
