import hashlib
import platform
import subprocess
import tempfile
import time
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, quote

import requests


class ImageService:
    def __init__(self, output_dir: Path, auto_approve: bool = False, clipboard_only: bool = False):
        self.output_dir = output_dir
        self.images_dir = output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        self.auto_approve = auto_approve
        self.clipboard_only = clipboard_only

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
                print(f"  ✗ No images found for '{word}'")
                return None

            for attempt, image_url in enumerate(image_urls, 1):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                try:
                    response = requests.get(image_url, timeout=30, headers=headers)
                    if response.status_code != 200:
                        continue

                    with tempfile.NamedTemporaryFile(
                        suffix=".jpg", delete=False
                    ) as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name

                    approval = self._show_image_for_approval(tmp_path, word, attempt)

                    if approval == 1:
                        image_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(image_path, "wb") as f:
                            f.write(response.content)
                        Path(tmp_path).unlink()
                        return str(image_path)
                    elif approval == -1:
                        Path(tmp_path).unlink()
                        print(f"  ✗ Skipping Pixabay")
                        return self._get_image_from_clipboard(word, image_path)
                    else:
                        Path(tmp_path).unlink()
                        if attempt == len(image_urls):
                            print(f"  ✗ No images approved from Pixabay")
                            return self._get_image_from_clipboard(word, image_path)
                        continue
                except Exception as e:
                    print(f"  Error processing image {attempt}: {e}")
                    continue

            return None

        except Exception as e:
            print(f"Failed to download image for '{word}': {e}")
            return None

    def _get_image_from_clipboard(self, word: str, image_path: Path) -> Optional[str]:
        self._open_google_search(word)
        print(f"  Browser opened with Google search for '{word}'")
        time.sleep(1)
        clipboard_url = input("  Paste image URL from clipboard (or press Enter to skip): ").strip()
        if clipboard_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            try:
                clip_response = requests.get(clipboard_url, timeout=30, headers=headers)
                if clip_response.status_code == 200:
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(image_path, "wb") as f:
                        f.write(clip_response.content)
                    print(f"  ✓ Image saved from clipboard")
                    return str(image_path)
            except Exception as e:
                print(f"  ✗ Failed to download from clipboard: {e}")
        return None

    def _show_image_for_approval(
        self, image_path: str, search_term: str, attempt: int
    ) -> int:
        print(f"\n  Showing image {attempt}...")
        self._open_image(image_path)

        while True:
            approval = (
                input(f"  Approve this image for '{search_term}'? (y/n/s): ")
                .strip()
                .lower()
            )
            if approval == "y":
                return 1
            elif approval == "n":
                return 0
            elif approval == "s":
                return -1
            else:
                print("  Enter 'y', 'n', or 's' for skip.")

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

    def _open_google_search(self, query: str) -> None:
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}"
            webbrowser.open(search_url)
        except Exception as e:
            print(f"Could not open browser: {e}")

    def _save_image(self, image_url: str, image_path: Path) -> Optional[str]:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(image_url, timeout=30, headers=headers)
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
        
        if self.clipboard_only:
            try:
                print(f"\n  ⚠ Clipboard-only mode: Please provide image URL for '{query}'")
                self._open_google_search(query)
                print(f"  Browser opened with Google search for '{query}'")
                time.sleep(1)
                clipboard_url = input("  Paste image URL from clipboard: ").strip()
                if clipboard_url:
                    urls.append(clipboard_url)
                    print(f"  ✓ Added image from clipboard")
            except:
                pass
            return urls
        
        try:
            pixabay_urls = self._pixabay_search(query)
            urls.extend(pixabay_urls[:3])
            if pixabay_urls:
                print(f"  ✓ Pixabay: found {len(pixabay_urls)} images")
        except Exception as e:
            print(f"  ✗ Pixabay search failed: {e}")

        if len(urls) == 0:
            try:
                print(f"\n  ⚠ No images found for '{query}'")
                self._open_google_search(query)
                print(f"  Browser opened with Google search for '{query}'")
                time.sleep(1)
                clipboard_url = input("  Paste image URL from clipboard (or press Enter to skip): ").strip()
                if clipboard_url:
                    urls.append(clipboard_url)
                    print(f"  ✓ Added image from clipboard")
            except:
                pass

        return urls


    def _pixabay_search(self, query: str) -> list[str]:
        try:
            pixabay_url = f"https://pixabay.com/api/?key=9656065-a4094594c34f9ac14c7fc4c39&q={query}&image_type=photo&category=all&min_width=400&per_page=3&safesearch=true"
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
