from utilities.prompt_builder import PromptBuildStrategyFactory, PromptBuildContext
from utilities.enums import ArtifactType, TranscriptPriority
from utilities.file_utils import make_clickable_path


from typing import Optional
import os
from dataclasses import dataclass


@dataclass
class ArtifactEntry:
    def __init__(
            self,
            file_path: str,
            category: ArtifactType,
            meta_inf: dict[str,str] = {}
    ) -> None:
        self.file_path: str = file_path
        self.category: ArtifactType = category
        self.meta_inf: dict[str,str] = meta_inf


class PipelineContext:
    def __init__(
        self,
        transcription_prompt,
        summarization_prompt,
        transcript_files: dict[TranscriptPriority, Optional[str]],
        verbosity: int = 0,
    ) -> None:
        self.transcription_prompt = transcription_prompt
        self.summarization_prompt = summarization_prompt
        self.transcript_files = transcript_files
        self.artifacts: list[ArtifactEntry] = []
        # self.output_files: list[tuple[str, str]] = []
        self.verbosity = verbosity

    def get_transcription_prompt(self) -> str:
        return self.transcription_prompt
    
    def get_summarization_prompt(self) -> str:
        return self.summarization_prompt
    
    def get_best_transcript_filepath(self) -> Optional[str]:
        for priority in TranscriptPriority.ordered():
            filepath = self.transcript_files.get(priority, None)
            if filepath and os.path.exists(filepath):
                return filepath
        return None
    
    def get_transcript_filepath(self, transcript_type: TranscriptPriority) -> Optional[str]:
        return self.transcript_files.get(transcript_type, None)
    
    def register_transcript(
            self,
            transcript_path: str,
            transcript_type: TranscriptPriority,
    ) -> None:
        if self.verbosity > 1:
            print(f"Registering transcript, {transcript_path}")
        self.transcript_files[transcript_type] = transcript_path

    def register_artifact(self, artifact: ArtifactEntry) -> None:
        if self.verbosity > 1:
            print(f"Registering artifact, {artifact}")
        self.artifacts.append(artifact)

    def report(self):
        if self.verbosity < 1 or len(self.artifacts) < 1:
            return
        max_lens = [len("PATH"),len("CATEGORY"),0]
        for i in self.artifacts:
            l0 = len(i.file_path) + 2
            if l0 > max_lens[0]:
                max_lens[0] = l0

            l1 = len(i.category.name)
            if l1 > max_lens[1]:
                max_lens[1] = l1

            for k,v in i.meta_inf.items():
                item_len = len(f"{k}: {v}")
                if item_len > max_lens[2]:
                    max_lens[2] = item_len

        print(f"{'CATEGORY'.ljust(max_lens[1])} | {'CATEGORY'.ljust(max_lens[0])} | {'META'.ljust(max_lens[2])}")
        print("".ljust(max_lens[0] + max_lens[1] + max_lens[2] + 6, "-"))
        for i in self.artifacts:
            quoted_path = "\"" + make_clickable_path(i.file_path) + "\""
            print(f"{i.category.name.ljust(max_lens[1], ' ')} | {quoted_path.ljust(max_lens[0])} | {str(i.meta_inf)}")
            

class PipelineContextBuilder:
    """Builder for creating FileTracker instances."""
    def __init__(self, verbosity: int = 0) -> None:
        self.transcription_prompt = None
        self.summarization_prompt = None
        self.transcripts: dict[TranscriptPriority, Optional[str]] = {
            TranscriptPriority.DENSE: None,
            TranscriptPriority.TEXT: None,
            TranscriptPriority.JSON: None,
            TranscriptPriority.RAW: None,
            TranscriptPriority.OTHER: None,
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
    
    def with_transcript_path(
            self,
            transcript_path: Optional[str],
            transcript_type: TranscriptPriority = TranscriptPriority.OTHER
    ) -> "PipelineContextBuilder":
        if transcript_path is None:
            return self
        self.transcripts[transcript_type] = transcript_path
        return self
    
    def build(self) -> PipelineContext:
        return PipelineContext(
            transcription_prompt=self.transcription_prompt,
            summarization_prompt=self.summarization_prompt,
            transcript_files=self.transcripts,
            verbosity=self._verbosity,
        )
