import torch
import whisper
from pyannote.audio import Pipeline
from pyannote.core import Segment
import subprocess
from datetime import datetime
import numpy as np
import os
from dotenv import dotenv_values

class AttrDict(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

audio_files = AttrDict()
audio_files.shortie = r"testfiles\Record 2025-02-20 at 21h48m57s.wav" # 2m 42s
audio_files.medium = r"testfiles\Record2023-11-22at13h33m15s.wav" # 1h 36m 1s
audio_files.long = r"testfiles\Record 2024-08-26 at 19h26m55s.wav" # 1h 36m 1s


# Configuration
WHISPER_MODEL = "medium"  # Use "small" if VRAM is tight
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"

def ensure_directories(args):
    # TODO Check if all input, output, clips, prompt exist; create otherwise
    pass

def assemble_init_prompt(prompt_parts_dir: str = "./prompt"):
    initial_prompt = "Nagranie sesji gry Dungeons & Dragons zawierające fantastyczne nazwy."
    for fname in os.listdir(prompt_parts_dir):
        if not fname.endswith(".list"):
            continue
        catname = fname.split(".")[0]
        fpath = os.path.join(prompt_parts_dir, fname)
        alles = list()
        with open(fpath, mode="r", encoding="utf-8") as file:
            alles = file.read().splitlines()
        catvals = ",".join(alles)
        initial_prompt += f" {catname}:{catvals}"
    print(len(initial_prompt), initial_prompt)
    return initial_prompt

def get_duration(input_file):
    cmd = [
        "ffprobe",
        "-i", input_file,
        "-show_entries",
        "format=duration",
        "-v", "quiet",
        "-of", "csv=p=0"
    ]
    completed = subprocess.run(cmd, check=True, stdout=subprocess.PIPE)
    duration_str = completed.stdout.decode().strip()
    duration = float(duration_str)
    return duration

def split_to_clips(input_file: str):
    output_files = []
    duration = get_duration(input_file)
    clip_duration = 3600
    output_path = r"clips"
    for start in range(0,int(duration),clip_duration):
        output_file = os.path.join(output_path, f"clip_{start}-{start+clip_duration}.wav")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_file,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-ss", f"{start}",
            "-t", f"{clip_duration}",
            output_file
        ]
        subprocess.run(cmd, check=True)
        output_files.append(output_file)
    return output_files

def convert_to_wav(input_file):
    """Convert any audio file to 16kHz WAV format using ffmpeg"""
    output_file = "temp_converted.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        "-t", "3600",
        output_file
    ]
    subprocess.run(cmd, check=True)
    return output_file

def transcribe_with_diarization(audio_file, config, initial_prompt):
    # Convert to proper format if necessary
    if not audio_file.endswith(".wav"):
        audio_file = convert_to_wav(audio_file)

    if get_duration(audio_file) > 3600:
        clips = split_to_clips(audio_file)
    else:
        clips = [audio_file]

    # Load models
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load diarization pipeline
    diarization_pipeline = Pipeline.from_pretrained(
        DIARIZATION_MODEL,
        use_auth_token=config["HF_TOKEN"]
    ).to(device)

    # Load Whisper model
    whisper_model = whisper.load_model(WHISPER_MODEL).to(device)

    # Perform diarization
    print("Performing speaker diarization...")
    diarization = diarization_pipeline(audio_file)

    # Perform transcription
    print("Transcribing audio...")
    result = whisper_model.transcribe(audio_file, word_timestamps=True, verbose=False, initial_prompt=initial_prompt)
    
    # Convert diarization results to list of segments
    diarization_segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        diarization_segments.append({
            "start": segment.start,
            "end": segment.end,
            "speaker": speaker
        })

    # Align whisper segments with diarization
    aligned_segments = []
    for segment in result["segments"]:
        seg_start = segment["start"]
        seg_end = segment["end"]
        
        # Find overlapping speaker segments
        speaker_candidates = []
        for diar_seg in diarization_segments:
            overlap_start = max(seg_start, diar_seg["start"])
            overlap_end = min(seg_end, diar_seg["end"])
            if overlap_end > overlap_start:
                speaker_candidates.append((
                    diar_seg["speaker"],
                    overlap_end - overlap_start
                ))
        
        # Select speaker with longest overlap
        if speaker_candidates:
            speaker = max(speaker_candidates, key=lambda x: x[1])[0]
        else:
            speaker = "UNKNOWN"

        aligned_segments.append({
            "start": seg_start,
            "end": seg_end,
            "speaker": speaker,
            "text": segment["text"]
        })

    return aligned_segments

def format_time(seconds):
    return str(datetime.utcfromtimestamp(seconds).strftime('%H:%M:%S'))

def format_datetime(seconds):
    return str(datetime.utcfromtimestamp(seconds).strftime('%y-%m%d_%H:%M:%S.%f'))

def save_output(segments, output_file="output\\transcript.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        current_speaker = None
        for seg in segments:
            if seg["speaker"] != current_speaker:
                f.write(f"\n\n[{seg['speaker']}] ({format_time(seg['start'])})\n")
                current_speaker = seg["speaker"]
            f.write(seg["text"] + " ")
    print(f"Transcript saved to {output_file}")

def main():
    import argparse

# Usage example
if __name__ == "__main__":
    print(split_to_clips(audio_files.long));exit()
    config = dotenv_values(".env")
    if not torch.cuda.is_available():
        print("WARNING CUDA UNAVAILABLE!")

    segments = transcribe_with_diarization(audio_files.long, config, assemble_init_prompt())
    save_output(segments, f"output\\transcript{format_datetime(datetime.now().timestamp())}.txt")