"""Multi-Mission Transcriber"""
import argparse
from utilities.discord_transcriber import TranscriberBuilder
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diarize and transcribe Discord conversation recordings")
    parser.add_argument('--input', action='append', required=True, help='Input audio file(s)')
    parser.add_argument('--output-dir', required=True, help='Output directory for final results')
    parser.add_argument('--clip-dir', required=True, help='Intermediate clip directory for split files')
    parser.add_argument('--strategy', choices=['non-diarized-single', 'diarized-single', 'non-diarized-multi', 'non-diarized-aligned'], required=True, help='Transcription strategy')
    parser.add_argument('--prompt-type', choices=['string', 'directory'], help='Type of initial prompt (string or directory)')
    parser.add_argument('--prompt', help='Initial prompt string or directory path')
    parser.add_argument('--output-types', nargs='+', choices=['json', 'text'], required=True, help='Output types (json, text, or both)')
    args = parser.parse_args()

    # Enforce XOR for prompt-type and prompt
    if (args.prompt_type and not args.prompt) or (args.prompt and not args.prompt_type):
        parser.error('--prompt-type and --prompt must be provided together')

    # Ensure output and clip directories exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.clip_dir, exist_ok=True)

    # Build the transcriber
    builder = TranscriberBuilder()
    transcriber = (builder
        .with_strategy(args.strategy)
        .with_input_files(args.input)
        .with_output_dir(args.output_dir)
        .with_clip_dir(args.clip_dir)
        .with_initial_prompt(args.prompt_type, args.prompt)
        .with_output_types(args.output_types)
        .build()
    )

    # Process the audio
    transcriber.process()