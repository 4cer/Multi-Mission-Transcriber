"""Multi-Mission Transcriber"""
import argparse
from utilities.transcriber import TranscriberBuilder
from utilities.pipeline_context import PipelineContextBuilder
import os

from whisper.tokenizer import LANGUAGES

if __name__ == "__main__":
    transcription_strategy_types = ['non-diarized-single', 'diarized-single', 'non-diarized-multi', 'non-diarized-aligned', 'nds', 'ds', 'ndm', 'nda']
    prompt_types = ['string', 'directory', 'str', 'dir']
    output_types = ['json', 'text', 'dense', 'raw']
    model_types = ['tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'medium.en', 'large', 'large-v1', 'large-v2', 'large-v3']

    # Transcription arguments
    parser = argparse.ArgumentParser(description="Diarize and transcribe Discord conversation recordings", epilog="Further help can be found at https://github.com/4cer/SessionTranscriber")
    parser.add_argument('-i', '--input', nargs='+', action='extend', help='Input audio file(s)')
    parser.add_argument('-o', '--output-directory', default="output", help='Output directory for final results')
    parser.add_argument('-b', '--output-base-name', type=str, help='Output file base name, extended with type and extension for each output type.')
    parser.add_argument('-c', '--clip-directory', default="clips", help='Intermediate clip directory for split files')
    parser.add_argument('-s', '--strategy', choices=transcription_strategy_types, help='Transcription strategy')
    parser.add_argument('-t', '--prompt-type', choices=prompt_types, help='Type of initial prompt (string or directory)')
    parser.add_argument('-p', '--prompt', help='Initial prompt string or directory path')
    parser.add_argument('-f', '--output-types', nargs='+', choices=output_types, help=f'Output types ({", ".join(output_types)} or any combination)')
    parser.add_argument('-l', '--language', choices=[*LANGUAGES.keys(), *LANGUAGES.values()], metavar="{pl, en, polish, english, ...}", help="Language presumed for the entire recording.")
    parser.add_argument('-m', '--speakers-min', type=int, help='Minimum number of speaker identities (excludes non-speaker noise/silence)')
    parser.add_argument('-x', '--speakers-max', type=int, help='Maximum number of speaker identities (excludes non-speaker noise/silence)')
    parser.add_argument('-e', '--speaker-count', type=int, help='Exact number of speaker identities (excludes non-speaker noise/silence). Mutually exclusive with -m and -x')
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Builder verbosity: level (Default is 0).")
    parser.add_argument('-w', '--suppress-warnings', action='store_true', help="Suppress warnings from constituent libraries and models.")
    parser.add_argument('-M', '--model', choices=model_types, default='large', help='Whisper model size to use')
    # Summarization arguments
    parser.add_argument('--summarize', action='store_true', help='Enable summarization after transcription')
    parser.add_argument('--summarization-transcript', help='Input transcript file, also serving as a summarize only flag.')
    parser.add_argument('--summarization-prompt-type', choices=prompt_types, default='directory', help='Type of summarization prompt (default: directory)')
    parser.add_argument('--summarization-prompt', default='prompt/summarization', help='Summarization prompt directory or string (default: prompt/summarization)')
    parser.add_argument('--summary-output', help='Output path for summary markdown file')
    parser.add_argument('--no-confirm', action='store_true', help='Skip confirmation before sending summarization request')
    args = parser.parse_args()

    # Determine pipeline modes
    transcription_needed = not args.summarization_transcript
    summarization_needed = args.summarize or args.summarization_transcript

    # Enforce non-standard argument constraints
    ## Transcription
    if transcription_needed:
        if not args.input:
            parser.error('--input is required for transcription')
        if not args.strategy:
            parser.error('--strategy is required for transcription')
        if not args.output_types:
            parser.error('--output-types is required for transcription')

    ### Enforce XOR for prompt-type and prompt
    if (args.prompt_type and not args.prompt) or (args.prompt and not args.prompt_type):
        parser.error('--prompt-type and --prompt must be provided together')

    ### Enforce -e mutually exclusive with -m -x
    if args.speaker_count and ((args.speakers_min and args.speakers_max) or args.speakers_min or args.speakers_max):
        parser.error('Use either `--e SPEAKER-COUNT` xor one or both of: `-m SPEAKERS-MIN` `-x SPEAKERS-MAX`')

    ### Ensure output and clip directories exist
    if transcription_needed:
        os.makedirs(args.output_directory, exist_ok=True)
        os.makedirs(args.clip_directory, exist_ok=True)

    ## Summarization
    if summarization_needed:
        if not args.summarization_prompt:
            parser.error('--summarization-prompt is required for summarization')
        if not args.summary_output:
            parser.error('--summary-output is required for summarization')

    tracker = (PipelineContextBuilder()
        .with_transcription_prompt(args.prompt_type, args.prompt)
        .with_summarization_prompt(args.summarization_prompt_type, args.summarization_prompt)
        .with_transcript_path(args.summarization_transcript)
        .build()
    )

    # Build the transcriber and process file(s)
    if transcription_needed:
        builder = TranscriberBuilder(verbosity=args.verbose, suppress_warnings=args.suppress_warnings)
        transcriber = (builder
            .with_strategy(args.strategy)
            .with_input_files(args.input)
            .with_output_dir(args.output_directory)
            .with_clip_dir(args.clip_directory)
            .with_assembled_transcription_prompt(tracker.get_transcription_prompt())
            .with_output_types(args.output_types)
            .with_language(args.language)
            .with_speaker_count(args.speakers_min, args.speakers_max, args.speaker_count)
            .with_output_base_name(args.output_base_name)
            .with_model(args.model)
            .with_pipeline_context(tracker)
            .build())

        transcriber.process()

    # Summarization (if enabled)
    if summarization_needed:
        from utilities.llm_summarizer import LLMSummarizerBuilder

        summarizer = (LLMSummarizerBuilder(verbosity=args.verbose)
            .with_confirmation(not args.no_confirm)
            .with_pipeline_context(tracker)
            .with_summary_output(args.summary_output)
            .build())

        # Use provided transcript path or get best from tracker
        transcript_path = args.summarization_transcript if args.summarization_transcript else tracker.get_best_transcript_filepath()
        if transcript_path:
            summarizer.summarize(transcript_path)
        else:
            print("[WARNING] No transcript found for summarization.")
