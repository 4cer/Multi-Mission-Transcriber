# Multi-Mission Transcriber (MMT)
Developed primarily for transcribing recordings of tabletop RPG sessions conducted over Discord or similar communication software.

## Usage
`mmt.py [-h] -i INPUT [-o OUTPUT_DIRECTORY] [-c CLIP_DIRECTORY] -s {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda} [-t {string,directory}] [-p PROMPT] -f {json,text,dense,raw} [{json,text,dense,raw} ...] [-l {pl, en, polish, english, ...}]`

### Arguments
| Argument | Accepted Values | Description | Multiplicty | Required |
| :------- | :-------------- | :---------- | :---------: | :------: |
| `-i`, `--input` | Relative or absolute filepath | Input audio file(s) | `1+` | `True` |
| `-o`, `--output-directory` | Relative or absolute filepath | Output directory for final results | `1` | `False` |
| `-c`, `--clip-directory` | Relative or absolute filepath | Intermediate clip directory for split files | `1` | `False` |
| `-s`, `--strategy` | One of<br>`{non-diarized-single,`<br>`diarized-single,`<br>`non-diarized-multi,`<br>`non-diarized-aligned,`<br>`nds, ds, ndm, nda}` | Transcription strategy | `1` | `True` |
| `-t`, `--prompt-type` | One of<br>`{string,directory}` | Type of initial prompt (string or directory) | `1` | `False` |
| `-p`, `--prompt` | For prompt type `string`:<br>String of length 1024 characters or less<br>For prompt type `directory`:<br>Relative or absolute directory path | Initial prompt string or directory path | `1` | `False` |
| `-f`, `--output-types` | One or more of:<br>`{json,text,dense,raw}` | Output types (json', 'text', 'dense', 'raw' or any combination) | `1+` | `True` |
| `-l`, `--language` | {pl, en, polish, english, ...} | Language presumed for the entire recording  | `0+` | `False` |
| `-h`, `--help` | N/A | Show help message and quit | `0,1` | `False` |

## Setup
### Hardware requirements
| Part | Minimum | Recommended |
| :--- | :------ | :---------- |
| Inference on GPU | CUDA-enabled GPU with 8GB VRAM | RTX GPU with 12 GB VRAM |
| Inference on CPU | 16 GB RAM | N/A |

### Recording
For maximum accuracy of speaker recognition, use a multi-stream recording solution such as [Craig](https://craig.chat/), preferably hosted locally to maintain maximum control over your privacy.
The reason for this recomendation is higher overall difficulty of diarization as a task, compared to simply sorting multiple audio stream contents by timestamp.