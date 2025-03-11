from utilities.strategies.transcription_strategy import (
    NonDiarizedSingleStreamStrategy,
    DiarizedSingleStreamStrategy,
    NonDiarizedMultiStreamStrategy,
    NonDiarizedAlignedFilesStrategy
)
from utilities.prompt_builder import PromptBuilder
from dotenv import load_dotenv
import os

class TranscriberBuilder:
    """Builder for creating DiscordTranscriber instances."""
    def __init__(self):
        self.strategy = None
        self.input_files = []
        self.output_dir = None
        self.clip_dir = None
        self.initial_prompt = None
        self.output_types = []

    def with_strategy(self, strategy_name):
        strategy_map = {
            'non-diarized-single': NonDiarizedSingleStreamStrategy(),
            'nds': NonDiarizedSingleStreamStrategy(),

            'diarized-single': DiarizedSingleStreamStrategy(),
            'ds': DiarizedSingleStreamStrategy(),

            'non-diarized-multi': NonDiarizedMultiStreamStrategy(),
            'ndm': NonDiarizedMultiStreamStrategy(),

            'non-diarized-aligned': NonDiarizedAlignedFilesStrategy(),
            'nda': NonDiarizedAlignedFilesStrategy()
        }
        self.strategy = strategy_map.get(strategy_name)
        if not self.strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        return self

    def with_input_files(self, input_files):
        self.input_files = input_files
        return self

    def with_output_dir(self, output_dir):
        self.output_dir = output_dir
        return self

    def with_clip_dir(self, clip_dir):
        self.clip_dir = clip_dir
        return self

    def with_initial_prompt(self, prompt_type, prompt):
        if prompt_type == 'string':
            self.initial_prompt = PromptBuilder.from_string(prompt)
        elif prompt_type == 'directory':
            self.initial_prompt = PromptBuilder.from_directory(prompt)
        else:
            self.initial_prompt = None
        print(f"[INITIAL PROMPT SET]\n{self.initial_prompt}\n")
        return self

    def with_output_types(self, output_types):
        self.output_types = output_types
        return self

    def build(self):
        if not all([self.strategy, self.input_files, self.output_dir, self.clip_dir, self.output_types]):
            raise ValueError("All required fields must be set before building")
        return DiscordTranscriber(
            strategy=self.strategy,
            input_files=self.input_files,
            output_dir=self.output_dir,
            clip_dir=self.clip_dir,
            initial_prompt=self.initial_prompt,
            output_types=self.output_types
        )

class DiscordTranscriber:
    """Processes audio files using the selected strategy."""
    def __init__(self, strategy, input_files, output_dir, clip_dir, initial_prompt, output_types):
        self.strategy = strategy
        self.input_files = input_files
        self.output_dir = output_dir
        self.clip_dir = clip_dir
        self.initial_prompt = initial_prompt
        self.output_types = output_types
        self._load_env()

    def _load_env(self):
        load_dotenv()
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN must be set in the .env file for pyannote.audio model access")
        os.environ["HF_TOKEN"] = hf_token

    def process(self):
        self.strategy.process(self.input_files, self.output_dir, self.clip_dir, self.initial_prompt, self.output_types)