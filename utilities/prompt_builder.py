import os
import glob

class PromptBuilder:
    @staticmethod
    def from_string(prompt_str):
        """Builds prompt from a full string."""
        return prompt_str

    @staticmethod
    def from_dict(prompt_dict) -> str:
        """Builds prompt from a dictionary of lists."""
        parts = []
        if 'prefix' in prompt_dict:
            parts.append(prompt_dict['prefix'])
        for key, values in prompt_dict.items():
            if key not in ['prefix', 'suffix']:
                parts.append(f"{key}:{','.join(values)}")
        if 'suffix' in prompt_dict:
            parts.append(prompt_dict['suffix'])
        return ' '.join(parts)

    @staticmethod
    def from_directory(prompt_dir) -> str:
        """Builds prompt from a directory with prefix, suffix, and .list files."""
        prompt_parts = []
        prefix_path = os.path.join(prompt_dir, 'prefix')
        if os.path.exists(prefix_path):
            with open(prefix_path, 'r') as f:
                prompt_parts.append(f.readline().strip())
        
        for list_file in glob.glob(os.path.join(prompt_dir, '*.list')):
            category = os.path.splitext(os.path.basename(list_file))[0]
            with open(list_file, 'r') as f:
                items = [line.strip() for line in f if line.strip()]
                if items:
                    prompt_parts.append(f"{category}:{','.join(items)}")
        
        suffix_path = os.path.join(prompt_dir, 'suffix')
        if os.path.exists(suffix_path):
            with open(suffix_path, 'r') as f:
                prompt_parts.append(f.readline().strip())
        
        return ' '.join(prompt_parts)