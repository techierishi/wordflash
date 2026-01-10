import hashlib
from pathlib import Path
from typing import Optional

from gtts import gTTS


class AudioService:
    def __init__(self, output_dir: Path, language: str = "de"):
        self.output_dir = output_dir
        self.audio_dir = output_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)
        self.language = language

    def generate_audio(self, text: str) -> Optional[str]:
        try:
            audio_filename = self._get_audio_filename(text)
            audio_path = self.audio_dir / audio_filename

            if audio_path.exists():
                return str(audio_path)

            tts = gTTS(text=text, lang=self.language, slow=False)
            tts.save(str(audio_path))

            return str(audio_path)

        except Exception as e:
            print(f"Failed to generate audio for '{text}': {e}")
            return None

    def _get_audio_filename(self, text: str) -> str:
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        safe_text = "".join(c for c in text if c.isalnum() or c in "-_")[:20]
        return f"{safe_text}_{text_hash}.mp3"
