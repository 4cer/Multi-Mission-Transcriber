from utilities.strategies.transcription_strategy import TranscriptionStrategyFactory, TranscriptionStrategy
from utilities.prompt_builder import PromptBuildStrategyFactory, PromptBuildContext
from utilities.pipeline_context import PipelineContext


from dotenv import load_dotenv
import os
from typing import Optional


class TranscriberBuilder:
    """Builder for creating DiscordTranscriber instances."""
    def __init__(self, verbosity: int = 0, suppress_warnings: bool = False):
        self.strategy: TranscriptionStrategy
        self.input_files: list[str] = []
        self.output_dir: str
        self.clip_dir: str
        self.transcription_prompt: Optional[str] = None
        self.output_types: list[str] = []
        self.language: Optional[str] = None
        self.model: str
        self.pipeline_context: Optional[PipelineContext] = None

        if verbosity < 0 or verbosity > 5:
            raise ValueError("Verbosity must be an integer, 0 <= verbosity <= 5")

        self._BUILDER_ONLY_verbosity = verbosity
        self._BUILDER_ONLY_suppress_warnings = suppress_warnings

    def with_strategy(self, strategy_name: str) -> "TranscriberBuilder":
        self.strategy = TranscriptionStrategyFactory.get_strategy(strategy_name)
        return self

    def with_input_files(self, input_files: list[str]) -> "TranscriberBuilder":
        self.input_files = input_files
        return self

    def with_output_dir(self, output_dir: str) -> "TranscriberBuilder":
        self.output_dir = output_dir
        return self

    def with_clip_dir(self, clip_dir: str) -> "TranscriberBuilder":
        self.clip_dir = clip_dir
        return self

    # def with_transcription_prompt(self, prompt_type: str, prompt: str):
    #     ctx = PromptBuildContext(
    #         prompt_data=prompt,
    #         inner_prompt=None
    #     )
    #     prompt_assembled = PromptBuildStrategyFactory.get_transcription_strategy(prompt_type).build(ctx)
    #     self.transcription_prompt = prompt_assembled.strip() if prompt_assembled else None

    #     if self.transcription_prompt and len(self.transcription_prompt) > 1024:
    #         raise ValueError("Initial prompt mustn't exceed 1024 characters!")
    #     if self._BUILDER_ONLY_verbosity > 0 and self.transcription_prompt:
    #         print(f"[INITIAL PROMPT SET] [LENGTH: {len(self.transcription_prompt)}]\n{self.transcription_prompt}\n")
    #     return self
    
    def with_assembled_transcription_prompt(self, prompt: str) -> "TranscriberBuilder":
        self.transcription_prompt = prompt
        return self

    def with_output_types(self, output_types: list[str]) -> "TranscriberBuilder":
        self.output_types = output_types
        return self
    
    def with_language(self, language: str) -> "TranscriberBuilder":
        self.language = language
        return self
    
    def with_speaker_count(
            self, min: Optional[int]=None,
            max: Optional[int]=None,
            exact: Optional[int]=None
    ) -> "TranscriberBuilder":
        self.speakers_min = min
        self.speakers_max = max
        self.speaker_count = exact
        return self
    
    def with_output_base_name(self, output_base_name: str) -> "TranscriberBuilder":
        self.output_base_name = output_base_name
        return self

    def with_model(self, model: str) -> "TranscriberBuilder":
        self.model = model
        return self
    
    def with_pipeline_context(self, context: PipelineContext) -> "TranscriberBuilder":
        self.pipeline_context = context
        return self

    def build(self):
        if not all([self.strategy, self.input_files, self.output_dir, self.clip_dir, self.output_types]):
            raise ValueError("All required fields must be set before building")
        return Transcriber(
            strategy=self.strategy,
            input_files=self.input_files,
            output_dir=self.output_dir,
            clip_dir=self.clip_dir,
            initial_prompt=self.transcription_prompt,
            output_types=self.output_types,
            language=self.language,
            speakers_min=self.speakers_min,
            speakers_max=self.speakers_max,
            speaker_count=self.speaker_count,
            output_base_name = self.output_base_name,
            model=self.model,
            pipeline_context=self.pipeline_context,
        )


class Transcriber:
    """Processes audio files using the selected strategy."""
    def __init__(
            self,
            strategy: TranscriptionStrategy,
            input_files: list[str],
            output_dir: str,
            clip_dir: str,
            initial_prompt: Optional[str],
            output_types: list[str],
            language: Optional[str],
            speakers_min: Optional[int],
            speakers_max: Optional[int],
            speaker_count: Optional[int],
            output_base_name: str,
            model: str,
            pipeline_context: Optional[PipelineContext],
    ):
        self.strategy = strategy
        self.input_files = input_files
        self.output_dir = output_dir
        self.clip_dir = clip_dir
        self.initial_prompt = initial_prompt
        self.output_types = output_types
        self.language = language
        self.speakers_min = speakers_min
        self.speakers_max = speakers_max
        self.speaker_count = speaker_count
        self.output_base_name = output_base_name
        self.model = model
        self.pipeline_context = pipeline_context
        self._load_env()

    def _load_env(self):
        load_dotenv()
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token or hf_token == 'your_huggingface_token_here':
            raise ValueError("HF_TOKEN must be set in the .env file for pyannote.audio model access")
        os.environ["HF_TOKEN"] = hf_token

    def process(self):
        self.strategy.process(
            self.input_files,
            self.output_dir,
            self.clip_dir,
            self.initial_prompt,
            self.output_types,
            self.language,
            self.speakers_min,
            self.speakers_max,
            self.speaker_count,
            self.output_base_name,
            self.model,
            self.pipeline_context
        )
