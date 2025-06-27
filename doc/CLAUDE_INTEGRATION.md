# 🚀 Claude Desktop Integration Guide

Your NCBI Literature Search MCP server is now integrated with Claude Desktop! Here's how to use it.

## ✅ Setup Complete

- ✅ NCBI MCP Server configured and tested
- ✅ Claude Desktop configuration updated
- ✅ Caching enabled for better performance
- ✅ Rate limiting configured (10 req/sec with API key)

## 🔄 Next Steps

### 1. Restart Claude Desktop
**Important**: You must restart Claude Desktop for the new MCP server to be recognized.

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Look for the 🔧 (tools) icon in your chat interface

### 2. Verify Integration
In a new Claude chat, you should see a 🔧 tools icon. If you see it, the integration worked!

## 🔬 How to Use with Claude

### Basic Literature Searches
```
"Search for recent papers on CRISPR gene editing in plants"
"Find phylogenetic studies on mammalian evolution from the last 2 years"
"Search for computational methods in population genetics"
```

### Advanced Research Queries
```
"Find review articles about machine learning applications in genomics, 
published in high-impact journals like Nature or Science"

"Search for papers by leading researchers in ancient DNA analysis"

"Find recent methods papers for phylogenetic reconstruction algorithms"
```

### Detailed Article Analysis
```
"Get detailed information including abstracts for the top 5 papers 
on evolutionary genomics"

"Find papers related to this specific study: PMID 12345678"

"Search for MeSH terms related to 'phylogenomics' to improve my search strategy"
```

## 🛠 Available Tools

Your Claude now has access to these literature search tools:

1. **search_pubmed** - Primary search tool
2. **get_article_details** - Get full abstracts and metadata
3. **search_mesh_terms** - Find standardized terminology
4. **get_related_articles** - Discover connected research
5. **advanced_search** - Complex multi-criteria searches
6. **batch_search_multiple_queries** - Parallel searches for efficiency
7. **cache_stats** - Monitor performance

## 📖 Example Research Workflows

### Literature Review Workflow
1. Start with broad search: *"Search for computational phylogenetics methods"*
2. Refine with MeSH terms: *"Find MeSH terms for phylogenetics"*
3. Get article details: *"Get abstracts for the top 10 papers from that search"*
4. Find related work: *"Find papers related to PMID [best paper ID]"*

### Staying Current
1. *"Search for new methods in evolutionary biology from the last 6 months"*
2. *"Find recent papers by [favorite researcher name]"*
3. *"Search for software tools published in bioinformatics journals this year"*

### Method Discovery
1. *"Find papers comparing different phylogenetic algorithms"*
2. *"Search for benchmarking studies in computational biology"*
3. *"Find review articles on the latest sequencing technologies"*

## 🚨 Troubleshooting

### If tools don't appear:
1. **Restart Claude Desktop** (most common fix)
2. Check the config file location: `~/Library/Application Support/Claude/claude_desktop_config.json`
3. Verify JSON syntax with: `python3 -m json.tool path/to/config.json`

### If searches fail:
1. Check internet connection
2. Verify NCBI API key is valid
3. Try simpler search terms first

### Performance Issues:
1. Use cache_stats tool to monitor caching
2. Reduce max_results for faster responses
3. Use batch operations for multiple queries

## 📊 Performance Features

- **Smart Caching**: Repeated searches are instant
- **Rate Limiting**: Respects NCBI's API limits automatically
- **Batch Processing**: Handle multiple queries efficiently
- **Connection Pooling**: Optimized for sustained use

## 🎯 Pro Tips

1. **Use specific field tags**: `"machine learning"[ti] AND genomics[mh]`
2. **Specify date ranges**: `"from the last 2 years"` or `"published after 2020"`
3. **Combine searches**: Ask for multiple related queries in one request
4. **Get full details**: Always ask for abstracts when you need to read papers
5. **Use MeSH terms**: They help find papers that use different terminology

## 📞 Support

If you encounter issues:
1. Check the server logs: `docker-compose logs ncbi-mcp-server`
2. Test standalone: `poetry run python -m src.ncbi_mcp_server.server`
3. Verify configuration in Claude Desktop config file

---

**Happy Researching! 🧬📚**

Your NCBI MCP server is now ready to accelerate your literature reviews and research discovery with Claude Desktop.
