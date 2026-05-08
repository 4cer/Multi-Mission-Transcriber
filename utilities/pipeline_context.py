from utilities.prompt_builder import PromptBuildStrategyFactory, PromptBuildContext


from typing import Optional
import os


TRANSCRIPT_PRIORITY = [
    'dense',
    'text',
    'json',
    'raw',
    'other',
]


class PipelineContext:
    def __init__(
        self,
        transcription_prompt,
        summarization_prompt,
        transcript_files: dict[str, Optional[str]],
    ) -> None:
        self.transcription_prompt = transcription_prompt
        self.summarization_prompt = summarization_prompt
        self.transcript_files = transcript_files

    def get_transcription_prompt(self) -> str:
        return self.transcription_prompt
    
    def get_summarization_prompt(self) -> str:
        return self.summarization_prompt
    
    def get_best_transcript_filepath(self) -> Optional[str]:
        for priority in TRANSCRIPT_PRIORITY:
            filepath = self.transcript_files.get(priority, None)
            if filepath and os.path.exists(filepath):
                return filepath
        return None
    
    def get_transcript_filepath(self, transcript_type: str) -> Optional[str]:
        return self.transcript_files.get(transcript_type, None)
    
    def register_transcript_filepath(self, transcript_path: str, transcript_type: str) -> None:
        self.transcript_files[transcript_type] = transcript_path


class PipelineContextBuilder:
    """Builder for creating FileTracker instances."""
    def __init__(self, verbosity: int = 0) -> None:
        self.transcription_prompt = None
        self.summarization_prompt = None
        self.transcripts: dict[str, Optional[str]] = {
            'dense': None,
            'text': None,
            'json': None,
            'raw': None,
            'other': None,
        }
        
        self.transcription_prompt_set = False
        
        if verbosity < 0 or verbosity > 5:
            raise ValueError("Verbosity must be an integer, 0 <= verbosity <= 5")
        
        self._verbosity = verbosity

    def with_transcription_prompt(self, prompt_type, prompt) -> "PipelineContextBuilder":
        ctx = PromptBuildContext(prompt_data=prompt, inner_prompt=None)
        prompt_assembled = PromptBuildStrategyFactory.get_transcription_strategy(prompt_type).build(ctx)
        self.transcription_prompt = prompt_assembled.strip() if prompt_assembled else None

        if self.transcription_prompt and len(self.transcription_prompt) > 1024:
            raise ValueError("Transcription prompt mustn't exceed 1024 characters!")
        if self._verbosity > 0 and self.transcription_prompt:
            print(f"[TRANSCRIPTION PROMPT SET] [LENGTH: {len(self.transcription_prompt)}]\n{self.transcription_prompt}\n")

        self.transcription_prompt_set = True
        return self
    
    def with_summarization_prompt(self, prompt_type, prompt) -> "PipelineContextBuilder":
        if not self.transcription_prompt_set:
            raise RuntimeError("Transcription prompt must be set before "
                               "summarization prompt!")
        
        ctx = PromptBuildContext(prompt_data=prompt, inner_prompt=self.transcription_prompt)
        prompt_assembled = PromptBuildStrategyFactory.get_summarization_strategy(prompt_type).build(ctx)
        self.summarization_prompt = prompt_assembled.strip() if prompt_assembled else None

        if self._verbosity > 0 and self.summarization_prompt:
            print(f"[SUMMARIZATION PROMPT SET] [LENGTH: {len(self.summarization_prompt)}]\n{self.summarization_prompt}\n")
        
        return self
    
    def with_transcript_path(self, transcript_path: Optional[str], transcript_type: str = 'other') -> "PipelineContextBuilder":
        if transcript_path is None:
            return self
        self.transcripts[transcript_type] = transcript_path
        return self
    
    def build(self) -> PipelineContext:
        return PipelineContext(
            transcription_prompt=self.transcription_prompt,
            summarization_prompt=self.summarization_prompt,
            transcript_files=self.transcripts,
        )
