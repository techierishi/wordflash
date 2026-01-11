import hashlib
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import requests


class ImageService:
    def __init__(self, output_dir: Path, auto_approve: bool = False):
        self.output_dir = output_dir
        self.images_dir = output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        self.auto_approve = auto_approve

    def download_image(self, word: str, manual_approval: bool = True) -> Optional[str]:
        try:
            image_filename = self._get_image_filename(word)
            image_path = self.images_dir / image_filename

            if image_path.exists():
                return str(image_path)

            if self.auto_approve or not manual_approval:
                image_url = self._search_image(word)
                if not image_url:
                    return None
                return self._save_image(image_url, image_path)

            image_urls = self._search_images_multiple(word)
            if not image_urls:
                return None

            for attempt, image_url in enumerate(image_urls, 1):
                response = requests.get(image_url, timeout=30)
                if response.status_code != 200:
                    continue

                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as tmp:
                    tmp.write(response.content)
                    tmp_path = tmp.name

                approved = self._show_image_for_approval(tmp_path, word, attempt)

                if approved:
                    with open(image_path, "wb") as f:
                        f.write(response.content)
                    Path(tmp_path).unlink()
                    return str(image_path)
                else:
                    Path(tmp_path).unlink()
                    if attempt == len(image_urls):
                        print(f"  ✗ No images approved for '{word}'")
                        return None
                    continue

            return None

        except Exception as e:
            print(f"Failed to download image for '{word}': {e}")
            return None

    def _show_image_for_approval(
        self, image_path: str, search_term: str, attempt: int
    ) -> bool:
        print(f"\n  Showing image {attempt}...")
        self._open_image(image_path)

        while True:
            approval = (
                input(f"  Approve this image for '{search_term}'? (y/n/skip): ")
                .strip()
                .lower()
            )
            if approval == "y":
                return True
            elif approval == "n":
                return False
            elif approval == "skip":
                return False
            else:
                print("  Enter 'y', 'n', or 'skip'")

    def _open_image(self, image_path: str) -> None:
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["open", image_path], check=True, timeout=5)
            elif system == "Windows":
                subprocess.run(["start", image_path], shell=True, check=True, timeout=5)
            elif system == "Linux":
                self._open_image_linux(image_path)
            else:
                print(f"  [Image saved temporarily - unsupported OS: {system}]")
        except subprocess.TimeoutExpired:
            print(f"  [Image viewer timed out]")
        except Exception as e:
            print(f"  [Could not open image: {e}]")

    def _open_image_linux(self, image_path: str) -> None:
        viewers = ["xdg-open", "eog", "display", "feh", "gpicview", "geeqie"]
        for viewer in viewers:
            try:
                subprocess.Popen(
                    [viewer, image_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except FileNotFoundError:
                continue
        print(f"  [Image saved temporarily - no viewer found. Install: apt install eog]")

    def _save_image(self, image_url: str, image_path: Path) -> Optional[str]:
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            with open(image_path, "wb") as f:
                f.write(response.content)
            return str(image_path)
        except Exception as e:
            print(f"Failed to save image: {e}")
            return None

    def _search_image(self, query: str) -> Optional[str]:
        images = self._search_images_multiple(query)
        return images[0] if images else None

    def _search_images_multiple(self, query: str) -> list[str]:
        urls = []
        try:
            pixabay_urls = self._pixabay_search(query)
            urls.extend(pixabay_urls)
        except:
            pass

        try:
            unsplash_url = f"https://source.unsplash.com/400x300/?{query}"
            response = requests.head(unsplash_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                urls.append(unsplash_url)
        except:
            pass

        try:
            picsum_url = "https://picsum.photos/400/300"
            response = requests.head(picsum_url, timeout=10)
            if response.status_code == 200:
                urls.append(picsum_url)
        except:
            pass

        return urls

    def _pixabay_search(self, query: str) -> list[str]:
        try:
            pixabay_url = f"https://pixabay.com/api/?key=9656065-a4094594c34f9ac14c7fc4c39&q={query}&image_type=photo&category=all&min_width=400&per_page=5&safesearch=true"
            response = requests.get(pixabay_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [hit["webformatURL"] for hit in data.get("hits", [])]
        except Exception as e:
            print(f"Error searching Pixabay: {e}")
        return []

    def _get_image_filename(self, word: str) -> str:
        word_hash = hashlib.md5(word.encode()).hexdigest()[:8]
        safe_word = "".join(c for c in word if c.isalnum() or c in "-_")[:20]
        return f"{safe_word}_{word_hash}.jpg"
