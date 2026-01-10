import hashlib
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import requests


class ImageService:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.images_dir = output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)

    def download_image(self, word: str) -> Optional[str]:
        try:
            image_filename = self._get_image_filename(word)
            image_path = self.images_dir / image_filename

            if image_path.exists():
                return str(image_path)

            image_url = self._search_image(word)
            if not image_url:
                return None

            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            with open(image_path, "wb") as f:
                f.write(response.content)

            return str(image_path)

        except Exception as e:
            print(f"Failed to download image for '{word}': {e}")
            return None

    def _search_image(self, query: str) -> Optional[str]:
        try:
            params = {
                "q": query,
                "client": "firefox-b-d",
                "source": "lnms",
                "tbm": "isch",
                "sa": "X",
                "ved": "2ahUKEwiA-aW_8aL3AhVCwoUKHQOQBpwQ_AUoAXoECAEQAw",
                "biw": "1920",
                "bih": "1080",
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            pixabay_url = f"https://pixabay.com/api/?key=9656065-a4094594c34f9ac14c7fc4c39&q={query}&image_type=photo&category=all&min_width=400&per_page=3&safesearch=true"

            try:
                response = requests.get(pixabay_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("hits"):
                        return data["hits"][0]["webformatURL"]
            except:
                pass

            unsplash_url = f"https://source.unsplash.com/400x300/?{query}"
            response = requests.head(unsplash_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return unsplash_url

            picsum_url = "https://picsum.photos/400/300"
            response = requests.head(picsum_url, timeout=10)
            if response.status_code == 200:
                return picsum_url

        except Exception as e:
            print(f"Error searching for image: {e}")

        return None

    def _get_image_filename(self, word: str) -> str:
        word_hash = hashlib.md5(word.encode()).hexdigest()[:8]
        safe_word = "".join(c for c in word if c.isalnum() or c in "-_")[:20]
        return f"{safe_word}_{word_hash}.jpg"
