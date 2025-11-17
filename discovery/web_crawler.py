"""Web crawler for discovering URLs and extracting content"""
import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict
from bs4 import BeautifulSoup
from core.logger import logger
from tqdm import tqdm


class WebCrawler:
    """Async web crawler for discovering URLs"""
    
    def __init__(self, config):
        self.config = config
        self.max_depth = config.get('discovery.max_depth', 2)
        self.max_pages = config.get('discovery.max_pages', 50)
        self.timeout = config.get('scanning.timeout', 10)
        self.user_agent = config.get('scanning.user_agent', 'SenSIt/1.0')
        self.visited_urls = set()
        self.discovered_urls = set()
        
    async def crawl(self, start_url: str) -> Dict[str, str]:
        """
        Crawl website starting from start_url
        Returns dict of {url: content}
        """
        logger.info(f"Starting web crawl from: {start_url}")
        
        # Parse base domain
        parsed = urlparse(start_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        self.domain = parsed.netloc
        
        # Initialize
        pages_content = {}
        to_visit = [(start_url, 0)]  # (url, depth)
        
        # Create progress bar
        with tqdm(total=min(self.max_pages, 100), desc="Crawling URLs", 
                  unit="page", ncols=80) as pbar:
            
            async with aiohttp.ClientSession() as session:
                while to_visit and len(self.visited_urls) < self.max_pages:
                    current_url, depth = to_visit.pop(0)
                    
                    # Skip if already visited
                    if current_url in self.visited_urls:
                        continue
                    
                    # Skip if max depth reached
                    if depth > self.max_depth:
                        continue
                    
                    # Fetch page
                    content = await self._fetch_page(session, current_url)
                    
                    if content:
                        self.visited_urls.add(current_url)
                        pages_content[current_url] = content
                        pbar.update(1)
                        
                        # Extract links if not at max depth
                        if depth < self.max_depth:
                            links = self._extract_links(content, current_url)
                            for link in links:
                                if link not in self.visited_urls:
                                    to_visit.append((link, depth + 1))
        
        logger.info(f"Crawl complete. Visited {len(self.visited_urls)} pages")
        return pages_content
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch a single page"""
        try:
            headers = {'User-Agent': self.user_agent}
            
            async with session.get(url, headers=headers, timeout=self.timeout, 
                                   ssl=False) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Only process HTML/text content
                    if 'text/html' in content_type or 'text/plain' in content_type:
                        return await response.text()
                    elif 'javascript' in content_type or 'json' in content_type:
                        return await response.text()
                    
        except asyncio.TimeoutError:
            logger.debug(f"Timeout fetching: {url}")
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
        
        return None
    
    def _extract_links(self, html_content: str, base_url: str) -> List[str]:
        """Extract links from HTML content"""
        links = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract from <a> tags
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                absolute_url = urljoin(base_url, href)
                
                # Only include same-domain links
                if self._is_same_domain(absolute_url):
                    # Remove fragments
                    clean_url = absolute_url.split('#')[0]
                    if clean_url and clean_url not in self.visited_urls:
                        links.append(clean_url)
            
            # Extract from <script> tags
            for tag in soup.find_all('script', src=True):
                src = tag['src']
                absolute_url = urljoin(base_url, src)
                
                if self._is_same_domain(absolute_url):
                    clean_url = absolute_url.split('#')[0]
                    if clean_url and clean_url not in self.visited_urls:
                        links.append(clean_url)
        
        except Exception as e:
            logger.debug(f"Error extracting links: {e}")
        
        return list(set(links))[:20]  # Limit to 20 links per page
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to same domain"""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain or parsed.netloc.endswith(f'.{self.domain}')
        except:
            return False
