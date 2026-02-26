import os

import joblib
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from oceanofpdf_downloader.models import Book, BookState
from oceanofpdf_downloader.repository import BookRepository

MODEL_VERSION = 1
MIN_SAMPLES_PER_CLASS = 3


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

    texts = [self._book_to_text(b) for b in positives] + [self._book_to_text(b) for b in negatives]
    labels = [1] * len(positives) + [0] * len(negatives)

    pipeline = Pipeline([
      ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
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

  def predict(self, book: Book) -> bool:
    if self._pipeline is None:
      raise RuntimeError("Model not loaded — call load() or train() first")
    text = self._book_to_text(book)
    prob = self._pipeline.predict_proba([text])[0][1]
    return float(prob) >= self.config.ml_confidence_threshold
