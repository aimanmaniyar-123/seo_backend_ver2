# utils/url_extractor.py
"""
URL Content Extractor Utility for SEO Analysis
Extracts SEO-relevant data from any given URL
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin
import re


class URLContentExtractor:
    """Extracts comprehensive SEO data from URLs"""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

    def extract(self, url: str) -> Dict[str, Any]:
        """Extract all SEO-relevant data from URL"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {"error": "Invalid URL format. Include http:// or https://"}

            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            return {
                "url": url,
                "status_code": response.status_code,
                "text_content": self._extract_text(soup),
                "html_content": str(soup),
                "title": self._extract_title(soup),
                "meta_description": self._get_meta_tag(soup, 'description'),
                "meta_keywords": self._get_meta_tag(soup, 'keywords'),
                "h1_tags": [h.get_text(strip=True) for h in soup.find_all('h1')],
                "h2_tags": [h.get_text(strip=True) for h in soup.find_all('h2')],
                "h3_tags": [h.get_text(strip=True) for h in soup.find_all('h3')],
                "images": self._extract_images(soup, url),
                "internal_links": self._extract_internal_links(soup, url),
                "external_links": self._extract_external_links(soup, url),
                "schema_markup": self._extract_schema(soup),
                "page_size_kb": len(response.content) / 1024,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
            }

        except requests.exceptions.Timeout:
            return {"error": f"Request timeout after {self.timeout} seconds"}
        except requests.exceptions.ConnectionError:
            return {"error": "Failed to connect to the URL"}
        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP Error: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

    def _extract_text(self, soup) -> str:
        """Extract clean text content"""
        for script in soup(['script', 'style', 'noscript']):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _extract_title(self, soup) -> Optional[str]:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else None

    def _get_meta_tag(self, soup, name: str) -> Optional[str]:
        """Extract meta tag content"""
        meta = soup.find('meta', attrs={'name': name})
        if not meta:
            meta = soup.find('meta', attrs={'property': name})
        return meta.get('content') if meta else None

    def _extract_images(self, soup, base_url: str) -> List[Dict]:
        """Extract image information"""
        images = []
        for img in soup.find_all('img')[:20]:
            src = img.get('src')
            if src:
                absolute_url = urljoin(base_url, src)
                images.append({
                    'src': absolute_url,
                    'alt': img.get('alt', ''),
                    'has_alt': bool(img.get('alt'))
                })
        return images

    def _extract_internal_links(self, soup, base_url: str) -> List[Dict]:
        """Extract internal links"""
        base_domain = urlparse(base_url).netloc
        internal = []

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)

            if parsed.netloc == base_domain:
                internal.append({
                    'url': absolute_url,
                    'anchor_text': link.get_text(strip=True)
                })

        return internal[:50]

    def _extract_external_links(self, soup, base_url: str) -> List[Dict]:
        """Extract external links"""
        base_domain = urlparse(base_url).netloc
        external = []

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            absolute_url = urljoin(base_url, href)
            parsed = urlparse(absolute_url)

            if parsed.netloc and parsed.netloc != base_domain:
                external.append({
                    'url': absolute_url,
                    'anchor_text': link.get_text(strip=True)
                })

        return external[:30]

    def _extract_schema(self, soup) -> List[Dict]:
        """Extract JSON-LD schema markup"""
        schemas = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                schema_data = json.loads(script.string)
                schemas.append(schema_data)
            except:
                pass
        return schemas


# ------------------------------------------------------------
# Module-level wrapper so other files can call: url_extractor.extract(url)
def extract(url: str):
    extractor = URLContentExtractor()
    return extractor.extract(url)


# Global instance (optional shared extractor)
url_extractor = URLContentExtractor()
