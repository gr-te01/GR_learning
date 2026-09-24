"""
fetcher_engine.py
爬虫引擎：基于 Scrapling，负责页面抓取和自适应解析
"""

from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class FetcherEngine:
    """页面抓取引擎，支持三种模式"""

    MODE_FAST = "fast"        # 静态页面，速度最快
    MODE_STEALTH = "stealth"  # 反爬拦截，绕过 Cloudflare
    MODE_DYNAMIC = "dynamic"  # JS 渲染，SPA 页面

    def __init__(self, adaptive: bool = True, adaptive_domain: str = None):
        """
        Args:
            adaptive: 是否启用自适应元素追踪
            adaptive_domain: 自适应数据的域名标识，用于跨子域共享
        """
        self.adaptive = adaptive
        self.adaptive_domain = adaptive_domain

    def fetch(self, url: str, mode: str = MODE_FAST,
              headers: Optional[Dict] = None,
              cookies: Optional[Dict] = None,
              proxy: Optional[str] = None,
              **kwargs) -> Any:
        """
        抓取页面。

        Returns:
            Scrapling Response 对象，包含 .status / .css() / .html / .text 等
        """
        common_opts = {
            "impersonate": "chrome",
            "stealthy_headers": True,
            "follow_redirects": True,
        }
        if headers:
            common_opts["headers"] = headers
        if cookies:
            common_opts["cookies"] = cookies
        if proxy:
            common_opts["proxy"] = proxy

        # 合并额外参数
        common_opts.update(kwargs)

        try:
            if mode == self.MODE_STEALTH:
                # 绕过 Cloudflare Turnstile
                page = StealthyFetcher.fetch(
                    url,
                    headless=True,
                    solve_cloudflare=True,
                    network_idle=True,
                    **common_opts,
                )
            elif mode == self.MODE_DYNAMIC:
                # JS 渲染页面
                page = DynamicFetcher.fetch(
                    url,
                    headless=True,
                    network_idle=True,
                    **common_opts,
                )
            else:
                # 静态页面，最快
                page = Fetcher.get(url, **common_opts)

            logger.info(f"Fetched {url} [{mode}] -> {page.status}")
            return page

        except Exception as e:
            logger.error(f"Fetch failed: {url} -> {e}")
            raise

    def fetch_with_fallback(self, url: str,
                            headers: Optional[Dict] = None,
                            cookies: Optional[Dict] = None,
                            proxy: Optional[str] = None) -> Any:
        """
        自动降级抓取：先快速模式，失败后依次尝试 dynamic / stealth。
        适合不确定目标站点防护等级的场景。
        """
        modes = [self.MODE_FAST, self.MODE_DYNAMIC, self.MODE_STEALTH]
        last_error = None

        for mode in modes:
            try:
                return self.fetch(url, mode=mode, headers=headers,
                                  cookies=cookies, proxy=proxy)
            except Exception as e:
                last_error = e
                logger.warning(f"Fallback: {mode} failed for {url}")

        raise last_error

    def parse(self, page, css_selector: str,
              auto_save: bool = False,
              adaptive: bool = False) -> List[Any]:
        """
        自适应解析：使用 Scrapling 的 auto_save / adaptive 机制。

        Args:
            page: fetch() 返回的 Response 对象
            css_selector: CSS 选择器
            auto_save: 首次使用时设为 True，保存元素特征
            adaptive: 网站改版后设为 True，自动重定位元素

        Returns:
            匹配的元素列表
        """
        opts = {}
        if auto_save:
            opts["auto_save"] = True
        if adaptive:
            opts["adaptive"] = True

        return page.css(css_selector, **opts)