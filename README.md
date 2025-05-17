# Multi-Mission Transcriber (MMT)
Developed primarily for transcribing recordings of tabletop RPG sessions conducted over Discord or similar communication software.

## Usage
```
mmt.py [-h] -i INPUT [-o OUTPUT_DIRECTORY] [-b OUTPUT_BASE_NAME] [-c CLIP_DIRECTORY] -s {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda,test} [-t {string,directory,str,dir}] [-p PROMPT] -f {json,text,dense,raw}
              [{json,text,dense,raw} ...] [-l {pl, en, polish, english, ...}] [-m SPEAKERS_MIN] [-x SPEAKERS_MAX] [-e SPEAKER_COUNT] [-v] [-w]

Diarize and transcribe Discord conversation recordings

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input audio file(s)
  -o OUTPUT_DIRECTORY, --output-directory OUTPUT_DIRECTORY
                        Output directory for final results
  -b OUTPUT_BASE_NAME, --output-base-name OUTPUT_BASE_NAME
                        Output file base name, extended with type and extension for each output type.
  -c CLIP_DIRECTORY, --clip-directory CLIP_DIRECTORY
                        Intermediate clip directory for split files
  -s {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda,test}, --strategy {non-diarized-single,diarized-single,non-diarized-multi,non-diarized-aligned,nds,ds,ndm,nda,test}
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
```

### Example usage with aligned clips and a directory prompt in Polish
```Powershell
python mmt.py `
    -i "files\file1.aac" `
    -i "files\file2.aac" `
    -i "files\file3.aac" `
    -i "files\file4.aac" `
    -i "files\file5.aac" `
    -i "files\file6.aac" `
    --strategy nda `
    --prompt-type directory `
    --prompt prompt/some_prompt `
    --output-types json text dense raw `
    --language pl `
    --output-base-name "Name of output"
```

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