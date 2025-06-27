#!/usr/bin/env python3
"""
NCBI Literature Search MCP Server
A Model Context Protocol server for searching NCBI databases (PubMed, PMC, etc.)
Designed for researchers in evolutionary biology, computational biology, and all life sciences.
"""

import asyncio
import json
import logging
import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import httpx
from mcp.server.fastmcp import FastMCP

# Import our modules
from .analytics import AnalyticsManager, track_usage
from .cache import SimpleLRUCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ncbi-mcp-server")

class NCBIClient:
    """Client for interacting with NCBI E-utilities API"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        self.email = email
        self.api_key = api_key
        
        # Enhanced HTTP client with connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0
        )
        
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, read=60.0),
            limits=limits,
            follow_redirects=True
        )
        
        # Rate limiting
        self.last_request_time = 0
        self.min_interval = 0.1 if api_key else 0.34  # 10/sec with key, 3/sec without
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            await asyncio.sleep(self.min_interval - time_since_last)
        
        self.last_request_time = time.time()
        
    async def search_pubmed(self, query: str, max_results: int = 20, 
                           sort: str = "relevance", date_range: Optional[str] = None) -> Dict[str, Any]:
        """Search PubMed database"""
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": str(max_results),
            "sort": sort,
            "retmode": "json"
        }
        
        if date_range:
            params["datetype"] = "pdat"
            params["reldate"] = date_range
            
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
            
        url = f"{self.BASE_URL}/esearch.fcgi"
        
        try:
            await self._rate_limit()
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            raise
    
    async def get_article_details(self, pmids: List[str]) -> Dict[str, Any]:
        """Fetch detailed information for specific PMIDs"""
        pmid_list = ",".join(pmids)
        params = {
            "db": "pubmed",
            "id": pmid_list,
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
            
        url = f"{self.BASE_URL}/efetch.fcgi"
        
        try:
            await self._rate_limit()
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return self._parse_pubmed_xml(response.text)
        except Exception as e:
            logger.error(f"Article details fetch failed: {e}")
            raise
    
    async def search_mesh_terms(self, term: str) -> Dict[str, Any]:
        """Search MeSH (Medical Subject Headings) terms"""
        params = {
            "db": "mesh",
            "term": term,
            "retmax": "10",
            "retmode": "json"
        }
        
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
            
        url = f"{self.BASE_URL}/esearch.fcgi"
        
        try:
            await self._rate_limit()
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"MeSH search failed: {e}")
            raise
    
    async def get_related_articles(self, pmid: str, max_results: int = 10) -> Dict[str, Any]:
        """Find articles related to a given PMID"""
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "retmax": str(max_results),
            "retmode": "json"
        }
        
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
            
        url = f"{self.BASE_URL}/elink.fcgi"
        
        try:
            await self._rate_limit()
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Related articles fetch failed: {e}")
            raise

    async def advanced_search(self, terms: List[str], operator: str = "AND",
                            authors: Optional[List[str]] = None, journals: Optional[List[str]] = None,
                            publication_types: Optional[List[str]] = None, date_from: Optional[str] = None,
                            date_to: Optional[str] = None, max_results: int = 20) -> Dict[str, Any]:
        """Perform advanced search with multiple criteria"""
        query_parts = []
        
        # Add main terms
        if terms:
            term_query = f" {operator} ".join(terms)
            query_parts.append(f"({term_query})")
        
        # Add authors
        if authors:
            author_queries = [f"{author}[au]" for author in authors]
            query_parts.append(f"({' OR '.join(author_queries)})")
        
        # Add journals
        if journals:
            journal_queries = [f"{journal}[journal]" for journal in journals]
            query_parts.append(f"({' OR '.join(journal_queries)})")
        
        # Add publication types
        if publication_types:
            pub_type_queries = [f"{pub_type}[pt]" for pub_type in publication_types]
            query_parts.append(f"({' OR '.join(pub_type_queries)})")
        
        # Add date range
        if date_from and date_to:
            query_parts.append(f"({date_from}[pdat]:{date_to}[pdat])")
        
        # Combine all parts
        final_query = " AND ".join(query_parts)
        
        # Use regular search with the complex query
        return await self.search_pubmed(final_query, max_results)
    
    def _parse_pubmed_xml(self, xml_text: str) -> Dict[str, Any]:
        """Parse PubMed XML response into structured data"""
        try:
            root = ET.fromstring(xml_text)
            articles = []
            
            for article in root.findall(".//PubmedArticle"):
                article_data = {}
                
                # PMID
                pmid_elem = article.find(".//PMID")
                if pmid_elem is not None:
                    article_data["pmid"] = pmid_elem.text
                
                # Title
                title_elem = article.find(".//ArticleTitle")
                if title_elem is not None:
                    article_data["title"] = title_elem.text or "No title available"
                
                # Authors
                authors = []
                for author in article.findall(".//Author"):
                    last_name = author.find("LastName")
                    first_name = author.find("ForeName")
                    if last_name is not None and first_name is not None:
                        authors.append(f"{first_name.text} {last_name.text}")
                article_data["authors"] = authors
                
                # Journal
                journal_elem = article.find(".//Journal/Title")
                if journal_elem is not None:
                    article_data["journal"] = journal_elem.text
                
                # Publication date
                pub_date = article.find(".//PubDate")
                if pub_date is not None:
                    year = pub_date.find("Year")
                    month = pub_date.find("Month")
                    if year is not None:
                        date_str = year.text
                        if month is not None:
                            date_str += f"-{month.text}"
                        article_data["publication_date"] = date_str
                
                # Abstract
                abstract_elem = article.find(".//AbstractText")
                if abstract_elem is not None:
                    article_data["abstract"] = abstract_elem.text
                
                # DOI
                doi_elem = article.find(".//ELocationID[@EIdType='doi']")
                if doi_elem is not None:
                    article_data["doi"] = doi_elem.text
                
                # Keywords/MeSH terms
                mesh_terms = []
                for mesh in article.findall(".//MeshHeading/DescriptorName"):
                    if mesh.text:
                        mesh_terms.append(mesh.text)
                article_data["mesh_terms"] = mesh_terms
                
                articles.append(article_data)
            
            return {"articles": articles}
            
        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
            return {"articles": [], "error": "Failed to parse XML response"}

# Import caching and batch processing
from .cache import CacheManager, CachedNCBIClient
from .batch import BatchProcessor

# Configure caching
cache_manager = CacheManager(
    redis_url=os.getenv("REDIS_URL"),  # You can provide: redis://localhost:6379/0
    file_cache_dir=os.path.join(os.getcwd(), ".cache")
)

# Initialize NCBI client with caching
ncbi_client = CachedNCBIClient(
    NCBIClient(
        email=os.getenv("NCBI_EMAIL"),
        api_key=os.getenv("NCBI_API_KEY")
    ),
    cache_manager
)

# Initialize batch processor
batch_processor = BatchProcessor(ncbi_client, max_concurrent=5)

# Initialize analytics manager
analytics_manager = AnalyticsManager(
    analytics_file=os.path.join(os.getcwd(), "analytics.json"),
    max_events_memory=1000,
    flush_interval=300  # 5 minutes
)

# Create FastMCP server
mcp = FastMCP("NCBI Literature Search")

@mcp.tool()
@track_usage("search_pubmed", "search")
async def search_pubmed(
    query: str,
    max_results: int = 20,
    sort: str = "relevance",
    date_range: Optional[str] = None
) -> Dict[str, Any]:
    """Search PubMed database for scientific literature."""
    try:
        result = await ncbi_client.search_pubmed(query, max_results, sort, date_range)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
@track_usage("get_article_details", "fetch")
async def get_article_details(pmids: List[str]) -> Dict[str, Any]:
    """Fetch detailed information for specific PubMed articles."""
    try:
        result = await ncbi_client.get_article_details(pmids)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
@track_usage("search_mesh_terms", "search")
async def search_mesh_terms(term: str) -> Dict[str, Any]:
    """Search Medical Subject Headings (MeSH) terms."""
    try:
        result = await ncbi_client.search_mesh_terms(term)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
@track_usage("get_related_articles", "search")
async def get_related_articles(pmid: str, max_results: int = 10) -> Dict[str, Any]:
    """Find articles related to a specific PubMed article."""
    try:
        result = await ncbi_client.get_related_articles(pmid, max_results)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
@track_usage("advanced_search", "search")
async def advanced_search(
    terms: List[str],
    operator: str = "AND",
    authors: Optional[List[str]] = None,
    journals: Optional[List[str]] = None,
    publication_types: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    max_results: int = 20
) -> Dict[str, Any]:
    """Perform advanced PubMed searches with multiple criteria."""
    try:
        result = await ncbi_client.advanced_search(
            terms, operator, authors, journals, publication_types,
            date_from, date_to, max_results
        )
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics."""
    try:
        stats = await cache_manager.stats()
        return stats
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def clear_cache() -> Dict[str, Any]:
    """Clear expired cache entries."""
    try:
        cleared = await cache_manager.clear_expired()
        return {
            "status": "success",
            "cleared_entries": cleared,
            "message": f"Cleared {cleared} expired cache entries"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def batch_search_multiple_queries(queries: List[str], max_results_per_query: int = 20) -> Dict[str, Any]:
    """Perform multiple PubMed searches in parallel for efficiency."""
    try:
        result = await batch_processor.batch_search(queries, max_results_per_query)
        return {
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "total_time": result.total_time,
            "results": result.results,
            "errors": result.errors
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def batch_get_article_details(pmids: List[str], chunk_size: int = 50) -> Dict[str, Any]:
    """Fetch article details for many PMIDs efficiently in batches."""
    try:
        # Split PMIDs into chunks
        pmid_chunks = batch_processor.chunk_pmids(pmids, chunk_size)
        result = await batch_processor.batch_get_articles(pmid_chunks)
        
        # Flatten results
        all_articles = []
        for batch_result in result.results:
            if batch_result.get("result", {}).get("articles"):
                all_articles.extend(batch_result["result"]["articles"])
        
        return {
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "total_time": result.total_time,
            "total_articles": len(all_articles),
            "articles": all_articles,
            "errors": result.errors
        }
    except Exception as e:
        return {"error": str(e)}

# Analytics MCP Tools
@mcp.tool()
async def get_analytics_summary() -> Dict[str, Any]:
    """Get comprehensive analytics summary including usage stats, performance metrics, and system health."""
    try:
        summary = await analytics_manager.get_analytics_summary()
        return summary
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_detailed_metrics(hours: int = 24) -> Dict[str, Any]:
    """Get detailed performance metrics for the specified time period (default: last 24 hours)."""
    try:
        metrics = await analytics_manager.get_detailed_metrics(hours)
        return metrics
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def reset_analytics() -> Dict[str, Any]:
    """Reset analytics data (use with caution - this will clear all collected metrics)."""
    try:
        # Stop current analytics
        await analytics_manager.stop()
        
        # Create new analytics manager
        global analytics_manager
        analytics_manager = AnalyticsManager(
            analytics_file=os.path.join(os.getcwd(), "analytics.json"),
            max_events_memory=1000,
            flush_interval=300
        )
        
        # Start new analytics
        await analytics_manager.start()
        
        return {
            "status": "success",
            "message": "Analytics data has been reset",
            "reset_time": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def startup():
    """Initialize services on startup"""
    await analytics_manager.start()
    logger.info("All services initialized")

async def shutdown():
    """Cleanup on shutdown"""
    await analytics_manager.stop()
    await ncbi_client.close()
    logger.info("All services shut down")

def main():
    """Main function to run the MCP server"""
    # Set up event loop for startup/shutdown
    async def run_with_lifecycle():
        try:
            await startup()
            # Run the MCP server (this will block)
            await mcp.run_async()
        finally:
            await shutdown()
    
    # For now, just run the basic server
    # TODO: Implement proper lifecycle management
    mcp.run()

if __name__ == "__main__":
    main()
