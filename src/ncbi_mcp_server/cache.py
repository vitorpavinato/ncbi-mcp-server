#!/usr/bin/env python3
"""
Caching module for NCBI MCP Server
Provides Redis-based caching with file-based fallback
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiofiles

logger = logging.getLogger(__name__)

# Analytics integration
try:
    from .analytics import analytics_manager
except ImportError:
    analytics_manager = None

class CacheManager:
    """Unified cache manager with Redis and file-based fallback"""
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 file_cache_dir: str = ".cache",
                 default_ttl: int = 3600):  # 1 hour default
        self.redis_client = None
        self.file_cache_dir = Path(file_cache_dir)
        self.default_ttl = default_ttl
        self.use_redis = False
        
        # Create cache directory
        self.file_cache_dir.mkdir(exist_ok=True)
        
        # Try to initialize Redis
        if redis_url:
            self._init_redis(redis_url)
    
    def _init_redis(self, redis_url: str) -> None:
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.use_redis = True
            logger.info("Redis cache initialized")
        except ImportError:
            logger.warning("Redis not available, using file-based cache only")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using file-based cache")
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generate a cache key from parameters"""
        # Create a consistent string from parameters
        param_str = json.dumps(kwargs, sort_keys=True)
        key_hash = hashlib.md5(param_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        # Try Redis first
        if self.use_redis and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Fall back to file cache
        return await self._get_from_file(key)
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        
        # Try Redis first
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, json.dumps(value))
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
        
        # Fall back to file cache
        await self._set_to_file(key, value, ttl)
    
    async def _get_from_file(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from file cache"""
        try:
            cache_file = self.file_cache_dir / f"{key}.cache"
            if not cache_file.exists():
                return None
            
            async with aiofiles.open(cache_file, 'rb') as f:
                data = await f.read()
                cache_entry = pickle.loads(data)
            
            # Check if expired
            if datetime.now() > cache_entry['expires']:
                cache_file.unlink()  # Delete expired file
                return None
            
            return cache_entry['data']
            
        except Exception as e:
            logger.warning(f"File cache get failed: {e}")
            return None
    
    async def _set_to_file(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        """Set value in file cache"""
        try:
            cache_file = self.file_cache_dir / f"{key}.cache"
            cache_entry = {
                'data': value,
                'expires': datetime.now() + timedelta(seconds=ttl),
                'created': datetime.now()
            }
            
            async with aiofiles.open(cache_file, 'wb') as f:
                await f.write(pickle.dumps(cache_entry))
                
        except Exception as e:
            logger.warning(f"File cache set failed: {e}")
    
    async def clear_expired(self) -> int:
        """Clear expired cache files"""
        try:
            cleared = 0
            for cache_file in self.file_cache_dir.glob("*.cache"):
                try:
                    async with aiofiles.open(cache_file, 'rb') as f:
                        data = await f.read()
                        cache_entry = pickle.loads(data)
                    
                    if datetime.now() > cache_entry['expires']:
                        cache_file.unlink()
                        cleared += 1
                except Exception:
                    # If we can't read the file, delete it
                    cache_file.unlink()
                    cleared += 1
            
            logger.info(f"Cleared {cleared} expired cache entries")
            return cleared
            
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")
            return 0
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'cache_type': 'redis' if self.use_redis else 'file',
            'default_ttl': self.default_ttl
        }
        
        if self.use_redis and self.redis_client:
            try:
                info = await self.redis_client.info()
                stats.update({
                    'redis_used_memory': info.get('used_memory_human', 'unknown'),
                    'redis_keys': await self.redis_client.dbsize()
                })
            except Exception:
                pass
        else:
            # File cache stats
            cache_files = list(self.file_cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files if f.exists())
            stats.update({
                'file_cache_entries': len(cache_files),
                'file_cache_size_mb': round(total_size / (1024 * 1024), 2)
            })
        
        return stats

class CachedNCBIClient:
    """NCBI Client with caching capabilities"""
    
    def __init__(self, ncbi_client, cache_manager: CacheManager):
        self.ncbi_client = ncbi_client
        self.cache = cache_manager
        
        # Cache TTL for different operation types
        self.cache_ttls = {
            'search': 1800,      # 30 minutes for searches
            'article': 86400,    # 24 hours for article details
            'mesh': 7200,        # 2 hours for MeSH terms
            'related': 3600      # 1 hour for related articles
        }
    
    async def search_pubmed(self, query: str, max_results: int = 20, 
                           sort: str = "relevance", date_range: Optional[str] = None) -> Dict[str, Any]:
        """Cached PubMed search"""
        cache_key = self.cache._generate_key(
            "search_pubmed",
            query=query,
            max_results=max_results,
            sort=sort,
            date_range=date_range
        )
        
        # Try cache first
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for search: {query[:50]}...")
            return cached_result
        
        # Cache miss - call API
        logger.info(f"Cache miss for search: {query[:50]}...")
        result = await self.ncbi_client.search_pubmed(query, max_results, sort, date_range)
        
        # Cache the result
        await self.cache.set(cache_key, result, self.cache_ttls['search'])
        return result
    
    async def get_article_details(self, pmids: list) -> Dict[str, Any]:
        """Cached article details fetch"""
        # Sort PMIDs for consistent caching
        sorted_pmids = sorted(pmids)
        cache_key = self.cache._generate_key("article_details", pmids=sorted_pmids)
        
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for articles: {len(pmids)} PMIDs")
            return cached_result
        
        logger.info(f"Cache miss for articles: {len(pmids)} PMIDs")
        result = await self.ncbi_client.get_article_details(pmids)
        
        await self.cache.set(cache_key, result, self.cache_ttls['article'])
        return result
    
    async def search_mesh_terms(self, term: str) -> Dict[str, Any]:
        """Cached MeSH search"""
        cache_key = self.cache._generate_key("mesh_search", term=term)
        
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for MeSH: {term}")
            return cached_result
        
        logger.info(f"Cache miss for MeSH: {term}")
        result = await self.ncbi_client.search_mesh_terms(term)
        
        await self.cache.set(cache_key, result, self.cache_ttls['mesh'])
        return result
    
    async def get_related_articles(self, pmid: str, max_results: int = 10) -> Dict[str, Any]:
        """Cached related articles fetch"""
        cache_key = self.cache._generate_key("related_articles", pmid=pmid, max_results=max_results)
        
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for related articles: {pmid}")
            return cached_result
        
        logger.info(f"Cache miss for related articles: {pmid}")
        result = await self.ncbi_client.get_related_articles(pmid, max_results)
        
        await self.cache.set(cache_key, result, self.cache_ttls['related'])
        return result
    
    async def advanced_search(self, terms: list, operator: str = "AND",
                            authors: Optional[list] = None, journals: Optional[list] = None,
                            publication_types: Optional[list] = None, date_from: Optional[str] = None,
                            date_to: Optional[str] = None, max_results: int = 20) -> Dict[str, Any]:
        """Cached advanced search"""
        cache_key = self.cache._generate_key(
            "advanced_search",
            terms=terms,
            operator=operator,
            authors=authors,
            journals=journals,
            publication_types=publication_types,
            date_from=date_from,
            date_to=date_to,
            max_results=max_results
        )
        
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info("Cache hit for advanced search")
            return cached_result
        
        logger.info("Cache miss for advanced search")
        result = await self.ncbi_client.advanced_search(
            terms, operator, authors, journals, publication_types,
            date_from, date_to, max_results
        )
        
        await self.cache.set(cache_key, result, self.cache_ttls['search'])
        return result
