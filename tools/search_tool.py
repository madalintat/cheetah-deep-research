from .base_tool import BaseTool
import asyncio
import json
import time
import requests
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
        # Local-only search: no headless browser, no external paid APIs
    
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
    
    # Removed Crawl4AI initialization: using lightweight requests + BeautifulSoup approach only
    
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
    
    # Removed Crawl4AI URL extraction: we use DuckDuckGo HTML scrape directly
    
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
    
    # Removed Crawl4AI content extraction: we extract with requests + BeautifulSoup in _fallback_to_duckduckgo_scrape
    
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

    # Removed Tavily fallback: using free DuckDuckGo scraping only (local-only behavior)
    
    async def execute(self, query: str, max_results: int = 5, deep_extract: bool = True) -> List[dict]:
        """Local-only web search using DuckDuckGo HTML + requests/BeautifulSoup. No Crawl4AI, no Tavily."""
        try:
            print(f"🚀 Starting local search for: '{query}'")
            print(f"📋 Target: {max_results} results, Deep extract: {deep_extract}")

            # Primary: DuckDuckGo HTML scrape + per-page content fetch (already implemented below)
            results = self._fallback_to_duckduckgo_scrape(query, max_results)

            if not results:
                print("⚠️ No results found via local scrape")
                return []

            # Evaluate and lightly refine key facts using simple heuristics (no remote LLM)
            refined = []
            query_words = [w.lower() for w in query.split() if len(w) > 3]
            for item in results[:max_results]:
                content = item.get('content', '') or ''
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                key_facts = []
                for line in lines[:50]:
                    lower = line.lower()
                    if (any(qw in lower for qw in query_words) or any(ch.isdigit() for ch in line)) and 20 <= len(line) <= 200:
                        key_facts.append(line)
                item['key_facts'] = (item.get('key_facts') or []) + key_facts[:5]
                refined.append(item)

            print(f"✅ Local search completed with {len(refined)} results")
            return refined

        except Exception as main_error:
            print(f"💥 Local search failed: {str(main_error)}")
            return []
    
    async def cleanup(self):
        """Clean up the crawler when done"""
        if self.crawler:
            await self.crawler.close()
            self.crawler = None