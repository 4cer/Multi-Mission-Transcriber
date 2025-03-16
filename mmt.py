"""Multi-Mission Transcriber"""
import argparse
from utilities.discord_transcriber import TranscriberBuilder
import os

from whisper.tokenizer import LANGUAGES

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diarize and transcribe Discord conversation recordings", epilog="Further help can be found at https://github.com/4cer/SessionTranscriber")
    parser.add_argument('-i', '--input', action='append', required=True, help='Input audio file(s)')
    parser.add_argument('-o', '--output-directory', default="output", help='Output directory for final results')
    parser.add_argument('-c', '--clip-directory', default="clips", help='Intermediate clip directory for split files')
    parser.add_argument('-s', '--strategy', choices=['non-diarized-single', 'diarized-single', 'non-diarized-multi', 'non-diarized-aligned', 'nds', 'ds', 'ndm', 'nda', 'test'], required=True, help='Transcription strategy')
    parser.add_argument('-t', '--prompt-type', choices=['string', 'directory'], help='Type of initial prompt (string or directory)')
    parser.add_argument('-p', '--prompt', help='Initial prompt string or directory path')
    output_types = ['json', 'text', 'dense', 'raw']
    parser.add_argument('-f', '--output-types', nargs='+', choices=output_types, required=True, help=f'Output types ({", ".join(output_types)} or any combination)')
    parser.add_argument('-l', '--language', choices=[*LANGUAGES.keys(), *LANGUAGES.values()], metavar="{pl, en, polish, english, ...}", help="Language presumed for the entire recording.")
    parser.add_argument('-m', '--speakers-min', type=int, help="The expected maximum of speaker identities. The number excludes non-speaker noise/silence")
    parser.add_argument('-x', '--speakers-max', type=int, help="The expected minimum of speaker identities. The number excludes non-speaker noise/silence")
    parser.add_argument('-e', '--speaker-count', type=int, help="The expected exact count of speakers, mutually exclusive with -m -x")
    args = parser.parse_args()

    # Enforce XOR for prompt-type and prompt
    if (args.prompt_type and not args.prompt) or (args.prompt and not args.prompt_type):
        parser.error('--prompt-type and --prompt must be provided together')

    # Enforce -e mutually exclusive with -m -x
    if args.speaker_count and ((args.speakers_min and args.speakers_max) or args.speakers_min or args.speakers_max):
        parser.error('Use either `--e SPEAKER-COUNT` xor one or both of: `-m SPEAKER-MIN` `-x SPEAKER-MAP`')

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
        .with_language(args.language)
        .with_speaker_count(args.speakers_min, args.speakers_max, args.speaker_count)
        .build()
    )

    # Process the audio
    transcriber.process()