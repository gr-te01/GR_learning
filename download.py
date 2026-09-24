"""
download_engine.py
下载器：直链下载 + 流媒体下载（基于 yt-dlp 兜底）
"""

import os
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Callable, Dict, List
from queue import Queue
import yt_dlp
import logging

logger = logging.getLogger(__name__)


class DownloadTask:
    """下载任务描述"""
    def __init__(self, url: str, save_path: str,
                 resource_type: str = "direct",
                 headers: Optional[Dict] = None):
        self.url = url
        self.save_path = save_path
        self.resource_type = resource_type
        self.headers = headers or {}


class DirectDownloader:
    """直链文件下载，支持多线程分片"""

    def __init__(self, max_workers: int = 4, chunk_size: int = 8192):
        self.max_workers = max_workers
        self.chunk_size = chunk_size

    def download(self, task: DownloadTask,
                 progress_cb: Optional[Callable] = None) -> str:
        """
        执行下载。

        Args:
            task: DownloadTask 对象
            progress_cb: 进度回调 (downloaded_bytes, total_bytes)

        Returns:
            保存路径
        """
        headers = task.headers.copy() if task.headers else {}
        headers.setdefault("User-Agent", "Mozilla/5.0")

        # 获取文件大小
        total = self._get_content_length(task.url, headers)

        os.makedirs(os.path.dirname(task.save_path) or ".", exist_ok=True)

        if total and total > 1024 * 1024:  # 大于 1MB 用分片
            return self._download_multipart(task, headers, total, progress_cb)
        else:
            return self._download_single(task, headers, progress_cb)

    def _get_content_length(self, url: str, headers: Dict) -> int:
        try:
            resp = requests.head(url, headers=headers,
                                 allow_redirects=True, timeout=10)
            return int(resp.headers.get("Content-Length", 0))
        except Exception:
            return 0

    def _download_single(self, task: DownloadTask, headers: Dict,
                         progress_cb) -> str:
        resp = requests.get(task.url, headers=headers,
                            stream=True, timeout=30)
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0

        with open(task.save_path, "wb") as f:
            for chunk in resp.iter_content(self.chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)
        return task.save_path

    def _download_multipart(self, task: DownloadTask, headers: Dict,
                            total: int, progress_cb) -> str:
        chunk_size = total // self.max_workers
        ranges = []
        for i in range(self.max_workers):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < self.max_workers - 1 else total - 1
            ranges.append((start, end))

        parts = []
        downloaded_lock = threading.Lock()
        downloaded = [0]

        def download_chunk(start, end, idx):
            h = headers.copy()
            h["Range"] = f"bytes={start}-{end}"
            resp = requests.get(task.url, headers=h,
                                stream=True, timeout=30)
            part_path = f"{task.save_path}.part{idx}"
            with open(part_path, "wb") as f:
                for chunk in resp.iter_content(self.chunk_size):
                    f.write(chunk)
                    with downloaded_lock:
                        downloaded[0] += len(chunk)
                        if progress_cb:
                            progress_cb(downloaded[0], total)
            return part_path

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = [ex.submit(download_chunk, s, e, i)
                       for i, (s, e) in enumerate(ranges)]
            for fut in as_completed(futures):
                parts.append(fut.result())

        # 合并分片
        parts.sort(key=lambda p: int(p.rsplit(".part", 1)[-1]))
        with open(task.save_path, "wb") as out:
            for part in parts:
                with open(part, "rb") as f:
                    out.write(f.read())
                os.remove(part)

        return task.save_path


class StreamDownloader:
    """流媒体下载（m3u8 / mpd），基于 yt-dlp"""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_path

    def download(self, task: DownloadTask,
                 progress_cb: Optional[Callable] = None) -> str:
        """
        下载流媒体，yt-dlp 自动处理 m3u8 分片 + ffmpeg 合并。
        """
        os.makedirs(os.path.dirname(task.save_path) or ".", exist_ok=True)

        def ytdlp_hook(d):
            if progress_cb and d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                progress_cb(downloaded, total)

        ydl_opts = {
            "outtmpl": task.save_path,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [ytdlp_hook],
            "concurrent_fragment_downloads": 8,
            "merge_output_format": "mp4",
        }

        if self.ffmpeg_path:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_path

        if task.headers:
            # yt-dlp 通过 --add-header 传递
            ydl_opts["http_headers"] = task.headers

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([task.url])

        return task.save_path


class DownloadManager:
    """下载管理器：队列 + 线程池"""

    def __init__(self, max_direct_workers: int = 2,
                 max_stream_workers: int = 1):
        self.direct_downloader = DirectDownloader()
        self.stream_downloader = StreamDownloader()
        self.direct_pool = ThreadPoolExecutor(max_workers=max_direct_workers)
        self.stream_pool = ThreadPoolExecutor(max_workers=max_stream_workers)
        self._futures = {}

    def submit(self, task: DownloadTask,
               progress_cb: Optional[Callable] = None):
        """提交下载任务，返回 Future"""
        if task.resource_type == "stream":
            fut = self.stream_pool.submit(
                self.stream_downloader.download, task, progress_cb)
        else:
            fut = self.direct_pool.submit(
                self.direct_downloader.download, task, progress_cb)
        self._futures[fut] = task
        return fut

    def shutdown(self, wait: bool = True):
        self.direct_pool.shutdown(wait=wait)
        self.stream_pool.shutdown(wait=wait)