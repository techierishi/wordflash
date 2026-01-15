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

                    approved = self._show_image_for_approval(tmp_path, word, attempt)

                    if approved:
                        image_path.parent.mkdir(parents=True, exist_ok=True)
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
                except Exception as e:
                    print(f"  Error processing image {attempt}: {e}")
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
        """Try various image viewers on Linux."""
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
        """Open Google search in default browser for the given query."""
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}"
            webbrowser.open(search_url)
        except Exception as e:
            print(f"Could not open browser: {e}")

    def _save_image(self, image_url: str, image_path: Path) -> Optional[str]:
        try:
            # Add headers to handle URLs that might require User-Agent
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
        """Search for images from Pixabay and Wikipedia Commons.
        
        Priority order (normal mode):
        1. Pixabay (up to 3 images)
        2. Wikipedia Commons (up to 3 images)
        3. User clipboard paste (if both sources fail)
        
        In clipboard_only mode, skips steps 1-2 and goes directly to user input.
        """
        urls = []
        
        # If clipboard_only mode, skip API searches and ask user directly
        if self.clipboard_only:
            try:
                print(f"\n  ⚠ Clipboard-only mode: Please provide image URL for '{query}'")
                self._open_google_search(query)
                print(f"  Browser opened with Google search for '{query}'")
                time.sleep(1)  # Wait for browser to open
                clipboard_url = input("  Paste image URL from clipboard: ").strip()
                if clipboard_url:
                    urls.append(clipboard_url)
                    print(f"  ✓ Added image from clipboard")
            except:
                pass
            return urls
        
        # Primary source: Pixabay (up to 3 results)
        try:
            pixabay_urls = self._pixabay_search(query)
            urls.extend(pixabay_urls[:3])
            if pixabay_urls:
                print(f"  ✓ Pixabay: found {len(pixabay_urls)} images")
        except Exception as e:
            print(f"  ✗ Pixabay search failed: {e}")

        # If Pixabay didn't find enough images, try Wikipedia Commons
        if len(urls) < 3:
            try:
                wiki_urls = self._wikipedia_commons_search(query)
                urls.extend(wiki_urls[:3])
                if wiki_urls:
                    print(f"  ✓ Wikipedia Commons: found {len(wiki_urls)} images")
            except:
                pass

        # If both sources failed, ask user to paste from clipboard
        if len(urls) == 0:
            try:
                print(f"\n  ⚠ No images found for '{query}' from Pixabay or Wikipedia Commons")
                self._open_google_search(query)
                print(f"  Browser opened with Google search for '{query}'")
                time.sleep(1)  # Wait for browser to open
                clipboard_url = input("  Paste image URL from clipboard (or press Enter to skip): ").strip()
                if clipboard_url:
                    urls.append(clipboard_url)
                    print(f"  ✓ Added image from clipboard")
            except:
                pass

        return urls


    def _pixabay_search(self, query: str) -> list[str]:
        """Search Pixabay for CC-licensed images (up to 3 results)."""
        try:
            pixabay_url = f"https://pixabay.com/api/?key=9656065-a4094594c34f9ac14c7fc4c39&q={query}&image_type=photo&category=all&min_width=400&per_page=3&safesearch=true"
            response = requests.get(pixabay_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [hit["webformatURL"] for hit in data.get("hits", [])]
        except Exception as e:
            print(f"Error searching Pixabay: {e}")
        return []

    def _wikipedia_commons_search(self, query: str) -> list[str]:
        """Search Wikipedia Commons for CC0/CC-BY licensed images (up to 3 results).
        
        This searches Wikipedia articles for the query term and extracts images
        from the article's images section.
        """
        try:
            wiki_api = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "titles": query.title(),
                "prop": "images",
                "imlimit": "10",
                "format": "json",
            }
            
            response = requests.get(wiki_api, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                image_urls = []
                
                # Extract image file names from the Wikipedia page
                for page in data.get("query", {}).get("pages", {}).values():
                    images = page.get("images", [])
                    if images:
                        # Try to get the actual image URLs from Commons
                        for image in images[:10]:
                            image_title = image.get("title", "").replace("File:", "").replace("Image:", "")
                            
                            # Skip images that are unlikely to be content images
                            if any(x in image_title.lower() for x in ["infobox", "navbox", "icon", "logo", "redirect"]):
                                continue
                            
                            # Get the image URL from Commons
                            try:
                                commons_api = "https://commons.wikimedia.org/w/api.php"
                                file_params = {
                                    "action": "query",
                                    "titles": f"File:{image_title}",
                                    "prop": "imageinfo",
                                    "iiprop": "url",
                                    "format": "json",
                                }
                                
                                file_response = requests.get(commons_api, params=file_params, timeout=10)
                                if file_response.status_code == 200:
                                    file_data = file_response.json()
                                    for file_page in file_data.get("query", {}).get("pages", {}).values():
                                        for img_info in file_page.get("imageinfo", []):
                                            url = img_info.get("url", "")
                                            # Filter for standard image formats
                                            if url and ("jpg" in url.lower() or "png" in url.lower()):
                                                image_urls.append(url)
                                                if len(image_urls) >= 3:
                                                    break
                            except:
                                continue
                            
                            if len(image_urls) >= 3:
                                break
                
                return image_urls[:3]
        except:
            pass
        
        return []




    def _get_image_filename(self, word: str) -> str:
        word_hash = hashlib.md5(word.encode()).hexdigest()[:8]
        safe_word = "".join(c for c in word if c.isalnum() or c in "-_")[:20]
        return f"{safe_word}_{word_hash}.jpg"
