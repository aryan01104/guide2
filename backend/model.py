#!/usr/bin/env python3
"""
productivity_score_model.py

Provides two core functions:
  - train_model_db: train a transformer regressor on DB data.
  - classify_string: score a single text using saved weights.

Parameters:
  - db_url (str): SQLAlchemy connection string to your database. Examples:
      • SQLite: "sqlite:///path/to/db.sqlite"
      • PostgreSQL: "postgresql://user:pass@host:port/dbname"
  - output_dir (str): local folder where the model weights and tokenizer are saved.
    After training, this directory will contain files like `pytorch_model.bin` and `tokenizer.json`.

Usage example in Python:
```python
from productivity_score_model import train_model_db, classify_string

# Train from database:
train_model_db(
    db_url="sqlite:///mydb.sqlite",
    output_dir="out_dir"
)

# Infer later:
score = classify_string(
    "Worked on Jupyter notebook…",
    "out_dir"
)
print(score)
```

Dependencies:
  pip install torch transformers datasets scikit-learn pandas sqlalchemy
"""

import os
import torch
import pandas as pd
from sqlalchemy import create_engine
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import mean_squared_error, mean_absolute_error

db_url = "sqlite:///data/activity.db"


def load_data_from_db(db_url: str,
                      table_name: str = "activity_logs") -> Dataset:
    """
    Load 'details' and 'productivity_score' columns from the DB table,
    drop rows without a score, and return a Hugging Face Dataset.
    """
    engine = create_engine(db_url)
    df = pd.read_sql_table(table_name, con=engine)
    df = df.dropna(subset=["details", "productivity_score"])
    df = df.rename(columns={
        "details": "text",
        "productivity_score": "label"
    })[["text", "label"]]
    return Dataset.from_pandas(df)


def compute_metrics(eval_pred):
    labels = eval_pred.label_ids
    preds = eval_pred.predictions.squeeze()
    return {
        "mse": mean_squared_error(labels, preds),
        "mae": mean_absolute_error(labels, preds),
    }


def train_model_db(
    db_url: str,
    output_dir: str,
    model_name: str = "distilbert-base-uncased",
    epochs: int = 3,
    batch_size: int = 8,
    lr: float = 2e-5,
    table_name: str = "activity_logs"
):
    """
    Train a transformer regressor on DB entries from table_name.
    Saves tokenizer and model weights to output_dir.
    """
    # 1. Load and prepare dataset
    ds = load_data_from_db(db_url, table_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    ds = ds.map(
        lambda batch: tokenizer(
            batch["text"],
            padding="max_length",
            truncation=True,
            max_length=200
        ),
        batched=True
    )
    ds = ds.remove_columns(["text"])
    ds.set_format(type="torch", columns=["input_ids", "attention_mask", "label"])

    # 2. Split
    split = ds.train_test_split(test_size=0.1, seed=42)
    train_ds, eval_ds = split["train"], split["test"]

    # 3. Model setup
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1)
    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=lr,
        evaluation_strategy="epoch",
        save_strategy="epoch"
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        compute_metrics=compute_metrics
    )

    # 4. Train & save
    trainer.train()
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)


def classify_string(
    text: str,
    model_dir: str
) -> float:
    """
    Load saved model/tokenizer from model_dir and return productivity score for text.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=200,
        padding="max_length"
    )
    with torch.no_grad():
        logits = model(**inputs).logits.squeeze().item()

    return float(max(-50, min(50, logits)))


train_model_db(
    db_url= db_url,
    output_dir= "/resources/prod_model",
    model_name = "distilbert-base-uncased",
    epochs =  3,
    batch_size = 8,
    lr = 2e-5,
    table_name = "activity_logs"
)