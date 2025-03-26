import os
import glob
from abc import ABC, abstractmethod
from types import MappingProxyType

class PromptBuildStrategy(ABC):
    @abstractmethod
    def build(self, prompt_data: str|dict) -> str:
        ...


class PromptStringStrategy(PromptBuildStrategy):
    def build(self, prompt_string: str) -> str:
        # return super().build()
        """Sets initial prompt from a string given by user without changes."""
        return prompt_string
    

class PromptDictionaryStrategy(PromptBuildStrategy):
    def build(self, prompt_dict: dict) -> str:
        # return super().build()
        """Builds prompt from a dictionary of lists."""
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
    def build(self, prompt_path: str) -> str:
        # return super().build()
        """Builds prompt from a directory with prefix, suffix, and .list files."""
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
