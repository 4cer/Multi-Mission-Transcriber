import os
import glob
from abc import ABC, abstractmethod
from types import MappingProxyType
from dataclasses import dataclass
# from typing import Optional


@dataclass
class PromptBuildContext:
    """Represents prompt building argument combinations.

    One of:
    - Prompt directory path, None
    - Prompt dictionary, None
    - Prompt string, None
    - Prompt directory, Inner prompt string
    """
    prompt_data: str | dict
    inner_prompt: str | None


class PromptBuildStrategy(ABC):
    @abstractmethod
    def build(self, context: PromptBuildContext) -> str:
        ...


class PromptStringStrategy(PromptBuildStrategy):
    def build(self, context: PromptBuildContext) -> str:
        """Sets initial prompt from a string given by user without changes."""
        prompt_string = context.prompt_data
        if type(prompt_string) is not str:
            raise RuntimeError("Prompt String must receive a prompt string!")
        return prompt_string


class PromptDictionaryStrategy(PromptBuildStrategy):
    # def build(self, prompt_dict: dict) -> str:
    def build(self, context: PromptBuildContext) -> str:
        """Builds prompt from a dictionary of lists."""
        prompt_dict = context.prompt_data
        if type(prompt_dict) is not dict:
            raise RuntimeError("Prompt Dictionary must receive a prompt dict!")

        parts = []
        if 'prefix' in prompt_dict:
            parts.append(prompt_dict['prefix'])
        lists = []
        for key, values in prompt_dict.items():
            if key not in ['prefix', 'suffix']:
                lists.append(f"{key}:{','.join(values)}")
        parts.append(f"{'. '.join(lists)}.")
        if 'suffix' in prompt_dict:
            parts.append(prompt_dict['suffix'])
        return ' '.join(parts)


class PromptDirectoryStrategy(PromptBuildStrategy):
    # def build(self, prompt_path: str) -> str:
    def build(self, context: PromptBuildContext) -> str:
        """Builds prompt from a directory with prefix, suffix, and .list files."""
        prompt_path = context.prompt_data
        if type(prompt_path) is not str:
            raise RuntimeError("Prompt Directory must receive a prompt dir "
                               "path!")
        
        prompt_parts = []
        prefix_path = os.path.join(prompt_path, 'prefix')
        if os.path.exists(prefix_path):
            with open(prefix_path, 'r', encoding='utf8') as f:
                prompt_parts.append(f.readline().strip())
        
        for list_file in glob.glob(os.path.join(prompt_path, '*.list')):
            category = os.path.splitext(os.path.basename(list_file))[0]
            with open(list_file, 'r', encoding='utf8') as f:
                items = [line.strip() for line in f if line.strip()]
                if items:
                    prompt_parts.append(f"{category}:{','.join(items)}.")
        
        suffix_path = os.path.join(prompt_path, 'suffix')
        if os.path.exists(suffix_path):
            with open(suffix_path, 'r', encoding='utf8') as f:
                prompt_parts.append(f.readline().strip())
        
        return ' '.join(prompt_parts)


class SummarizationPromptDirectoryStrategy(PromptBuildStrategy):
    # def build(self, prompt_path: str) -> str:
    def build(self, context: PromptBuildContext) -> str:
        """Builds prompt from a directory with prefix, suffix, and .list files."""
        prompt_path = context.prompt_data
        inner_prompt = context.inner_prompt
        print(type(prompt_path), prompt_path)
        print(type(inner_prompt), inner_prompt)
        if not (isinstance(prompt_path, str) and isinstance(inner_prompt, str)):
            raise RuntimeError("Summarization Prompt Directory must receive a "
                               "summarization prompt dir path and rendered "
                               "string transcription prompt!")
        
        prompt_parts = []
        prefix_path = os.path.join(prompt_path, 'prefix')
        if os.path.exists(prefix_path):
            with open(prefix_path, 'r', encoding='utf8') as f:
                prompt_parts.append(f.read().strip())
        
        prompt_parts.append("\nTranscription prompt:")
        prompt_parts.append(inner_prompt)
        prompt_parts.append("\n")
        
        suffix_path = os.path.join(prompt_path, 'suffix')
        if os.path.exists(suffix_path):
            with open(suffix_path, 'r', encoding='utf8') as f:
                prompt_parts.append(f.read().strip())
        
        return '\n'.join(prompt_parts)


class PromptBuildStrategyFactory():
    _transcription_strategy_mapping = MappingProxyType(
        {
            'string':           PromptStringStrategy(),
            'str':              PromptStringStrategy(),

            'dictionary':       PromptDictionaryStrategy(),
            'dict':             PromptDictionaryStrategy(),

            'directory':        PromptDirectoryStrategy(),
            'dir':              PromptDirectoryStrategy(),
        }
    )

    _summarization_strategy_mapping = MappingProxyType(
        {
            'directory':        SummarizationPromptDirectoryStrategy(),
            'dir':              SummarizationPromptDirectoryStrategy(),

            'string':           PromptStringStrategy(),
            'str':              PromptStringStrategy(),
        }
    )

    @staticmethod
    def get_transcription_strategy(prompt_type: str):
        strategy = PromptBuildStrategyFactory._transcription_strategy_mapping.get(prompt_type, None)
        if not strategy:
            raise ValueError(f"Unknown prompt build strategy: {prompt_type}!")
        return strategy


    @staticmethod
    def get_summarization_strategy(prompt_type: str):
        strategy = PromptBuildStrategyFactory._summarization_strategy_mapping.get(prompt_type, None)
        if not strategy:
            raise ValueError(f"Unknown prompt build strategy: {prompt_type}!")
        return strategy
