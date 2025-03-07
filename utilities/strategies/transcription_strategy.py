from abc import ABC, abstractmethod
import whisperx
import pyannote.audio
import torchaudio
import numpy as np
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, fcluster
import subprocess
import glob
import shutil
import os
import json
import datetime

class TranscriptionStrategy(ABC):
    @abstractmethod
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types):
        pass

class NonDiarizedSingleStreamStrategy(TranscriptionStrategy):
    """Transcribes single or multi-stream audio as a single speaker."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types):
        model = whisperx.load_model("large", device="cuda", compute_type="float16")
        for input_file in input_files:
            result = model.transcribe(input_file, prompt=initial_prompt)
            segments = result["segments"]
            self._generate_outputs(input_file, output_dir, output_types, segments, speaker="Speaker")

    def _generate_outputs(self, input_file, output_dir, output_types, segments, speaker):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        if 'json' in output_types:
            json_path = os.path.join(output_dir, f"{base_name}.json")
            with open(json_path, 'w') as f:
                json.dump({"segments": [{"start": seg["start"], "end": seg["end"], "text": seg["text"], "speaker": speaker} for seg in segments]}, f, indent=2)
        if 'text' in output_types:
            text_path = os.path.join(output_dir, f"{base_name}.txt")
            with open(text_path, 'w') as f:
                for seg in segments:
                    start_str = self._format_time(seg["start"])
                    f.write(f"[{start_str}] {speaker}: {seg['text']}\n")

    def _format_time(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

class DiarizedSingleStreamStrategy(TranscriptionStrategy):
    """Transcribes single-stream audio with speaker diarization."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types):
        model = whisperx.load_model("large", device="cuda", compute_type="float16")
        embedding_model = pyannote.audio.Inference("pyannote/embedding", device="cuda")
        for input_file in input_files:
            clips = self._handle_large_files(input_file, clip_dir)
            all_segments = []
            for clip_path in clips:
                result = model.transcribe(clip_path, prompt=initial_prompt)
                segments = result["segments"]
                for segment in segments:
                    waveform, sample_rate = torchaudio.load(clip_path, frame_offset=int(segment["start"] * sample_rate), num_frames=int((segment["end"] - segment["start"]) * sample_rate))
                    embedding = embedding_model({"waveform": waveform, "sample_rate": sample_rate})
                    all_segments.append({"start": segment["start"], "end": segment["end"], "text": segment["text"], "embedding": embedding})
            if all_segments:
                embeddings = np.array([seg["embedding"].numpy() for seg in all_segments])
                dist_matrix = pdist(embeddings, metric='cosine')
                linkage_matrix = linkage(dist_matrix, method='average')
                clusters = fcluster(linkage_matrix, threshold=0.5, criterion='distance')
                unique_clusters = np.unique(clusters)
                speaker_map = {cluster: f"Speaker {i+1}" for i, cluster in enumerate(unique_clusters)}
                for i, segment in enumerate(all_segments):
                    segment["speaker"] = speaker_map[clusters[i]]
                    del segment["embedding"]
                sorted_segments = sorted(all_segments, key=lambda x: x["start"])
                self._generate_outputs(input_file, output_dir, output_types, sorted_segments)

    def _handle_large_files(self, input_file, clip_dir):
        if os.path.getsize(input_file) > 1024 * 1024 * 1024:  # 1GB
            return self._split_audio(input_file, clip_dir)
        else:
            clip_path = os.path.join(clip_dir, "original" + os.path.splitext(input_file)[1])
            shutil.copy(input_file, clip_path)
            return [clip_path]

    def _split_audio(self, input_file, clip_dir, segment_time=3600):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        clip_subdir = os.path.join(clip_dir, base_name)
        os.makedirs(clip_subdir, exist_ok=True)
        output_pattern = os.path.join(clip_subdir, "clip%03d" + os.path.splitext(input_file)[1])
        cmd = ['ffmpeg', '-i', input_file, '-f', 'segment', '-segment_time', str(segment_time), '-c', 'copy', output_pattern]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return sorted(glob.glob(os.path.join(clip_subdir, "clip*")))

    def _generate_outputs(self, input_file, output_dir, output_types, segments):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        if 'json' in output_types:
            json_path = os.path.join(output_dir, f"{base_name}.json")
            with open(json_path, 'w') as f:
                json.dump({"segments": segments}, f, indent=2)
        if 'text' in output_types:
            text_path = os.path.join(output_dir, f"{base_name}.txt")
            with open(text_path, 'w') as f:
                for seg in segments:
                    start_str = self._format_time(seg["start"])
                    f.write(f"[{start_str}] {seg['speaker']}: {seg['text']}\n")

    def _format_time(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

class NonDiarizedMultiStreamStrategy(TranscriptionStrategy):
    """Transcribes multi-stream audio, each stream as a different speaker."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types):
        model = whisperx.load_model("large", device="cuda", compute_type="float16")
        for idx, input_file in enumerate(input_files):
            speaker = f"Speaker {idx + 1}"
            result = model.transcribe(input_file, prompt=initial_prompt)
            segments = result["segments"]
            self._generate_outputs(input_file, output_dir, output_types, segments, speaker)

    def _generate_outputs(self, input_file, output_dir, output_types, segments, speaker):
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        if 'json' in output_types:
            json_path = os.path.join(output_dir, f"{base_name}.json")
            with open(json_path, 'w') as f:
                json.dump({"segments": [{"start": seg["start"], "end": seg["end"], "text": seg["text"], "speaker": speaker} for seg in segments]}, f, indent=2)
        if 'text' in output_types:
            text_path = os.path.join(output_dir, f"{base_name}.txt")
            with open(text_path, 'w') as f:
                for seg in segments:
                    start_str = self._format_time(seg["start"])
                    f.write(f"[{start_str}] {speaker}: {seg['text']}\n")

    def _format_time(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

class NonDiarizedAlignedFilesStrategy(TranscriptionStrategy):
    """Transcribes multiple aligned files, each as a separate speaker, into a combined output."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types):
        model = whisperx.load_model("large", device="cuda", compute_type="float16")
        all_segments = []
        for idx, input_file in enumerate(input_files):
            speaker = f"Speaker {idx + 1}"
            result = model.transcribe(input_file, prompt=initial_prompt)
            segments = result["segments"]
            for seg in segments:
                all_segments.append({"start": seg["start"], "end": seg["end"], "text": seg["text"], "speaker": speaker})
        sorted_segments = sorted(all_segments, key=lambda x: x["start"])
        self._generate_outputs(output_dir, output_types, sorted_segments)

    def _generate_outputs(self, output_dir, output_types, segments):
        if 'json' in output_types:
            json_path = os.path.join(output_dir, "combined.json")
            with open(json_path, 'w') as f:
                json.dump({"segments": segments}, f, indent=2)
        if 'text' in output_types:
            text_path = os.path.join(output_dir, "combined.txt")
            with open(text_path, 'w') as f:
                for seg in segments:
                    start_str = self._format_time(seg["start"])
                    f.write(f"[{start_str}] {seg['speaker']}: {seg['text']}\n")

    def _format_time(self, seconds):
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"