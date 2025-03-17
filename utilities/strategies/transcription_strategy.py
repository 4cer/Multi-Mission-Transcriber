from abc import ABC, abstractmethod
import pyannote.pipeline
import whisperx
import pyannote.audio
import torch
import torchaudio
import numpy as np
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, fcluster
import subprocess
import glob
import shutil
import os
import json
import datetime, time
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import math

import librosa
import sounddevice as sd


class TranscriptionStrategy(ABC):
    @abstractmethod
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        pass

    def _format_time(self, seconds):
        if seconds == None:
            return "--:--:--:---"
        td = datetime.timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{seconds:06.3f}"

    def _generate_outputs(self, input_files: list[str], output_dir: str, output_types: list[str], segments: list[dict]):
        """DiarizedSingleStreamStrategy"""
        base_name = os.path.splitext(os.path.basename("_".join(input_files)))[0]
        now = int(time.time())
        if 'json' in output_types:
            json_path = os.path.join(output_dir, f"{now}_{base_name}.json")
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
        if 'text' in output_types:
            text_path = os.path.join(output_dir, f"{now}_{base_name}.txt")
            with open(text_path, 'w', encoding='utf-8') as f:
                for seg in segments:
                    start_str = self._format_time(seg["start"])
                    end_str = self._format_time(seg.get("end",None))
                    f.write(f"[{start_str} / {end_str}] ({seg.get('speaker', 'N/A')}):\n{seg['text'].strip()}\n\n")
        if 'dense' in output_types:
            text_dense_path = os.path.join(output_dir, f"{now}_{base_name}.dense.txt")
            with open(text_dense_path, 'w', encoding='utf-8') as f:
                for seg in segments:
                    start_str = self._format_time(seg["start"])
                    end_str = self._format_time(seg.get("end",None))
                    f.write(f"[{start_str} / {end_str}] ({seg.get('speaker', 'N/A')}): {seg['text'].strip()}\n")
        if 'raw' in output_types:
            text_raw_path = os.path.join(output_dir, f"{now}_{base_name}.raw.txt")
            with open(text_raw_path, 'w', encoding='utf-8') as f:
                for seg in segments:
                    f.write(f"{seg['text']}\n")

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
    
    def _cleanup_clips(self, clips, clip_dir):
        for clip in clips:
            os.path.join(clip_dir, clip)
            try:
                os.remove(clip)
            except Exception as e:
                print(e)


class NonDiarizedSingleStreamStrategy(TranscriptionStrategy):
    """Transcribes single or multi-stream audio as a single speaker."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        model = whisperx.load_model("large", device="cuda", compute_type="float16", language=language)
        model.options.initial_prompt = initial_prompt
        for input_file in input_files:
            result = model.transcribe(input_file, print_progress=True)
            segments = result["segments"]
            self._generate_outputs([input_file], output_dir, output_types, segments)


class DiarizedMultiClipTest(TranscriptionStrategy):
    """Test for diarization sliding window with multiple files"""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        pipeline = pyannote.audio.Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1"
        ).to(torch.device('cuda'))

        diarizations = []
        embeddings = []
        for file in input_files:
            diarization, embedding = pipeline(file, return_embeddings=True)
            diarizations.append(diarization)
            embeddings.append(embedding)

        # TODO if more than 1 file, do embedding matching
        

    def process2(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        step = 1.0
        duration = 3.0
        embedding_model = pyannote.audio.Inference("pyannote/embedding", device=torch.device("cuda"), window="sliding", duration=duration, step=step, batch_size=64)
        vad_model = load_silero_vad()

        embedding_list = []
        file_limits = []
        nowlimit = 0
        for file in input_files:
            print("[Running VAD]", file)
            wav = read_audio(file)
            speech_timestamps = get_speech_timestamps(
                wav,
                vad_model,
                return_seconds=True,
            )
            print("[Extracting embeddings]", file)
            embeddings = embedding_model(file)
            print("[Separating silence embeddings]", file)
            silence = []
            for st in speech_timestamps:
                # start_i = math.ceil(st.get("start") / step)
                # end_i = math.floor((st.get("end") - duration) / step)
                silence.extend(range(*self.duration_timestamps_to_indices(st.get("start"), st.get("end"), step, duration)))
            embeddings.data[silence] = 9999.0
            embedding_list.append(embeddings.data)
            file_limits.append((nowlimit, file))
            nowlimit += embeddings.data.shape[0]
        
        concatted = np.concatenate(embedding_list, axis=0)

        print(concatted.shape)

        dist_matrix = pdist(concatted, metric='cosine')
        print("DIST MATRIX", dist_matrix.shape)

        linkage_matrix = linkage(dist_matrix, method='average')
        print("LINKAGE MATRIX", linkage_matrix.shape)

        # clusters = fcluster(linkage_matrix, t=0.9, criterion='distance')
        clusters = fcluster(linkage_matrix, t=9, criterion='maxclust')
        print("FCLUSTER", clusters.shape)

        identites = np.unique(clusters)
        print(identites)

        longest_blocks = []
        for idn in identites:
            si, ei = self.largest_consecutive_block_N(clusters, idn)
            start_t, end_t = self.duration_indices_to_timestamps(si,ei,step,duration)
            start_file = self.which_file(file_limits, si); end_file = self.which_file(file_limits, ei)
            print(f"{idn}\n{si:<13} - {ei:<13}\n{start_t} - {end_t}\n{start_file}\n{end_file}")
            # TODO Handle split between two files
            longest_blocks.append({'identity': idn ,'start_i': si, 'end_i': ei, 'start_t': start_t, 'end_t': end_t, 'file': start_file})
        
        longest_blocks.sort(key=lambda a: a.get('file'))

        file_now = None
        wav = None
        sample_rate = None
        for lb in longest_blocks:
            if file_now != lb.get('file') or file_now == None:
                file_now = lb.get('file')
                sample_rate = torchaudio.info(file_now).sample_rate
            start_t = lb.get('start_t'); end_t = lb.get('end_t')
            print("Identity", lb.get('identity'))
            self.play_file_fragment(file_now, start_t, end_t)

    @staticmethod
    def play_file_fragment(file_path, start_t, end_t):
        audio_fragment, sampling_rate = librosa.load(
            file_path, offset=start_t, duration=end_t - start_t
        )
        sd.play(audio_fragment, sampling_rate)
        sd.wait()  # Wait until playback finishes
        input("Press Enter to continue...")  # Wait for user input

    @staticmethod
    def which_file(file_limits: list[tuple[int,str]], index: int):
        for lim in file_limits:
            if index > lim[0]:
                return lim[1]

    @staticmethod
    def duration_timestamps_to_indices(start_time_s: float, end_time_s: float, step: float, duration: float) -> int | int:
        start_i = math.ceil(start_time_s / step)
        end_i = math.floor((end_time_s - duration) / step)
        return start_i, end_i
    
    @staticmethod
    def duration_indices_to_timestamps(start_index: int, end_index: int, step: float, duration: float) -> float | float:
        start_time_s = float(start_index * step)
        end_time_s = float(end_index * step + duration)
        return start_time_s, end_time_s
    
    @staticmethod
    def largest_consecutive_block_N(arr: np.ndarray, val: int) -> int | int:
        # Find all indices where the array equals the target value
        indices = np.where(arr == val)[0]
        
        # Handle case where the value is not present
        if len(indices) == 0:
            return (-1, -1)
        
        # Handle case where there's only one occurrence
        if len(indices) == 1:
            return (indices[0], indices[0])
        
        # Compute differences between consecutive indices to find breaks
        diffs = np.diff(indices)
        # Determine where the consecutive sequence breaks (difference > 1)
        split_positions = np.where(diffs != 1)[0] + 1
        # Split the indices into groups of consecutive sequences
        groups = np.split(indices, split_positions)
        
        max_start = indices[0]
        max_end = indices[0]
        max_length = 1
        
        for group in groups:
            if group.size == 0:
                continue
            start = group[0]
            end = group[-1]
            current_length = end - start + 1
            if current_length > max_length:
                max_length = current_length
                max_start = start
                max_end = end
        
        return max_start, max_end


class DiarizedSingleStreamStrategy(TranscriptionStrategy):
    """Transcribes single-stream audio with speaker diarization."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        model = whisperx.load_model("large", device="cuda", compute_type="float16", language=language)
        model.options.initial_prompt = initial_prompt
        embedding_model = pyannote.audio.Inference("pyannote/embedding", device=torch.device("cuda"))
        for input_file in input_files:
            clips = self._handle_large_files(input_file, clip_dir)
            all_segments = []
            for clip_path in clips:
                result = model.transcribe(clip_path, tqdm_progress=True)
                segments = result["segments"]
                for segment in segments:
                    sample_rate = torchaudio.info(clip_path).sample_rate
                    waveform, _ = torchaudio.load(clip_path, frame_offset=int(segment["start"] * sample_rate), num_frames=int((segment["end"] - segment["start"]) * sample_rate))
                    embedding_tensor = embedding_model({"waveform": waveform, "sample_rate": sample_rate})
                    embedding = embedding_tensor.data.mean(axis=0)
                    all_segments.append({"start": segment["start"], "end": segment["end"], "text": segment["text"], "embedding": embedding})
            if all_segments:
                embeddings = np.array([seg["embedding"].data for seg in all_segments])
                dist_matrix = pdist(embeddings, metric='cosine')
                linkage_matrix = linkage(dist_matrix, method='average')
                clusters = fcluster(linkage_matrix, t=0.5, criterion='distance')
                unique_clusters = np.unique(clusters)
                speaker_map = {cluster: f"Speaker {i+1}" for i, cluster in enumerate(unique_clusters)}
                for i, segment in enumerate(all_segments):
                    segment["speaker"] = speaker_map[clusters[i]]
                    del segment["embedding"]
                sorted_segments = sorted(all_segments, key=lambda x: x["start"])
                self._generate_outputs([input_file], output_dir, output_types, sorted_segments)


class NonDiarizedMultiStreamStrategy(TranscriptionStrategy):
    """Transcribes multi-stream audio, each stream as a different speaker."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        model = whisperx.load_model("large", device="cuda", compute_type="float16", language=language)
        model.options.initial_prompt = initial_prompt
        for idx, input_file in enumerate(input_files):
            speaker = f"Speaker {idx + 1}"
            result = model.transcribe(input_file, print_progress=True)
            segments = result["segments"]
            self._generate_outputs(input_file, output_dir, output_types, segments, speaker)


class NonDiarizedAlignedFilesStrategy(TranscriptionStrategy):
    """Transcribes multiple aligned files, each as a separate speaker, into a combined output."""
    def process(self, input_files, output_dir, clip_dir, initial_prompt, output_types, language, speakers_min, speakers_max, speaker_count):
        model = whisperx.load_model("large", device="cuda", compute_type="float16", language=language)
        model.options.initial_prompt = initial_prompt
        all_segments = []
        for idx, input_file in enumerate(input_files):
            speaker = f"Speaker {idx + 1}"
            result = model.transcribe(input_file, print_progress=True)
            segments = result["segments"]
            for seg in segments:
                all_segments.append({"start": seg["start"], "end": seg["end"], "text": seg["text"], "speaker": speaker})
        sorted_segments = sorted(all_segments, key=lambda x: x["start"])
        self._generate_outputs(input_files, output_dir, output_types, sorted_segments)

