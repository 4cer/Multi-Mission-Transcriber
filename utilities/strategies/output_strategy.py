from __future__ import annotations
from types import MappingProxyType
from abc import ABC, abstractmethod
import os
import json
import datetime, time
import typing
from typing import Optional


if typing.TYPE_CHECKING:
    from utilities.pipeline_context import PipelineContext


class OutputFormatStrategy(ABC):
    @abstractmethod
    def output(
        self,
        segments: list[dict],
        output_dir: str,
        timestamp: int,
        output_base_name: Optional[str] = None,
        pipeline_context: Optional[PipelineContext] = None,
    ) -> None:
        ...

    @staticmethod
    def _format_time( seconds) -> str:
        """Transform {seconds from recording start} into a HH:MM:SS:ssss format."""
        if seconds == None:
            return "--:--:--:---"
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"
    

class OutputJson(OutputFormatStrategy):
    def output(
        self,
        segments: list[dict],
        output_dir: str,
        timestamp: int,
        output_base_name: Optional[str] = None,
        pipeline_context: Optional[PipelineContext] = None,
    ) -> None:
        json_path = os.path.join(output_dir, f"{timestamp}_{output_base_name}-3.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(
                {"segments": [{
                    "start": seg.get("start", None),
                    "end": seg.get("end", None),
                    "speaker": seg.get("speaker", "N/A"),
                    "text": seg.get("text", "").strip()}
                    for seg in segments]
                },
                f, indent=2, ensure_ascii=False)
        if pipeline_context:
            pipeline_context.register_transcript_filepath(json_path, 'json')
    

class OutputText(OutputFormatStrategy):
    def output(
        self,
        segments: list[dict],
        output_dir: str,
        timestamp: int,
        output_base_name: Optional[str] = None,
        pipeline_context: Optional[PipelineContext] = None,
    ) -> None:
        text_path = os.path.join(output_dir, f"{timestamp}_{output_base_name}-1.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            for seg in segments:
                start_str = self._format_time(seg["start"])
                end_str = self._format_time(seg.get("end",None))
                f.write(f"[{start_str} / {end_str}] ({seg.get('speaker', 'N/A')}):\n{seg['text'].strip()}\n\n")
        if pipeline_context:
            pipeline_context.register_transcript_filepath(text_path, 'text')
    

class OutputDense(OutputFormatStrategy):
    def output(
        self,
        segments: list[dict],
        output_dir: str,
        timestamp: int,
        output_base_name: Optional[str] = None,
        pipeline_context: Optional[PipelineContext] = None,
    ) -> None:
        text_dense_path = os.path.join(output_dir, f"{timestamp}_{output_base_name}-0.dense.txt")
        with open(text_dense_path, 'w', encoding='utf-8') as f:
            for seg in segments:
                start_str = self._format_time(seg["start"])
                end_str = self._format_time(seg.get("end",None))
                f.write(f"[{start_str} / {end_str}] ({seg.get('speaker', 'N/A')}): {seg['text'].strip()}\n")
        if pipeline_context:
            pipeline_context.register_transcript_filepath(text_dense_path, 'dense')
    

class OutputRaw(OutputFormatStrategy):
    def output(
        self,
        segments: list[dict],
        output_dir: str,
        timestamp: int,
        output_base_name: Optional[str] = None,
        pipeline_context: Optional[PipelineContext] = None,
    ) -> None:
        text_raw_path = os.path.join(output_dir, f"{timestamp}_{output_base_name}-2.raw.txt")
        with open(text_raw_path, 'w', encoding='utf-8') as f:
            for seg in segments:
                f.write(f"{seg['text'].strip()}\n")
        if pipeline_context:
            pipeline_context.register_transcript_filepath(text_raw_path, 'raw')
    

class OutputFormatStrategyFactory():
    _strategy_mapping = MappingProxyType(
        {
            'json': OutputJson(),
            'text': OutputText(),
            'dense': OutputDense(),
            'raw': OutputRaw()
        }
    )

    @staticmethod
    def get_strategy(output_type: str) -> OutputFormatStrategy:
        strategy = OutputFormatStrategyFactory._strategy_mapping.get(output_type, None)
        if not strategy:
            raise ValueError(f"Unknown output format strategy: {output_type}!")
        return strategy
