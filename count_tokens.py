#!/usr/bin/env python3
"""
Count tokens in a file using the DeepSeek V4 Pro tokenizer.
Usage: python count_tokens.py <file_path> [model_name]
"""

import sys
from transformers import AutoTokenizer

def main():
    if len(sys.argv) < 2:
        print("Usage: python count_tokens.py <file_path> [model_name]")
        sys.exit(1)

    file_path = sys.argv[1]
    # Default model name – update this if the actual Hugging Face repo differs
    model_name = sys.argv[2] if len(sys.argv) > 2 else "deepseek-ai/DeepSeek-V4-Pro"

    print(f"Loading tokenizer: {model_name} ...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    token_ids = tokenizer.encode(text)
    print(f"Token count: {len(token_ids)}")

if __name__ == "__main__":
    main()