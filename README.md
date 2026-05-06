# Multi-Mission Transcriber (MMT)
Developed primarily for transcribing recordings of tabletop RPG sessions conducted over Discord or similar communication software.

## Usage
### Interactive Mode (`interactiverun.ps1`)

For a guided, interactive experience, use the `interactiverun.ps1` PowerShell script. It prompts for each argument step-by-step and remembers your preferences across runs (prompt, output directory, language) via a local `mmt_config.json` file. It also keeps a history of the last 5 output base names for quick reference.

The script automatically uses the project's `.venv` Python interpreter, so there is no need to activate the virtual environment manually.

```Powershell
.\interactiverun.ps1
```

When launched, the script will walk you through the following prompts:

1. **Input audio files** — Space-separated file paths (wrap paths in double quotes if they contain spaces).
2. **Strategy** — Choose by number, full name, or short alias (defaults to `non-diarized-aligned`).
3. **Prompt type** — `directory` or `string` (defaults to `directory`).
4. **Prompt value** — Directory path or string depending on the chosen type; defaults to the last value used.
5. **Output directory** — Where results are written; defaults to the last directory used.
6. **Output types** — One or more of `json`, `text`, `dense`, `raw` (defaults to all four).
7. **Language** — Language code or name (e.g. `en`, `pl`); defaults to the last language used.
8. **Output base name** — Optional base name for output files; shows the last 5 names for reference.

Any prompt left blank will fall back to the persisted default (if one exists) or be omitted from the command.

### Command Line Usage
```
mmt.py [-h] -i INPUT [INPUT ...] [-o OUTPUT_DIRECTORY] [-b OUTPUT_BASE_NAME] [-c CLIP_DIRECTORY]
       -s {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda}
       [-t {string,directory,str,dir}] [-p PROMPT]
       -f {json,text,dense,raw} [{json,text,dense,raw} ...]
       [-l {pl, en, polish, english, ...}] [-m SPEAKERS_MIN] [-x SPEAKERS_MAX] [-e SPEAKER_COUNT]
       [-v] [-w] [-M {tiny,tiny.en,base,base.en,small,small.en,medium,medium.en,large,large-v1,large-v2,large-v3}]

Diarize and transcribe Discord conversation recordings

options:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Input audio file(s)
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Output directory for final results
  -b OUTPUT_BASE_NAME, --output-base-name OUTPUT_BASE_NAME
                        Output file base name, extended with type and extension for each output type.
  -c CLIP_DIRECTORY, --clip-directory CLIP_DIRECTORY
                        Intermediate clip directory for split files
  -s {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda}, --strategy {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda}
                        Transcription strategy
  -t {string,directory,str,dir}, --prompt-type {string,directory,str,dir}
                        Type of initial prompt (string or directory)
  -p PROMPT, --prompt PROMPT
                        Initial prompt string or directory path
  -f {json,text,dense,raw} [{json,text,dense,raw} ...], --output-types {json,text,dense,raw} [{json,text,dense,raw} ...]
                        Output types (json, text, dense, raw or any combination)
  -l {pl, en, polish, english, ...}, --language {pl, en, polish, english, ...}
                        Language presumed for the entire recording.
  -m SPEAKERS_MIN, --speakers-min SPEAKERS_MIN
                        The expected maximum of speaker identities. The number excludes non-speaker noise/silence
  -x SPEAKERS_MAX, --speakers-max SPEAKERS_MAX
                        The expected minimum of speaker identities. The number excludes non-speaker noise/silence
  -e SPEAKER_COUNT, --speaker-count SPEAKER_COUNT
                        The expected exact count of speakers, mutually exclusive with -m -x
  -v, --verbose         Builder verbosity: level (Default is 0).
  -w, --suppress-warnings
                        Suppress warnings from constituent libraries and models.
  -M {tiny,tiny.en,base,base.en,small,small.en,medium,medium.en,large,large-v1,large-v2,large-v3}, --model {tiny,tiny.en,base,base.en,small,small.en,medium,medium.en,large,large-v1,large-v2,large-v3}
                        Whisper model size to use (default: large)
```

### Example usage with aligned clips and a directory prompt in Polish
```Powershell
python mmt.py `
    -i files\file1.aac files\file2.aac files\file3.aac files\file4.aac files\file5.aac files\file6.aac `
    --strategy nda `
    --prompt-type directory `
    --prompt prompt/some_prompt `
    --output-types json text dense raw `
    --language pl `
    --model large `
    --output-base-name "Name of output"
```

### Arguments
| Argument | Accepted Values | Description | Multiplicty | Required |
| :------- | :-------------- | :---------- | :---------: | :------: |
| `-i`, `--input` | Relative or absolute filepath(s) | Input audio file(s) - one or more paths separated by spaces | `1+` | `True` |
| `-o`, `--output-directory` | Relative or absolute filepath | Output directory for final results | `1` | `False` |
| `-b`, `--output-base-name` | String | Output file base name, extended with type and extension for each output type | `1` | `False` |
| `-c`, `--clip-directory` | Relative or absolute filepath | Intermediate clip directory for split files | `1` | `False` |
| `-s`, `--strategy` | One of<br>`{non-diarized-single,`<br>`diarized-single,`<br>`non-diarized-multi,`<br>`non-diarized-aligned,`<br>`nds, ds, ndm, nda}` | Transcription strategy | `1` | `True` |
| `-t`, `--prompt-type` | One of<br>`{string,directory}` | Type of initial prompt (string or directory) | `1` | `False` |
| `-p`, `--prompt` | For prompt type `string`:<br>String of length 1024 characters or less<br>For prompt type `directory`:<br>Relative or absolute directory path | Initial prompt string or directory path | `1` | `False` |
| `-f`, `--output-types` | One or more of:<br>`{json,text,dense,raw}` | Output types (json, text, dense, raw or any combination) | `1+` | `True` |
| `-l`, `--language` | {pl, en, polish, english, ...} | Language presumed for the entire recording | `0+` | `False` |
| `-M`, `--model` | One of<br>`{tiny, tiny.en, base, base.en,`<br>`small, small.en, medium,`<br>`medium.en, large, large-v1,`<br>`large-v2, large-v3}` | Whisper model size to use (default: `large`) | `1` | `False` |
| `-v`, `--verbose` | Integer (count) | Increase verbosity level | `0+` | `False` |
| `-w`, `--suppress-warnings` | Flag | Suppress warnings from constituent libraries and models | `0` | `False` |
| `-h`, `--help` | N/A | Show help message and quit | `0,1` | `False` |

## Setup
### Hardware requirements
_The values below pertain to the `large` model; smaller models require less VRAM/RAM._
| Part | Minimum | Recommended |
| :--- | :------ | :---------- |
| Inference on GPU | CUDA-enabled GPU with 8GB VRAM | RTX GPU with 12 GB VRAM |
| Inference on CPU | 16 GB RAM | N/A |

### Recording
For maximum accuracy of speaker recognition, use a multi-stream recording solution such as [Craig](https://craig.chat/), preferably hosted locally to maintain maximum control over your privacy.
The reason for this recomendation is higher overall difficulty of diarization as a task, compared to simply sorting multiple audio stream contents by timestamp.