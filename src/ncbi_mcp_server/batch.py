#!/usr/bin/env python3
"""
Batch processing module for NCBI MCP Server
Handles bulk operations efficiently with rate limiting and error handling
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class BatchResult:
    """Result from a batch operation"""
    success_count: int
    failure_count: int
    results: List[Dict[str, Any]]
    errors: List[str]
    total_time: float
    started_at: datetime
    completed_at: datetime

class BatchProcessor:
    """Handles batch processing with rate limiting and error handling"""
    
    def __init__(self, ncbi_client, max_concurrent: int = 5, batch_size: int = 10):
        self.ncbi_client = ncbi_client
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def batch_search(self, queries: List[str], max_results_per_query: int = 20) -> BatchResult:
        """Perform multiple searches in parallel"""
        started_at = datetime.now()
        
        async def search_single(query: str) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    result = await self.ncbi_client.search_pubmed(query, max_results_per_query)
                    return {"query": query, "result": result, "status": "success"}
                except Exception as e:
                    logger.error(f"Batch search failed for '{query}': {e}")
                    return {"query": query, "error": str(e), "status": "error"}
        
        # Execute all searches
        tasks = [search_single(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        errors = []
        processed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
                errors.append(str(result))
            elif result.get("status") == "success":
                success_count += 1
                processed_results.append(result)
            else:
                failure_count += 1
                errors.append(result.get("error", "Unknown error"))
        
        completed_at = datetime.now()
        total_time = (completed_at - started_at).total_seconds()
        
        return BatchResult(
            success_count=success_count,
            failure_count=failure_count,
            results=processed_results,
            errors=errors,
            total_time=total_time,
            started_at=started_at,
            completed_at=completed_at
        )
    
    async def batch_get_articles(self, pmid_groups: List[List[str]]) -> BatchResult:
        """Fetch article details for multiple groups of PMIDs"""
        started_at = datetime.now()
        
        async def fetch_group(pmids: List[str]) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    result = await self.ncbi_client.get_article_details(pmids)
                    return {"pmids": pmids, "result": result, "status": "success"}
                except Exception as e:
                    logger.error(f"Batch article fetch failed for PMIDs {pmids}: {e}")
                    return {"pmids": pmids, "error": str(e), "status": "error"}
        
        # Execute all fetches
        tasks = [fetch_group(pmids) for pmids in pmid_groups]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        errors = []
        processed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
                errors.append(str(result))
            elif result.get("status") == "success":
                success_count += 1
                processed_results.append(result)
            else:
                failure_count += 1
                errors.append(result.get("error", "Unknown error"))
        
        completed_at = datetime.now()
        total_time = (completed_at - started_at).total_seconds()
        
        return BatchResult(
            success_count=success_count,
            failure_count=failure_count,
            results=processed_results,
            errors=errors,
            total_time=total_time,
            started_at=started_at,
            completed_at=completed_at
        )
    
    async def batch_related_articles(self, pmids: List[str], max_related: int = 10) -> BatchResult:
        """Find related articles for multiple PMIDs"""
        started_at = datetime.now()
        
        async def get_related(pmid: str) -> Dict[str, Any]:
            async with self.semaphore:
                try:
                    result = await self.ncbi_client.get_related_articles(pmid, max_related)
                    return {"pmid": pmid, "result": result, "status": "success"}
                except Exception as e:
                    logger.error(f"Batch related articles failed for PMID {pmid}: {e}")
                    return {"pmid": pmid, "error": str(e), "status": "error"}
        
        # Execute all requests
        tasks = [get_related(pmid) for pmid in pmids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        errors = []
        processed_results = []
        
        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
                errors.append(str(result))
            elif result.get("status") == "success":
                success_count += 1
                processed_results.append(result)
            else:
                failure_count += 1
                errors.append(result.get("error", "Unknown error"))
        
        completed_at = datetime.now()
        total_time = (completed_at - started_at).total_seconds()
        
        return BatchResult(
            success_count=success_count,
            failure_count=failure_count,
            results=processed_results,
            errors=errors,
            total_time=total_time,
            started_at=started_at,
            completed_at=completed_at
        )
    
    def chunk_pmids(self, pmids: List[str], chunk_size: int = 50) -> List[List[str]]:
        """Split PMIDs into chunks for batch processing"""
        return [pmids[i:i + chunk_size] for i in range(0, len(pmids), chunk_size)]
    
    async def progressive_search(self, query: str, total_results: int = 1000) -> Dict[str, Any]:
        """Perform a large search progressively to avoid timeouts"""
        results = []
        batch_size = 100  # Max per API call
        
        for start in range(0, total_results, batch_size):
            remaining = total_results - start
            current_batch_size = min(batch_size, remaining)
            
            try:
                # Note: NCBI doesn't support offset, so we use retstart parameter
                # This is a simplified version - full implementation would need more complex logic
                batch_result = await self.ncbi_client.search_pubmed(
                    query, 
                    max_results=current_batch_size
                )
                
                if batch_result.get('esearchresult', {}).get('idlist'):
                    results.extend(batch_result['esearchresult']['idlist'])
                    logger.info(f"Progressive search: fetched {len(results)}/{total_results}")
                else:
                    logger.info("No more results available")
                    break
                    
            except Exception as e:
                logger.error(f"Progressive search batch failed at position {start}: {e}")
                break
        
        return {
            "total_fetched": len(results),
            "requested": total_results,
            "pmids": results
        }
