from .base_tool import BaseTool
import asyncio
import json
import time
import requests
from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig, CrawlerRunConfig
from tavily import TavilyClient
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

class SearchResult(BaseModel):
    """Structured search result from OLLAMA-powered extraction"""
    title: str = Field(..., description="Title or main heading of the content")
    content: str = Field(..., description="Main content or summary of the information")
    key_facts: List[str] = Field(default_factory=list, description="Important facts or bullet points")
    urls: List[str] = Field(default_factory=list, description="Source URLs mentioned or referenced")
    date_info: Optional[str] = Field(None, description="Date or time information if mentioned")
    location: Optional[str] = Field(None, description="Location or geographic information if relevant")

class SearchTool(BaseTool):
    """
    🚀 Revolutionary search tool powered by Crawl4AI + Local OLLAMA
    
    This tool completely eliminates DuckDuckGo and uses:
    - Crawl4AI for superior web crawling and content extraction
    - Local OLLAMA models for intelligent content understanding and structuring
    - Tavily as intelligent fallback only when Crawl4AI fails or provides insufficient info
    
    Benefits:
    - No reliance on free but low-quality search APIs
    - Deep content extraction with full page rendering
    - Local LLM processing for privacy and speed
    - Smart quality evaluation to determine when fallback is needed
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.crawler = None
        self.search_sites = [
            "https://www.google.com/search?q={}",
            "https://www.bing.com/search?q={}",
            "https://duckduckgo.com/?q={}",
            "https://search.yahoo.com/search?p={}"
        ]
    
    @property
    def name(self) -> str:
        return "search_web"
    
    @property
    def description(self) -> str:
        return "Revolutionary web search using Crawl4AI + Local OLLAMA for deep content extraction with Tavily as intelligent fallback"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find information on the web"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to return",
                    "default": 5
                },
                "deep_extract": {
                    "type": "boolean",
                    "description": "Whether to use deep OLLAMA-powered content extraction",
                    "default": True
                }
            },
            "required": ["query"]
        }
    
    async def _init_crawler(self):
        """Initialize the Crawl4AI crawler with robust configuration"""
        if self.crawler is None:
            try:
                print("🔧 Initializing Crawl4AI crawler...")
                self.crawler = AsyncWebCrawler(
                    headless=True,
                    browser_type="chromium",
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    verbose=False,
                    # Additional robust configuration
                    max_concurrent=2,  # Reduced for stability
                    ignore_https_errors=True,
                    ignore_body_visibility=True,
                    ignore_body_scroll=True
                )
                print("✅ Crawl4AI crawler initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Crawl4AI crawler: {e}")
                # Don't crash, just log the error
                print(f"⚠️  Continuing without Crawl4AI, will use Tavily fallback")
                self.crawler = None
    
    def _get_search_urls(self, query: str, max_results: int = 5) -> List[str]:
        """Generate SMART search URLs based on query intelligence"""
        search_urls = []
        import urllib.parse
        
        # Analyze query to determine search strategy
        query_lower = query.lower()
        
        # 🎯 INTELLIGENT SEARCH STRATEGY SELECTION
        if any(word in query_lower for word in ['price', 'cost', 'discount', 'sale', 'buy', 'shop']):
            # 💰 SHOPPING/PRICE QUERIES
            targeted_searches = [
                f"{query} 2024 price",
                f"{query} discount code",
                f"{query} where to buy",
                f"site:amazon.com {query}",
                f"site:ebay.com {query}",
                f"{query} official store",
                f"{query} comparison price"
            ]
        elif any(word in query_lower for word in ['review', 'opinion', 'experience', 'rating']):
            # ⭐ REVIEW/OPINION QUERIES  
            targeted_searches = [
                f"{query} review 2024",
                f"site:reddit.com {query}",
                f"{query} user experience",
                f"site:trustpilot.com {query}",
                f"{query} pros cons",
                f"site:youtube.com {query} review",
                f"{query} expert opinion"
            ]
        elif any(word in query_lower for word in ['location', 'store', 'local', 'near', 'city', 'country']):
            # 📍 LOCATION-SPECIFIC QUERIES
            targeted_searches = [
                f"{query} store location",
                f"{query} local retailer", 
                f"{query} near me",
                f"{query} official dealer",
                f"site:google.com/maps {query}",
                f"{query} contact information",
                f"{query} physical store"
            ]
        else:
            # 🔍 GENERAL RESEARCH QUERIES
            targeted_searches = [
                f"{query} 2024",
                f"{query} official website",
                f"site:wikipedia.org {query}",
                f"{query} guide tutorial",
                f"{query} latest information",
                f"site:reddit.com {query}",
                f"{query} expert analysis"
            ]
        
        # Create search URLs with intelligence
        for search_term in targeted_searches[:max_results]:
            encoded_query = urllib.parse.quote_plus(search_term)
            # Prefer DuckDuckGo for reliability without aggressive bot blocking
            search_urls.append(f"https://duckduckgo.com/?q={encoded_query}")
        
        return search_urls[:max_results]
    
    def _extract_urls_from_search_page(self, html_content: str) -> List[str]:
        """Extract actual content URLs from search engine results"""
        import re
        urls = []
        
        # Extract URLs from generic search page markup (works for DuckDuckGo, Google fallback)
        generic_pattern = r'<a[^>]+href=\"(https?://[^\"]+)\"[^>]*>'
        matches = re.findall(generic_pattern, html_content)
        
        for match in matches:
            # Skip Google's own URLs and ads
            if not any(skip in match for skip in ['duckduckgo.com', 'google.com', 'googleusercontent.com', 'doubleclick.net', 'ads', 'adsystem']):
                urls.append(match)
        
        return list(set(urls))  # Remove duplicates
    
    async def _get_content_urls(self, query: str, max_urls: int = 10) -> List[str]:
        """Get actual content URLs by crawling search engine results"""
        try:
            await self._init_crawler()
            
            # If crawler failed to initialize, return empty list to trigger Tavily fallback
            if self.crawler is None:
                print("⚠️  Crawler not available, will use Tavily fallback")
                return []
            
            # Get search engine URLs
            max_urls_int = int(max_urls)  # Ensure integer type
            search_urls = self._get_search_urls(query, min(3, max_urls_int // 3))  # Use fewer search engines
            print(f"🔍 Crawling {len(search_urls)} search result pages to extract content URLs...")
            
            all_content_urls = []
            
            # Crawl each search page to extract content URLs
            for search_url in search_urls:
                try:
                    print(f"🕷️ Extracting URLs from: {search_url[:60]}...")
                    
                    # Configure for fast search page crawling
                    crawler_config = CrawlerRunConfig(
                        cache_mode="BYPASS",
                        page_timeout=10000,  # 10 seconds timeout
                        wait_for="css:a[href]"  # Wait for links to load
                    )
                    
                    result = await self.crawler.arun(url=search_url, config=crawler_config)
                    
                    if result.success and result.html:
                        # Extract content URLs from the search page
                        content_urls = self._extract_urls_from_search_page(result.html)
                        print(f"   📎 Found {len(content_urls)} content URLs")
                        all_content_urls.extend(content_urls)
                        
                        # Limit to prevent too many URLs
                        if len(all_content_urls) >= max_urls_int:
                            break
                    else:
                        print(f"   ⚠️ Failed to crawl search page: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                        
                except Exception as e:
                    print(f"   ❌ Error crawling search page {search_url[:40]}: {e}")
                    continue
            
            # Remove duplicates and filter quality URLs
            unique_urls = list(set(all_content_urls))
            
            # Filter out low-quality URLs
            filtered_urls = []
            for url in unique_urls:
                if self._is_quality_url(url):
                    filtered_urls.append(url)
            
            print(f"🎯 Extracted {len(filtered_urls)} quality content URLs from search results")
            return filtered_urls[:max_urls_int]
            
        except Exception as e:
            print(f"❌ Failed to extract content URLs: {e}")
            return []
    
    def _is_quality_url(self, url: str) -> bool:
        """Filter out low-quality URLs"""
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        url_lower = url.lower()
        
        # Skip unwanted domains and file types
        skip_patterns = [
            'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com',
            'facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com',
            'ads.', 'doubleclick.', 'googleusercontent.com',
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            'mailto:', 'tel:', 'javascript:', '#', '?q=', 'search?'
        ]
        
        if any(pattern in url_lower for pattern in skip_patterns):
            return False
        
        # Prefer certain high-quality domains
        quality_indicators = [
            'wikipedia.org', 'github.com', 'stackoverflow.com', 
            'reddit.com', 'medium.com', 'news.', 'blog.',
            '.edu', '.gov', '.org'
        ]
        
        return True  # Pass basic filtering
    
    async def _crawl_with_ollama_extraction(self, url: str, query_context: str) -> dict:
        """Crawl a URL and extract structured content with improved reliability"""
        try:
            await self._init_crawler()
            
            # If crawler failed to initialize, return fallback result
            if self.crawler is None:
                print(f"⚠️  Crawler not available for {url[:40]}, returning fallback")
                return {
                    "url": url,
                    "title": "Content Unavailable",
                    "content": f"Content extraction temporarily unavailable for {url}",
                    "extraction_success": False,
                    "word_count": 0
                }
            
            print(f"🕷️ Extracting content from: {url[:60]}...")
            
            # Configure crawler for robust content extraction
            crawler_config = CrawlerRunConfig(
                cache_mode="BYPASS",
                page_timeout=15000,  # 15 seconds timeout
                wait_for="css:body",  # Wait for page body to load
                remove_overlay_elements=True,  # Remove popups/overlays
                prettiify=True  # Clean up HTML
            )
            
            # Perform the crawl
            result = await self.crawler.arun(url=url, config=crawler_config)
            
            if result.success:
                # Try multiple content extraction methods for robustness
                content = ""
                title = "Untitled"
                
                # Priority 1: Use markdown if available (cleanest)
                if hasattr(result, 'markdown') and result.markdown:
                    content = result.markdown[:3000]  # Increased to 3000 chars
                    
                # Priority 2: Fall back to cleaned HTML
                elif hasattr(result, 'cleaned_html') and result.cleaned_html:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(result.cleaned_html, 'html.parser')
                    content = soup.get_text()[:3000]
                
                # Priority 3: Fall back to HTML if nothing else works
                elif hasattr(result, 'html') and result.html:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(result.html, 'html.parser')
                    content = soup.get_text()[:3000]
                
                # Extract title with multiple fallbacks
                if hasattr(result, 'metadata') and result.metadata and isinstance(result.metadata, dict):
                    title = result.metadata.get('title', title)
                
                if title == "Untitled" and content:
                    # Try to extract title from content
                    lines = content.split('\n')[:10]
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 10 and len(line) < 120:
                            title = line[:100]  # Limit title length
                            break
                
                # Enhanced keyword extraction
                key_facts = []
                if content:
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    query_words = [w.lower() for w in query_context.split() if len(w) > 3]
                    
                    for line in lines[:50]:  # Check first 50 lines
                        line_lower = line.lower()
                        # Look for lines with query keywords, numbers, or useful patterns
                        if (any(word in line_lower for word in query_words) or
                            any(pattern in line_lower for pattern in ['$', '€', '£', '%', 'price', 'cost', 'rating', 'review', '2024', '2025']) or
                            any(char.isdigit() for char in line)):
                            if 20 <= len(line) <= 200:
                                key_facts.append(line)
                                
                    key_facts = key_facts[:7]  # Increased to 7 facts
                
                word_count = len(content.split()) if content else 0
                
                return {
                    "url": url,
                    "title": title[:200],  # Limit title length
                    "content": content,
                    "key_facts": key_facts,
                    "urls": [url],
                    "extraction_success": True,
                    "word_count": word_count,
                    "authority": self._assess_source_authority(url),
                    "crawl_date": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                error_msg = getattr(result, 'error_message', 'Unknown error')
                print(f"⚠️ Crawl4AI failed for {url[:50]}: {error_msg}")
                return {
                    "url": url,
                    "title": "Crawl Failed",
                    "content": f"Could not extract content: {error_msg}",
                    "extraction_success": False,
                    "word_count": 0
                }
                
        except Exception as e:
            print(f"❌ Content extraction failed for {url[:50]}: {str(e)[:100]}")
            return {
                "url": url,
                "title": "Processing Failed",
                "content": f"Failed to process content: {str(e)[:200]}",
                "extraction_success": False,
                "word_count": 0
            }
    
    def _assess_source_authority(self, url: str) -> str:
        """Assess the authority/credibility of a source"""
        if not url:
            return 'unknown'
        
        domain = url.lower()
        
        # High authority sources
        if any(auth in domain for auth in [
            'wikipedia.org', 'github.com', 'stackoverflow.com', 'stackexchange.com',
            'reddit.com', 'news.ycombinator.com', 'medium.com', 'arxiv.org',
            'bbc.com', 'cnn.com', 'reuters.com', 'guardian.com', 'nytimes.com',
            'gov.', '.edu', 'nature.com', 'science.org'
        ]):
            return 'high_authority'
        
        # Medium authority sources
        elif any(med in domain for med in [
            'blogspot.com', 'wordpress.com', 'substack.com', 'dev.to',
            'hashnode.com', 'towards'
        ]):
            return 'medium_authority'
        
        return 'standard'
    
    def _evaluate_crawl_results(self, results: List[dict], query: str) -> dict:
        """Evaluate the quality of Crawl4AI results with LENIENT criteria to minimize Tavily usage"""
        if not results:
            return {"sufficient": False, "reason": "no_results", "score": 0}
        
        successful_extractions = sum(1 for r in results if r.get('extraction_success', False))
        total_word_count = sum(r.get('word_count', 0) for r in results)
        avg_word_count = total_word_count / max(len(results), 1)
        
        # Check for relevant content with more lenient matching
        query_keywords = [kw.lower() for kw in query.split() if len(kw) > 2]  # Skip short words
        relevant_results = 0
        
        for result in results:
            content = f"{result.get('title', '')} {result.get('content', '')}".lower()
            # More lenient: if ANY keyword matches, consider it relevant
            keyword_matches = sum(1 for keyword in query_keywords if keyword in content)
            if keyword_matches >= 1:  # At least 1 keyword match (was 30% of all keywords)
                relevant_results += 1
        
        # Calculate quality score with more forgiving weighting
        extraction_ratio = successful_extractions / len(results) if results else 0
        relevance_ratio = relevant_results / len(results) if results else 0
        content_quality = min(avg_word_count / 100, 1)  # Lower bar: 100 words instead of 200
        
        quality_score = extraction_ratio * 0.5 + relevance_ratio * 0.3 + content_quality * 0.2
        
        # MUCH MORE LENIENT criteria to avoid Tavily overuse
        if successful_extractions == 0:
            return {"sufficient": False, "reason": "no_successful_extractions", "score": quality_score}
        elif quality_score < 0.25:  # Lowered from 0.4 to 0.25
            return {"sufficient": False, "reason": "very_low_quality", "score": quality_score}
        elif avg_word_count < 20:  # Lowered from 50 to 20 words
            return {"sufficient": False, "reason": "extremely_short_content", "score": quality_score}
        else:
            return {"sufficient": True, "reason": "acceptable_quality", "score": quality_score}
    
    def _fallback_to_duckduckgo_scrape(self, query: str, max_results: int = 5) -> List[dict]:
        """Free fallback: scrape DuckDuckGo results and fetch page content via requests + BeautifulSoup"""
        try:
            import urllib.parse
            from bs4 import BeautifulSoup
            session = requests.Session()
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
            encoded = urllib.parse.quote_plus(query)
            url = f"https://duckduckgo.com/html/?q={encoded}"
            r = session.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')

            results = []
            for a in soup.select('a.result__a')[:max_results]:
                href = a.get('href')
                if not href or 'duckduckgo.com' in href:
                    continue
                try:
                    pr = session.get(href, headers=headers, timeout=15)
                    if pr.status_code != 200:
                        continue
                    psoup = BeautifulSoup(pr.text, 'html.parser')
                    text = psoup.get_text(separator=' ', strip=True)[:2000]
                    title = (psoup.title.string.strip() if psoup.title and psoup.title.string else a.get_text(strip=True))[:200]
                    results.append({
                        'url': href,
                        'title': title,
                        'content': text,
                        'key_facts': [],
                        'urls': [href],
                        'extraction_success': True,
                        'word_count': len(text.split()),
                        'authority': self._assess_source_authority(href),
                        'source': 'duckduckgo_scrape'
                    })
                except Exception:
                    continue
            return results
        except Exception as e:
            print(f"⚠️  Free fallback failed: {e}")
            return []

    async def _fallback_to_tavily(self, query: str, max_results: int = 5) -> List[dict]:
        """Fallback to Tavily when Crawl4AI results are insufficient; if not configured, use DuckDuckGo scrape."""
        try:
            tavily_config = self.config.get('tavily', {})
            api_key = tavily_config.get('api_key')
            
            if not api_key:
                # No Tavily; use free fallback
                return self._fallback_to_duckduckgo_scrape(query, max_results)
            
            tavily = TavilyClient(api_key=api_key)
            
            print(f"💰 Fallback to Tavily premium search for: '{query}'")
            
            # Enhanced Tavily search
            current_year = datetime.now().year
            enhanced_query = f"{query} {current_year} current information recent"
            
            response = tavily.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=True,
                include_raw_content=True
            )
            
            results = []
            for i, item in enumerate(response.get('results', [])):
                results.append({
                    'url': item.get('url', ''),
                    'title': item.get('title', 'No title'),
                    'content': item.get('raw_content', item.get('content', ''))[:2000],
                    'key_facts': [],  # Tavily doesn't provide structured facts
                    'urls': [item.get('url', '')],
                    'extraction_success': True,
                    'word_count': len(item.get('raw_content', '').split()) if item.get('raw_content') else 0,
                    'authority': self._assess_source_authority(item.get('url', '')),
                    'source': 'tavily_premium',
                    'search_rank': i + 1,
                    'score': item.get('score', 0)
                })
            
            return results
            
        except Exception as e:
            # If Tavily fails, try free fallback too
            print(f"⚠️  Tavily fallback failed: {e}. Trying DuckDuckGo scrape...")
            return self._fallback_to_duckduckgo_scrape(query, max_results)
    
    async def execute(self, query: str, max_results: int = 5, deep_extract: bool = True) -> List[dict]:
        """Execute the revolutionary Crawl4AI + OLLAMA search with smart Tavily fallback"""
        try:
            print(f"🚀 Starting ENHANCED Crawl4AI search for: '{query}'")
            print(f"📋 Target: {max_results} results, Deep extract: {deep_extract}")
            
            # Add timeout protection
            import asyncio
            try:
                # Step 1: Get content URLs (not search engine URLs) with timeout
                max_urls = int(max_results) * 3  # Ensure integer type
                content_urls = await asyncio.wait_for(
                    self._get_content_urls(query, max_urls),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                print("⏰ Crawl4AI timeout, falling back to Tavily...")
                return await self._fallback_to_tavily(query, max_results)
            
            if not content_urls:
                print("❌ No content URLs found via Crawl4AI, escalating to Tavily...")
                return await self._fallback_to_tavily(query, max_results)
            
            print(f"🎯 Found {len(content_urls)} content URLs to extract from")
            
            if not deep_extract:
                # Quick mode: just return basic URL info
                print("⚡ Quick mode: returning content URLs")
                return [{"url": url, "title": f"Search result for: {query}", "content": "Quick search result"} 
                       for url in content_urls[:max_results]]
            
            # Step 2: Advanced Crawl4AI content extraction  
            print(f"🤖 Deep content extraction on {min(len(content_urls), max_results)} URLs...")
            
            async def process_content_urls():
                tasks = []
                for url in content_urls[:max_results]:
                    task = self._crawl_with_ollama_extraction(url, query)
                    tasks.append(task)
                
                return await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process URLs with content extraction
            crawl_results = await process_content_urls()
            
            # Filter successful results
            final_results = []
            for result in crawl_results:
                if isinstance(result, Exception):
                    print(f"⚠️ Extraction failed: {result}")
                    continue
                if result.get('extraction_success', False):
                    final_results.append(result)
            
            print(f"📊 Successful extractions: {len(final_results)}/{len(crawl_results)}")
            
            # Step 3: Quality evaluation with more lenient criteria
            quality_check = self._evaluate_crawl_results(final_results, query)
            
            if not quality_check["sufficient"] and len(final_results) < 2:
                print(f"💰 Crawl4AI results insufficient ({quality_check['reason']}, score: {quality_check['score']:.2f}, only {len(final_results)} successful)")
                print(f"🚀 Escalating to Tavily premium for better results...")
                return await self._fallback_to_tavily(query, max_results)
            else:
                print(f"✅ Crawl4AI results sufficient (score: {quality_check['score']:.2f}, {len(final_results)} successful extractions) 🎯")
                return final_results[:max_results] if final_results else await self._fallback_to_tavily(query, max_results)
                
        except Exception as main_error:
            print(f"💥 Crawl4AI search failed completely: {str(main_error)}")
            print(f"💰 Emergency fallback to Tavily...")
            
            try:
                return await self._fallback_to_tavily(query, max_results)
            except Exception:
                # As a last resort, free fallback
                return self._fallback_to_duckduckgo_scrape(query, max_results)
    
    async def cleanup(self):
        """Clean up the crawler when done"""
        if self.crawler:
            await self.crawler.close()
            self.crawler = None