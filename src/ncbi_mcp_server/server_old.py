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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ncbi-mcp-server")

class NCBIClient:
    """Client for interacting with NCBI E-utilities API"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        self.email = email
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
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
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Related articles fetch failed: {e}")
            raise
    
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

# Initialize NCBI client with environment variables
ncbi_client = NCBIClient(
    email=os.getenv("NCBI_EMAIL"),
    api_key=os.getenv("NCBI_API_KEY")
)

# Create FastMCP server
mcp = FastMCP("NCBI Literature Search")

@mcp.tool()
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
async def get_article_details(pmids: List[str]) -> Dict[str, Any]:
    """Fetch detailed information for specific PubMed articles."""
    try:
        result = await ncbi_client.get_article_details(pmids)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def search_mesh_terms(term: str) -> Dict[str, Any]:
    """Search Medical Subject Headings (MeSH) terms."""
    try:
        result = await ncbi_client.search_mesh_terms(term)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_related_articles(pmid: str, max_results: int = 10) -> Dict[str, Any]:
    """Find articles related to a specific PubMed article."""
    try:
        result = await ncbi_client.get_related_articles(pmid, max_results)
        return result
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
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

# Add the missing advanced_search method to NCBIClient
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

# Add the method to the NCBIClient class
NCBIClient.advanced_search = advanced_search

def main():
    """Main function to run the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query. Can include field tags like [ti] for title, [au] for author, [mh] for MeSH terms. Examples: 'phylogenetic analysis[ti]', 'computational biology AND machine learning', 'CRISPR[mh] AND evolution'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 20, max: 100)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'relevance', 'pub_date', 'author', 'journal'",
                        "enum": ["relevance", "pub_date", "author", "journal"],
                        "default": "relevance"
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Limit to recent articles. Options: '30' (30 days), '90' (3 months), '365' (1 year), '1095' (3 years)",
                        "enum": ["30", "90", "365", "1095"]
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_article_details",
            description="Fetch detailed information for specific PubMed articles using their PMIDs. Returns full abstracts, author lists, MeSH terms, and publication details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pmids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of PubMed IDs (PMIDs) to fetch details for",
                        "maxItems": 50
                    }
                },
                "required": ["pmids"]
            }
        ),
        Tool(
            name="search_mesh_terms",
            description="Search Medical Subject Headings (MeSH) terms to find standardized terminology for your research area. Useful for discovering related concepts and improving search precision.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Term to search for in MeSH database"
                    }
                },
                "required": ["term"]
            }
        ),
        Tool(
            name="get_related_articles",
            description="Find articles related to a specific PubMed article. Great for literature reviews and discovering relevant research you might have missed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pmid": {
                        "type": "string",
                        "description": "PubMed ID of the article to find related articles for"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of related articles to return (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["pmid"]
            }
        ),
        Tool(
            name="advanced_search",
            description="Perform advanced PubMed searches with multiple criteria. Perfect for complex research queries combining multiple concepts, authors, date ranges, and publication types.",
            inputSchema={
                "type": "object",
                "properties": {
                    "terms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of search terms to combine"
                    },
                    "operator": {
                        "type": "string",
                        "description": "Boolean operator to combine terms",
                        "enum": ["AND", "OR", "NOT"],
                        "default": "AND"
                    },
                    "authors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of author names to include"
                    },
                    "journals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of journal names to include"
                    },
                    "publication_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Publication types: 'Research Article', 'Review', 'Meta-Analysis', 'Clinical Trial', 'Case Report'"
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date in YYYY/MM/DD format"
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date in YYYY/MM/DD format"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["terms"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls for NCBI literature search"""
    
    if name == "search_pubmed":
        query = arguments["query"]
        max_results = arguments.get("max_results", 20)
        sort = arguments.get("sort", "relevance")
        date_range = arguments.get("date_range")
        
        try:
            # Perform search
            search_results = await ncbi_client.search_pubmed(
                query=query,
                max_results=max_results,
                sort=sort,
                date_range=date_range
            )
            
            # Get PMIDs from search results
            pmids = search_results.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                return [TextContent(
                    type="text",
                    text=f"No articles found for query: '{query}'"
                )]
            
            # Get detailed information for articles
            details = await ncbi_client.get_article_details(pmids[:max_results])
            
            # Format results
            result_text = f"**PubMed Search Results for: '{query}'**\n\n"
            result_text += f"Found {len(details.get('articles', []))} articles:\n\n"
            
            for i, article in enumerate(details.get("articles", []), 1):
                result_text += f"**{i}. {article.get('title', 'No title')}**\n"
                result_text += f"   PMID: {article.get('pmid', 'N/A')}\n"
                result_text += f"   Authors: {', '.join(article.get('authors', [])[:3])}{'...' if len(article.get('authors', [])) > 3 else ''}\n"
                result_text += f"   Journal: {article.get('journal', 'N/A')}\n"
                result_text += f"   Date: {article.get('publication_date', 'N/A')}\n"
                
                if article.get('doi'):
                    result_text += f"   DOI: {article.get('doi')}\n"
                
                if article.get('abstract'):
                    abstract = article['abstract'][:300] + "..." if len(article['abstract']) > 300 else article['abstract']
                    result_text += f"   Abstract: {abstract}\n"
                
                if article.get('mesh_terms'):
                    result_text += f"   MeSH Terms: {', '.join(article['mesh_terms'][:5])}\n"
                
                result_text += "\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching PubMed: {str(e)}"
            )]
    
    elif name == "get_article_details":
        pmids = arguments["pmids"]
        
        try:
            details = await ncbi_client.get_article_details(pmids)
            
            result_text = f"**Article Details for PMIDs: {', '.join(pmids)}**\n\n"
            
            for article in details.get("articles", []):
                result_text += f"**Title:** {article.get('title', 'No title')}\n"
                result_text += f"**PMID:** {article.get('pmid', 'N/A')}\n"
                result_text += f"**Authors:** {', '.join(article.get('authors', []))}\n"
                result_text += f"**Journal:** {article.get('journal', 'N/A')}\n"
                result_text += f"**Publication Date:** {article.get('publication_date', 'N/A')}\n"
                
                if article.get('doi'):
                    result_text += f"**DOI:** {article.get('doi')}\n"
                
                if article.get('abstract'):
                    result_text += f"**Abstract:** {article['abstract']}\n"
                
                if article.get('mesh_terms'):
                    result_text += f"**MeSH Terms:** {', '.join(article['mesh_terms'])}\n"
                
                result_text += "\n---\n\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching article details: {str(e)}"
            )]
    
    elif name == "search_mesh_terms":
        term = arguments["term"]
        
        try:
            mesh_results = await ncbi_client.search_mesh_terms(term)
            
            result_text = f"**MeSH Terms for: '{term}'**\n\n"
            
            # This is a simplified version - in practice, you'd parse the MeSH results
            # For now, we'll just return the raw search info
            id_list = mesh_results.get("esearchresult", {}).get("idlist", [])
            
            if id_list:
                result_text += f"Found {len(id_list)} MeSH terms related to '{term}'\n"
                result_text += f"MeSH IDs: {', '.join(id_list)}\n\n"
                result_text += "Use these MeSH terms in your PubMed searches for more precise results.\n"
                result_text += f"Example: '{term}[mh]' to search specifically for this MeSH term."
            else:
                result_text += f"No MeSH terms found for '{term}'"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching MeSH terms: {str(e)}"
            )]
    
    elif name == "get_related_articles":
        pmid = arguments["pmid"]
        max_results = arguments.get("max_results", 10)
        
        try:
            related_results = await ncbi_client.get_related_articles(pmid, max_results)
            
            # Extract related PMIDs from the response
            related_pmids = []
            for linkset in related_results.get("linksets", []):
                for linksetdb in linkset.get("linksetdbs", []):
                    if linksetdb.get("dbto") == "pubmed":
                        related_pmids.extend(linksetdb.get("links", []))
            
            if not related_pmids:
                return [TextContent(
                    type="text",
                    text=f"No related articles found for PMID: {pmid}"
                )]
            
            # Get details for related articles
            details = await ncbi_client.get_article_details(related_pmids[:max_results])
            
            result_text = f"**Related Articles for PMID: {pmid}**\n\n"
            
            for i, article in enumerate(details.get("articles", []), 1):
                result_text += f"**{i}. {article.get('title', 'No title')}**\n"
                result_text += f"   PMID: {article.get('pmid', 'N/A')}\n"
                result_text += f"   Authors: {', '.join(article.get('authors', [])[:2])}{'...' if len(article.get('authors', [])) > 2 else ''}\n"
                result_text += f"   Journal: {article.get('journal', 'N/A')}\n"
                result_text += f"   Date: {article.get('publication_date', 'N/A')}\n\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error finding related articles: {str(e)}"
            )]
    
    elif name == "advanced_search":
        terms = arguments["terms"]
        operator = arguments.get("operator", "AND")
        authors = arguments.get("authors", [])
        journals = arguments.get("journals", [])
        publication_types = arguments.get("publication_types", [])
        date_from = arguments.get("date_from")
        date_to = arguments.get("date_to")
        max_results = arguments.get("max_results", 20)
        
        # Build complex query
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
        
        try:
            # Use the regular search function with the complex query
            search_results = await ncbi_client.search_pubmed(
                query=final_query,
                max_results=max_results,
                sort="relevance"
            )
            
            pmids = search_results.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                return [TextContent(
                    type="text",
                    text=f"No articles found for advanced search query: {final_query}"
                )]
            
            details = await ncbi_client.get_article_details(pmids)
            
            result_text = f"**Advanced Search Results**\n"
            result_text += f"**Query:** {final_query}\n\n"
            result_text += f"Found {len(details.get('articles', []))} articles:\n\n"
            
            for i, article in enumerate(details.get("articles", []), 1):
                result_text += f"**{i}. {article.get('title', 'No title')}**\n"
                result_text += f"   PMID: {article.get('pmid', 'N/A')}\n"
                result_text += f"   Authors: {', '.join(article.get('authors', [])[:3])}{'...' if len(article.get('authors', [])) > 3 else ''}\n"
                result_text += f"   Journal: {article.get('journal', 'N/A')}\n"
                result_text += f"   Date: {article.get('publication_date', 'N/A')}\n\n"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error performing advanced search: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Main function to run the MCP server"""
    logger.info("Starting NCBI Literature Search MCP Server")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ncbi-literature-search",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())