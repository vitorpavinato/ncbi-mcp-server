# NCBI Literature Search MCP Server

A Model Context Protocol (MCP) server for searching NCBI databases, designed for researchers across all life sciences and biomedical fields. This server provides seamless access to PubMed's vast collection of 35+ million scientific articles through natural language queries, enabling AI assistants to help with literature reviews, research discovery, and scientific analysis.

## Features

🔬 **Comprehensive Search**: Search PubMed's 35+ million articles across all biological disciplines
📊 **Advanced Queries**: Support for complex searches with boolean operators, field tags, and filters  
🧬 **Life Sciences Research**: Covers all biological and biomedical fields including genetics, ecology, medicine, and biotechnology
💻 **Computational Biology**: Perfect for finding bioinformatics methods, algorithms, and computational tools
🔬 **Research Applications**: Literature reviews, hypothesis generation, method discovery, and staying current with scientific advances
📚 **Full Article Details**: Get abstracts, author lists, MeSH terms, DOIs, and publication information
🔗 **Related Articles**: Discover relevant research through NCBI's relationship algorithms
📖 **MeSH Integration**: Search and utilize Medical Subject Headings for precise terminology

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Poetry (recommended) - [Install Poetry](https://python-poetry.org/docs/#installation)

### Setup (5 minutes)

1. **Create and initialize project**
   ```bash
   mkdir ncbi-mcp-server && cd ncbi-mcp-server
   poetry init
   ```
   During init, add dependencies: `mcp`, `httpx`, `typing-extensions`

2. **Create project structure**
   ```bash
   mkdir -p src/ncbi_mcp_server
   # Save server.py code as src/ncbi_mcp_server/server.py
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Test the server**
   ```bash
   poetry run python src/ncbi_mcp_server/server.py
   ```

5. **Configure Claude Desktop**
   
   Edit your Claude Desktop config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/claude/claude_desktop_config.json`

   Add this configuration:
   ```json
   {
     "mcpServers": {
       "ncbi-literature": {
         "command": "poetry",
         "args": ["run", "python", "src/ncbi_mcp_server/server.py"],
         "cwd": "/FULL/PATH/TO/YOUR/ncbi-mcp-server"
       }
     }
   }
   ```

6. **Restart Claude Desktop** and start searching!

### Alternative Setup Methods

<details>
<summary>Click to expand alternative installation methods</summary>

#### **Conda Environment**
```bash
conda env create -f environment.yml
conda activate ncbi-mcp
python server.py
```

#### **Standard pip + venv**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python server.py
```
</details>

## Usage Examples

### For Evolutionary Biology Research

**Search for phylogenetic studies:**
```
"Search for recent phylogenetic analysis papers on mammalian evolution"
→ Uses: search_pubmed with query "phylogenetic analysis[ti] AND mammalian[ti] AND evolution"
```

**Find computational phylogenetics methods:**
```
"Find papers about maximum likelihood methods for phylogenetic reconstruction"
→ Uses: search_pubmed with query "maximum likelihood[ti] AND phylogenetic reconstruction"
```

**Search by specific organism:**
```
"Find recent papers on Drosophila comparative genomics"
→ Uses: search_pubmed with query "Drosophila[ti] AND comparative genomics[ti]"
```

### For Computational Biology Research

**Algorithm and method papers:**
```
"Search for machine learning applications in genomics from the last 2 years"
→ Uses: search_pubmed with date_range="730" and query "machine learning AND genomics"
```

**Software and database papers:**
```
"Find papers about new bioinformatics tools for sequence analysis"
→ Uses: search_pubmed with query "bioinformatics[ti] AND software[ti] AND sequence analysis"
```

### Advanced Search Examples

**Multi-criteria search:**
```
"Find review articles about CRISPR applications in evolutionary studies published in Nature or Science"
→ Uses: advanced_search with terms=["CRISPR", "evolution"], publication_types=["Review"], journals=["Nature", "Science"]
```

**Author-specific searches:**
```
"Find recent papers by researchers working on ancient DNA and phylogenomics"
→ Uses: search_pubmed with query "ancient DNA[ti] AND phylogenomics[ti]"
```

## Tool Reference

### `search_pubmed`
Primary search tool for PubMed database
- **query**: Search terms (supports field tags like `[ti]` for title, `[au]` for author, `[mh]` for MeSH terms)
- **max_results**: Number of results (1-100, default: 20)
- **sort**: Sort by "relevance", "pub_date", "author", or "journal"
- **date_range**: Limit to recent articles ("30", "90", "365", "1095" days)

**Examples:**
- `"CRISPR[ti] AND evolution"` - CRISPR in title AND evolution anywhere
- `"phylogenetic analysis[mh]"` - Using MeSH term for phylogenetic analysis
- `"computational biology AND machine learning"` - Boolean search

### `get_article_details`
Fetch complete information for specific articles
- **pmids**: List of PubMed IDs (up to 50)

Returns full abstracts, author lists, MeSH terms, DOI, publication details

### `search_mesh_terms`
Find standardized Medical Subject Headings
- **term**: Term to search in MeSH database

Helps discover related concepts and improve search precision

### `get_related_articles`
Discover articles related to a specific paper
- **pmid**: PubMed ID of reference article
- **max_results**: Number of related articles (1-50, default: 10)

Perfect for literature reviews and finding relevant research

### `advanced_search`
Complex searches with multiple criteria
- **terms**: List of search terms to combine
- **operator**: "AND", "OR", or "NOT" to combine terms
- **authors**: List of author names
- **journals**: List of journal names
- **publication_types**: "Research Article", "Review", "Meta-Analysis", etc.
- **date_from/date_to**: Date range in YYYY/MM/DD format
- **max_results**: Number of results (1-100, default: 20)

## Analytics & Performance Monitoring

The NCBI MCP Server includes comprehensive analytics to help you understand your research patterns and optimize performance.

### Analytics Tools

#### `get_analytics_summary`
Get comprehensive analytics overview
```
"Show me my research analytics summary"
```
Returns:
- Total requests and uptime
- Operation breakdown (searches, fetches, etc.)
- Cache performance metrics
- Recent activity and error rates
- System health indicators

#### `get_detailed_metrics`
Detailed performance metrics for specific time periods
```
"Get detailed metrics for the last 24 hours"
```
- **hours**: Time period to analyze (default: 24)
- Operation-specific performance data
- Timeline analysis with hourly breakdowns
- Error rates and response times per operation

#### `reset_analytics`
Reset analytics data (use with caution)
```
"Reset all analytics data"
```
**Note**: This permanently clears all collected metrics.

### What's Tracked

**Usage Patterns:**
- Search queries and frequency
- Most used operations
- Unique vs. repeated queries
- Peak usage periods

**Performance Metrics:**
- Response times for each operation
- Cache hit/miss rates
- Error rates and types
- Rate limiting efficiency

**Research Insights:**
- Popular search terms and patterns
- Research workflow analysis
- Literature access patterns
- Most accessed journals and topics

## Deployment

### Quick Start

1. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your NCBI email and API key
   ```

2. **Choose deployment method:**
   ```bash
   # Local development
   ./deploy.sh local
   
   # Docker deployment
   ./deploy.sh docker
   
   # Production deployment
   ./deploy.sh production
   ```

### Deployment Options

#### 1. Local Development
Perfect for development and testing:
```bash
poetry install
poetry run python -m src.ncbi_mcp_server.server
```

#### 2. Docker Deployment
Recommended for most users with two options:

**Full setup with Redis (recommended):**
```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your NCBI email and API key

# Start all services
docker-compose up -d
```

**Simple setup without Redis:**
```bash
# For basic usage without Redis dependencies
cp .env.example .env
# Edit .env with your NCBI email

docker-compose -f docker-compose.simple.yml up -d
```

**Full setup includes:**
- NCBI MCP Server container
- Redis cache for performance
- Redis Commander UI (http://localhost:8081)

**Simple setup includes:**
- NCBI MCP Server container only
- In-memory caching (no persistence)

#### 3. Production Deployment
For production environments:
```bash
# Configure production settings
cp .env.production .env
# Edit with production values

# Deploy
./deploy.sh production
```

### Monitoring

**Docker logs:**
```bash
docker-compose logs -f ncbi-mcp-server
```

**Cache monitoring:**
- Redis Commander: http://localhost:8081
- Cache stats via MCP tool: `cache_stats()`

**Health checks:**
```bash
# Test server health
curl http://localhost:8000/health

# Test via MCP
python -c "from src.ncbi_mcp_server.server import cache_stats; import asyncio; print(asyncio.run(cache_stats()))"
```

## Configuration

### NCBI API Key (Optional but Recommended)
For higher rate limits and better performance:

1. **Register at NCBI**: https://www.ncbi.nlm.nih.gov/account/
2. **Get API key**: https://www.ncbi.nlm.nih.gov/account/settings/
3. **Add to server code** in `src/ncbi_mcp_server/server.py`:

```python
# Replace the line: ncbi_client = NCBIClient()
# With:
ncbi_client = NCBIClient(
    email="your.email@university.edu",
    api_key="your_api_key_here"
)
```

### Rate Limits
- **Without API key**: 3 requests/second
- **With API key**: 10 requests/second  
- **With API key + email**: Higher limits for bulk requests

## Development Workflow

### Poetry Commands
```bash
poetry shell              # Activate virtual environment
poetry add package        # Add new dependency
poetry remove package     # Remove dependency
poetry update            # Update all dependencies
poetry run python ...    # Run commands in environment
poetry build             # Create distribution packages
```

### Code Quality (if you added dev dependencies)
```bash
poetry add --group dev black mypy pytest isort flake8
poetry run black .       # Format code
poetry run mypy .        # Type checking  
poetry run pytest       # Run tests
poetry run isort .       # Sort imports
```

### Sharing with Colleagues
```bash
# They just need:
git clone your-repo
cd ncbi-mcp-server  
poetry install
# Everything works identically!
```

## Field Tags for Advanced Searches

PubMed supports many field tags for precise searching:

- `[ti]` - Title
- `[tiab]` - Title and Abstract  
- `[au]` - Author
- `[mh]` - MeSH Terms
- `[journal]` - Journal Name
- `[pdat]` - Publication Date
- `[pt]` - Publication Type
- `[lang]` - Language
- `[sb]` - Subset (e.g., medline, pubmed)

**Example Advanced Queries:**
```
"machine learning"[ti] AND "phylogen*"[tiab] AND "2020"[pdat]:"2024"[pdat]
evolutionary[mh] AND computational[ti] AND (genomics[tiab] OR proteomics[tiab])
"ancient DNA"[ti] AND (paleogenomics[mh] OR phylogenomics[tiab])
```

## Research Workflow Examples

### Literature Review Workflow
1. **Start broad**: `search_pubmed("computational phylogenetics")`
2. **Refine with MeSH**: `search_mesh_terms("phylogenetics")` 
3. **Find key papers**: Use publication dates and journal filters
4. **Explore connections**: `get_related_articles(pmid="key_paper_id")`
5. **Deep dive**: `get_article_details(pmids=["12345", "67890"])`

### Staying Current
1. **Recent methods**: `search_pubmed("new methods", date_range="90")`
2. **Follow key authors**: `search_pubmed("author_name[au]", sort="pub_date")`
3. **Track specific topics**: `advanced_search` with your research keywords

### Method Discovery
1. **Algorithm papers**: `search_pubmed("algorithm[ti] AND your_field")`
2. **Software tools**: `search_pubmed("software[ti] OR tool[ti] AND bioinformatics")`
3. **Benchmarking**: `search_pubmed("comparison[ti] OR benchmark[ti]")`

## Troubleshooting

### Common Issues

**Server won't start:**
- Check Python version (3.8+ required)
- Install dependencies: `pip install -r requirements.txt`
- Verify file permissions

**No search results:**
- Check query syntax (use proper field tags)
- Try broader search terms
- Verify internet connection

**Rate limit errors:**
- Add delays between requests
- Get NCBI API key for higher limits
- Consider searching fewer results per query

**XML parsing errors:**
- Usually temporary NCBI server issues
- Retry after a few seconds
- Check NCBI status: https://www.ncbi.nlm.nih.gov/

### Getting Help

- **NCBI E-utilities documentation**: https://www.ncbi.nlm.nih.gov/books/NBK25499/
- **PubMed search tips**: https://pubmed.ncbi.nlm.nih.gov/help/
- **MeSH database**: https://www.ncbi.nlm.nih.gov/mesh/

## Contributing

This MCP server is designed to grow with the research community. Ideas for enhancement:

- **Additional databases**: PMC, BioRxiv, databases beyond NCBI
- **Citation analysis**: Track paper impact and citation networks  
- **Export formats**: BibTeX, EndNote, RIS for reference managers
- **Saved searches**: Persistent search profiles and alerts
- **Full-text integration**: When available through PMC

## License

This project is open source. Feel free to modify and distribute according to your institution's policies.

---

**Perfect for researchers in:**
- Evolutionary Biology & Phylogenetics
- Computational Biology & Bioinformatics  
- Molecular Evolution & Population Genetics
- Comparative Genomics & Proteomics
- Systems Biology & Network Analysis
- Biostatistics & Mathematical Biology
- Ancient DNA & Paleogenomics
- Conservation Genetics & Ecology

Start exploring the vast world of biological literature with powerful, precise searches!