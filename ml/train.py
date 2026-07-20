import argparse
import os

from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from .data_prep import prepare


def compute_metrics(eval_pred):
    preds, labels = eval_pred
    preds = preds.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, zero_division=0)
    return {"accuracy": acc, "f1": f1}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT on EMSCAD")
    parser.add_argument("--data", default="data/raw/emscad.csv")
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--output-dir", default="artifacts/model")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    train_df, val_df = prepare(args.data, seed=args.seed)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch):
        return tokenizer(
            batch["text"], truncation=True, padding="max_length", max_length=args.max_length
        )

    train_ds = (
        Dataset.from_pandas(train_df[["text", "fraudulent"]])
        .map(tokenize, batched=True)
        .rename_column("fraudulent", "labels")
    )
    val_ds = (
        Dataset.from_pandas(val_df[["text", "fraudulent"]])
        .map(tokenize, batched=True)
        .rename_column("fraudulent", "labels")
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name, num_labels=2
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_dir=os.path.join(args.output_dir, "logs"),
        seed=args.seed,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    metrics = trainer.evaluate()
    print("Eval:", metrics)
    print(f"Best model saved to {args.output_dir}")


if __name__ == "__main__":
    main()
