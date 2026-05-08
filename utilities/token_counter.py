#!/usr/bin/env python3
"""
Token counter utility for transcripts and prompts.
Handles request assembly, token counting, and optional LLM submission.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utilities.llm_summarizer import LLMSummarizer, LLMSummarizerBuilder
from utilities.prompt_builder import PromptBuildStrategyFactory


def load_prompt(prompt_type: str, prompt_value: str) -> str:
    """
    Load a prompt from a file or use it as a string.

    Args:
        prompt_type: 'string', 'str', 'directory', or 'dir'
        prompt_value: The prompt string or directory path

    Returns:
        The assembled prompt string
    """
    strategy = PromptBuildStrategyFactory.get_transcription_strategy(prompt_type)
    return strategy.build(prompt_value)


def count_tokens_in_file(
    file_path: str,
    summarization_prompt: str,
    transcription_prompt: str = None,
    tokenizer_model: str = None,
    verbose: bool = False,
) -> int:
    """
    Count tokens in a transcript file with the full summarization context.

    Args:
        file_path: Path to the transcript file
        summarization_prompt: Fully assembled summarization prompt
        transcription_prompt: Optional transcription prompt
        tokenizer_model: Model to use for token counting
        verbose: Whether to print verbose output

    Returns:
        Number of tokens
    """
    with open(file_path, "r", encoding="utf-8") as f:
        transcript_content = f.read()

    builder = LLMSummarizerBuilder()
    if tokenizer_model:
        builder.with_tokenizer_model(tokenizer_model)
    if verbose:
        builder.with_verbosity(True)

    # For token counting only, we don't need API config
    # Set dummy values to pass validation
    builder.with_api_endpoint("https://api.openrouter.ai/api/v1")
    builder.with_api_key("dummy-key-for-token-counting-only")

    summarizer = builder.build()

    # Build context by combining prompts with transcript
    parts = []
    if summarization_prompt:
        parts.append(summarization_prompt.strip())
        parts.append("")

    if transcription_prompt:
        parts.append(transcription_prompt.strip())
        parts.append("")

    parts.append(transcript_content.strip())
    context = "\n".join(parts)

    token_count = summarizer.count_tokens(context)

    if verbose or token_count >= 0:
        print(f"Transcript file: {file_path}")
        print(f"Transcript size: {len(transcript_content)} characters")
        print(f"Context size: {len(context)} characters")
        print(f"Token count: {token_count}")

    return token_count


def main():
    parser = argparse.ArgumentParser(
        description="Count tokens in a transcript and optionally submit for summarization."
    )
    parser.add_argument(
        "transcript",
        help="Path to the transcript file (dense format recommended)",
    )
    parser.add_argument(
        "--summarization-prefix",
        "-sp",
        help="Path to summarization prefix file or the prefix string",
        default="prompt/summarization/prefix",
    )
    parser.add_argument(
        "--summarization-suffix",
        "-ss",
        help="Path to summarization suffix file or the suffix string",
        default="prompt/summarization/suffix",
    )
    parser.add_argument(
        "--transcription-prompt",
        "-tp",
        help="Path to transcription prompt directory or the prompt string",
    )
    parser.add_argument(
        "--transcription-prompt-type",
        "-tpt",
        choices=["string", "str", "directory", "dir"],
        default="directory",
        help="Type of transcription prompt (default: directory)",
    )
    parser.add_argument(
        "--summarization-prefix-type",
        "-spt",
        choices=["string", "str", "directory", "dir"],
        default="directory",
        help="Type of summarization prefix (default: directory)",
    )
    parser.add_argument(
        "--summarization-suffix-type",
        "-sst",
        choices=["string", "str", "directory", "dir"],
        default="directory",
        help="Type of summarization suffix (default: directory)",
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Model architecture for tokenization",
        default="nvidia/nemotron-3-super-120b-a12b:free",
    )
    parser.add_argument(
        "--api-endpoint",
        "-e",
        help="LLM API endpoint (if submitting for summarization)",
    )
    parser.add_argument(
        "--api-key",
        "-k",
        help="LLM API key (if submitting for summarization)",
    )
    parser.add_argument(
        "--submit",
        "-s",
        action="store_true",
        help="Submit for summarization (not just count tokens)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for the summary markdown file",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation before sending request",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    # Load prompts
    if os.path.exists(args.summarization_prefix):
        prefix_type = args.summarization_prefix_type
        prefix_value = args.summarization_prefix
    else:
        prefix_type = "string"
        prefix_value = args.summarization_prefix

    if os.path.exists(args.summarization_suffix):
        suffix_type = args.summarization_suffix_type
        suffix_value = args.summarization_suffix
    else:
        suffix_type = "string"
        suffix_value = args.summarization_suffix

    prefix = load_prompt(prefix_type, prefix_value)
    suffix = load_prompt(suffix_type, suffix_value)

    # Combine prefix and suffix into a single summarization prompt
    summarization_prompt = "\n".join([prefix, "", suffix]).strip()

    transcription_prompt = None
    if args.transcription_prompt:
        transcription_prompt = load_prompt(
            args.transcription_prompt_type, args.transcription_prompt
        )

    # Just count tokens
    token_count = count_tokens_in_file(
        args.transcript,
        summarization_prompt,
        transcription_prompt,
        tokenizer_model=args.model,
        verbose=args.verbose,
    )

    if token_count < 0:
        print("Warning: Could not count tokens.", file=sys.stderr)

    # Submit for summarization if requested
    if args.submit:
        builder = LLMSummarizerBuilder()
        if args.api_endpoint:
            builder.with_api_endpoint(args.api_endpoint)
        if args.api_key:
            builder.with_api_key(args.api_key)
        builder.with_model(args.model)
        builder.with_verbosity(args.verbose)
        builder.with_assembled_summarization_prompt(summarization_prompt)
        builder.with_assembled_transcription_prompt(transcription_prompt)

        summarizer = builder.build()

        result = summarizer.summarize(
            transcript_path=args.transcript,
        )

        if result["success"]:
            print(f"\n[SUCCESS] Summary generated!")
            print(f"\n{result['summary']}")

            # Save to file
            if args.output:
                summarizer.save_summary_markdown(
                    result["summary"],
                    args.output,
                    args.transcript,
                    result.get("usage"),
                )
            else:
                # Auto-generate output path
                transcript_name = Path(args.transcript).stem
                output_path = f"{transcript_name}_summary.md"
                summarizer.save_summary_markdown(
                    result["summary"],
                    output_path,
                    args.transcript,
                    result.get("usage"),
                )
                print(f"\n[SAVED] Summary written to: {output_path}")
        else:
            print(f"\n[ERROR] {result['error']}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
