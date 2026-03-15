import argparse
import os
from typing import Dict, List

from datasets import DatasetDict, Features, Value, load_dataset
from huggingface_hub import hf_hub_download
from transformers import (
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5ForConditionalGeneration,
    T5Tokenizer,
)


def _resolve_data_files(repo_id: str) -> Dict[str, str]:
    return {
        "train": hf_hub_download(repo_id=repo_id, repo_type="dataset", filename="train.csv"),
        "validation": hf_hub_download(repo_id=repo_id, repo_type="dataset", filename="valid.csv"),
        "test": hf_hub_download(repo_id=repo_id, repo_type="dataset", filename="test.csv"),
    }


def _clean_text(value) -> str:
    if value is None:
        return ""
    text = str(value)
    if text.lower() == "nan":
        return ""
    return " ".join(text.split()).strip()


def _expand_batch_to_examples(batch: Dict[str, List[str]]) -> Dict[str, List[str]]:
    input_text = []
    target_text = []

    for context_value, question_value, answer1_value, answer2_value in zip(
        batch.get("story_section", []),
        batch.get("question", []),
        batch.get("answer1", []),
        batch.get("answer2", []),
    ):
        context = _clean_text(context_value)
        question = _clean_text(question_value)
        if not context or not question:
            continue

        for answer_value in (answer1_value, answer2_value):
            answer = _clean_text(answer_value)
            if not answer:
                continue

            input_text.append(f"answer_token: {answer} context: {context}")
            target_text.append(question)

    return {"input_text": input_text, "target_text": target_text}


def _build_training_dataset(repo_id: str) -> DatasetDict:
    data_files = _resolve_data_files(repo_id)
    features = Features(
        {
            "story_name": Value("string"),
            "story_section": Value("string"),
            "question": Value("string"),
            "answer1": Value("string"),
            "answer2": Value("string"),
            "local_or_sum": Value("string"),
            "attribute": Value("string"),
            "ex_or_im": Value("string"),
            "ex_or_im2": Value("string"),
        }
    )
    raw = load_dataset("csv", data_files=data_files, features=features)

    expanded = raw.map(_expand_batch_to_examples, batched=True, remove_columns=raw["train"].column_names)

    return expanded


def _tokenize_dataset(dataset: DatasetDict, tokenizer: T5Tokenizer, max_input_length: int, max_target_length: int):
    def _tokenize(batch):
        model_inputs = tokenizer(
            batch["input_text"],
            max_length=max_input_length,
            truncation=True,
            padding=False,
        )
        labels = tokenizer(
            text_target=batch["target_text"],
            max_length=max_target_length,
            truncation=True,
            padding=False,
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    return dataset.map(_tokenize, batched=True, remove_columns=dataset["train"].column_names)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune T5 question generation model on FairytaleQA")
    parser.add_argument("--repo-id", default="WorkInTheDark/FairytaleQA")
    parser.add_argument("--base-model", default="mrm8488/t5-base-finetuned-question-generation-ap")
    parser.add_argument("--output-dir", default="models/qg_finetuned")
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--max-input-length", type=int, default=256)
    parser.add_argument("--max-target-length", type=int, default=64)
    parser.add_argument("--max-steps", type=int, default=-1, help="Set >0 for a quick run")
    parser.add_argument("--eval-steps", type=int, default=200)
    parser.add_argument("--save-steps", type=int, default=200)
    parser.add_argument("--logging-steps", type=int, default=50)
    parser.add_argument("--disable-eval", action="store_true", help="Disable validation/test evaluation for faster CPU training")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("Loading dataset...")
    dataset = _build_training_dataset(args.repo_id)
    print(dataset)

    print(f"Loading tokenizer/model from: {args.base_model}")
    tokenizer = T5Tokenizer.from_pretrained(args.base_model)
    model = T5ForConditionalGeneration.from_pretrained(args.base_model)

    tokenized = _tokenize_dataset(dataset, tokenizer, args.max_input_length, args.max_target_length)

    eval_strategy = "no" if args.disable_eval else "steps"

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        predict_with_generate=False,
        eval_strategy=eval_strategy,
        save_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        save_total_limit=2,
        load_best_model_at_end=not args.disable_eval,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        fp16=False,
        max_steps=args.max_steps,
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        processing_class=tokenizer,
        data_collator=data_collator,
    )

    print("Starting training...")
    train_result = trainer.train()

    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    metrics = train_result.metrics
    train_samples = len(tokenized["train"])
    metrics["train_samples"] = train_samples

    if "train_runtime" in metrics and metrics["train_runtime"] > 0:
        metrics["samples_per_second_effective"] = train_samples / metrics["train_runtime"]

    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    if not args.disable_eval:
        print("Running test split evaluation...")
        test_metrics = trainer.evaluate(tokenized["test"], metric_key_prefix="test")
        trainer.log_metrics("test", test_metrics)
        trainer.save_metrics("test", test_metrics)

    print("Training complete.")
    print(f"Saved fine-tuned model to: {args.output_dir}")


if __name__ == "__main__":
    main()
