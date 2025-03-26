import os
import glob
from abc import ABC, abstractmethod
from types import MappingProxyType

class PromptBuildStrategy(ABC):
    @staticmethod
    @abstractmethod
    def build(prompt_data: str) -> str:
        ...


class PromptStringStrategy(PromptBuildStrategy):
    @staticmethod
    def build(prompt_data: str) -> str:
        # return super().build()
        """Sets initial prompt from a string given by user without changes."""
        return prompt_data
    

class PromptDictionaryStrategy(PromptBuildStrategy):
    @staticmethod
    def build(prompt_data: str) -> str:
        # return super().build()
        """Builds prompt from a dictionary of lists."""
        parts = []
        if 'prefix' in prompt_data:
            parts.append(prompt_data['prefix'])
        for key, values in prompt_data.items():
            if key not in ['prefix', 'suffix']:
                parts.append(f"{key}:{','.join(values)}")
        if 'suffix' in prompt_data:
            parts.append(prompt_data['suffix'])
        return ' '.join(parts)
    

class PromptDirectoryStrategy(PromptBuildStrategy):
    @staticmethod
    def build(prompt_data: str) -> str:
        # return super().build()
        """Builds prompt from a directory with prefix, suffix, and .list files."""
        prompt_parts = []
        prefix_path = os.path.join(prompt_data, 'prefix')
        if os.path.exists(prefix_path):
            with open(prefix_path, 'r', encoding='utf8') as f:
                prompt_parts.append(f.readline().strip())
        
        for list_file in glob.glob(os.path.join(prompt_data, '*.list')):
            category = os.path.splitext(os.path.basename(list_file))[0]
            with open(list_file, 'r', encoding='utf8') as f:
                items = [line.strip() for line in f if line.strip()]
                if items:
                    prompt_parts.append(f"{category}:{','.join(items)}.")
        
        suffix_path = os.path.join(prompt_data, 'suffix')
        if os.path.exists(suffix_path):
            with open(suffix_path, 'r') as f:
                prompt_parts.append(f.readline().strip())
        
        return ' '.join(prompt_parts)
    

class PromptBuildStrategyFactory():
    _strategy_mapping = MappingProxyType(
        {
            'string':       PromptStringStrategy(),
            'str':          PromptStringStrategy(),

            'dictionary':   PromptDictionaryStrategy(),
            'dict':         PromptDictionaryStrategy(),

            'directory':    PromptDirectoryStrategy(),
            'dir':          PromptDirectoryStrategy()
        }
    )

    @staticmethod
    def get_strategy(prompt_type: str):
        strategy = PromptBuildStrategyFactory._strategy_mapping.get(prompt_type, None)
        if not strategy:
            raise ValueError(f"Unknown prompt build strategy: {prompt_type}!")
        return strategy
