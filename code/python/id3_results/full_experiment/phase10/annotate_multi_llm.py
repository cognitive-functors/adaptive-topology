#!/usr/bin/env python3
"""
Multi-LLM Annotation Script for ID-3 Experiment.
Annotates texts using multiple LLM providers for inter-rater reliability.

Usage:
    export OPENAI_API_KEY="..."
    export ANTHROPIC_API_KEY="..."
    export DEEPSEEK_API_KEY="..."
    python3 annotate_multi_llm.py
"""
import json, os, time, sys
from pathlib import Path

MODELS = {
    "gpt4o": {"provider": "openai", "model": "gpt-4o", "env": "OPENAI_API_KEY"},
    "claude": {"provider": "anthropic", "model": "claude-sonnet-4-20250514", "env": "ANTHROPIC_API_KEY"},
    "deepseek": {"provider": "openai_compat", "model": "deepseek-chat",
                 "env": "DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com"},
}

PROMPT = open("annotation_prompt.txt").read()

def annotate_openai(text: str, model: str, api_key: str, base_url: str = None) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": PROMPT + text}],
        temperature=0, max_tokens=50,
    )
    return json.loads(resp.choices[0].message.content.strip())

def annotate_anthropic(text: str, model: str, api_key: str) -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=50,
        messages=[{"role": "user", "content": PROMPT + text}],
    )
    return json.loads(resp.content[0].text.strip())

def main():
    texts = [json.loads(l) for l in open("texts_for_annotation.jsonl")]
    results = {m: [] for m in MODELS}

    for model_name, cfg in MODELS.items():
        api_key = os.environ.get(cfg["env"])
        if not api_key:
            print(f"SKIP {model_name}: {cfg['env']} not set")
            continue
        print(f"Annotating with {model_name} ({len(texts)} texts)...")
        for item in texts:
            try:
                if cfg["provider"] == "anthropic":
                    label = annotate_anthropic(item["text"], cfg["model"], api_key)
                else:
                    label = annotate_openai(item["text"], cfg["model"], api_key,
                                           cfg.get("base_url"))
                results[model_name].append({"id": item["id"], **label})
                time.sleep(0.5)  # rate limit
            except Exception as e:
                results[model_name].append({"id": item["id"], "error": str(e)})

        with open(f"annotations_{model_name}.jsonl", "w") as f:
            for r in results[model_name]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  Done: {model_name}")

    # Compute agreement
    print("\nInter-rater agreement:")
    valid_models = [m for m in results if results[m] and "error" not in results[m][0]]
    if len(valid_models) >= 2:
        for axis in ["t", "d", "a"]:
            agreements = []
            for i in range(len(texts)):
                vals = []
                for m in valid_models:
                    if i < len(results[m]) and "error" not in results[m][i]:
                        vals.append(results[m][i].get(axis))
                if len(vals) >= 2:
                    agreements.append(len(set(vals)) == 1)
            pct = sum(agreements) / len(agreements) * 100 if agreements else 0
            print(f"  {axis.upper()}: {pct:.1f}% exact agreement")

if __name__ == "__main__":
    main()
