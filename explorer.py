"""
resource_sniffer.py
资源嗅探：从页面中提取可下载的媒体资源
"""

import re
from urllib.parse import urljoin
from typing import List, Dict, Optional


class ResourceSniffer:
    """从 Scrapling 的 page 对象中嗅探媒体资源"""

    # 流媒体特征
    STREAM_PATTERNS = [
        (r'["\']([^"\']*\.m3u8[^"\']*)["\']', "HLS"),
        (r'["\']([^"\']*\.mpd[^"\']*)["\']', "DASH"),
    ]

    # 直链媒体扩展名
    DIRECT_EXTENSIONS = {
        ".mp4", ".webm", ".mkv", ".avi", ".mov",
        ".mp3", ".m4a", ".wav", ".flac",
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    }

    @classmethod
    def sniff(cls, page, base_url: str,
              include_images: bool = False) -> List[Dict]:
        """
        从页面中嗅探所有可下载资源。

        Returns:
            [{
                "type": "stream" | "direct",
                "stream_type": "HLS" | "DASH" | None,
                "url": 绝对 URL,
                "title": 文件名或描述,
                "ext": 扩展名
            }]
        """
        resources = []
        seen = set()

        # 1. 流媒体：从 HTML 中正则提取
        html = page.html or ""
        for pattern, stream_type in cls.STREAM_PATTERNS:
            for match in re.findall(pattern, html, re.IGNORECASE):
                full_url = urljoin(base_url, match)
                if full_url not in seen:
                    seen.add(full_url)
                    resources.append({
                        "type": "stream",
                        "stream_type": stream_type,
                        "url": full_url,
                        "title": full_url.split("/")[-1].split("?")[0],
                        "ext": "." + stream_type.lower(),
                    })

        # 2. 直链媒体：从标签中提取
        tag_selectors = ["video[src]", "audio[src]", "source[src]"]
        if include_images:
            tag_selectors.append("img[src]")

        for selector in tag_selectors:
            for el in page.css(selector):
                src = el.attrib.get("src")
                if not src:
                    continue
                full_url = urljoin(base_url, src)
                if full_url in seen:
                    continue

                ext = cls._get_extension(full_url)
                if ext and ext in cls.DIRECT_EXTENSIONS:
                    seen.add(full_url)
                    resources.append({
                        "type": "direct",
                        "stream_type": None,
                        "url": full_url,
                        "title": src.split("/")[-1].split("?")[0],
                        "ext": ext,
                    })

        # 3. 从页面链接中嗅探直链资源
        for link in page.css("a[href]"):
            href = link.attrib.get("href", "")
            if not href:
                continue
            full_url = urljoin(base_url, href)
            if full_url in seen:
                continue
            ext = cls._get_extension(full_url)
            if ext and ext in cls.DIRECT_EXTENSIONS:
                seen.add(full_url)
                resources.append({
                    "type": "direct",
                    "stream_type": None,
                    "url": full_url,
                    "title": link.text.strip() or href.split("/")[-1].split("?")[0],
                    "ext": ext,
                })

        return resources

    @staticmethod
    def _get_extension(url: str) -> Optional[str]:
        """从 URL 中提取小写扩展名"""
        path = url.split("?")[0].split("#")[0]
        if "." in path.split("/")[-1]:
            return "." + path.split("/")[-1].rsplit(".", 1)[-1].lower()
        return None