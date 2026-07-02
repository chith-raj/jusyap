from __future__ import annotations

import tempfile
import threading
import wave
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate: int, channels: int = 1, device: Optional[str] = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._stream is not None:
                return
            self._frames = []
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                device=self.device,
                callback=self._callback,
            )
            self._stream.start()

    def stop_to_wav(self) -> Path:
        with self._lock:
            if self._stream is None:
                raise RuntimeError("Recorder is not running")
            self._stream.stop()
            self._stream.close()
            self._stream = None

            if not self._frames:
                raise RuntimeError("No audio captured")

            audio = np.concatenate(self._frames, axis=0)
            audio = np.clip(audio, -1.0, 1.0)
            pcm = (audio * 32767).astype(np.int16)

        temp_file = tempfile.NamedTemporaryFile(
            prefix="yapr-", suffix=".wav", delete=False
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        with wave.open(str(temp_path), "wb") as wav:
            wav.setnchannels(self.channels)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm.tobytes())

        return temp_path

    def is_recording(self) -> bool:
        return self._stream is not None

    def _callback(self, indata, frames, time, status) -> None:  # noqa: ANN001
        if status:
            print(f"Audio warning: {status}", flush=True)
        self._frames.append(indata.copy())
