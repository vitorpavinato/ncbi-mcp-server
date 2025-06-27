# 🔍 Enhanced Search Strategies for NCBI MCP Server

Based on real-world testing, here are optimized search strategies for better literature discovery.

## 🎯 The "Distribution of Fitness Effects" Case Study

**Target Paper**: "Isolating selective from non-selective forces using site frequency ratios" (PMID: 40258089)
**URL**: https://journals.plos.org/plosgenetics/article?id=10.1371/journal.pgen.1011427

### What Worked vs. What Didn't

❌ **Failed Searches**:
- "fitness effects distribution population genomics"
- "distribution of fitness effects population genomics" 
- "fitness effects inference genomics"

✅ **Successful Searches**:
- **"selective forces site frequency"** (position 2-3)
- **"mutation fitness effects site frequency"** (position 4)
- **"distribution mutation fitness effects"** (position 10)

## 🧠 **Key Insights**

1. **Use Method-Specific Terms**: Include specific methodological terms like "site frequency", "SFS", "allele frequency"
2. **Try Alternative Phrases**: "selective forces" vs "fitness effects"
3. **Sort by Date for "Latest"**: When looking for recent papers, use `sort="pub_date"`
4. **Expand Search Scope**: Increase `max_results` to 20-50 for comprehensive searches

## 🚀 **Improved Search Strategies**

### For Distribution of Fitness Effects Research:

#### Strategy 1: Multi-term approach
```python
queries = [
    "distribution fitness effects",
    "selective forces site frequency", 
    "mutation fitness effects SFS",
    "allele frequency spectrum fitness",
    "DFE inference population genetics"
]
```

#### Strategy 2: Method-focused
```python
queries = [
    "site frequency spectrum method",
    "SFS population genetics inference", 
    "allele frequency fitness estimation",
    "polymorphism fitness effects"
]
```

#### Strategy 3: Recent literature (sorted by date)
```python
# Use date sorting for "latest" requests
search_params = {
    "sort": "pub_date",
    "max_results": 20,
    "date_range": "365"  # Last year
}
```

## 📋 **Recommended Claude Prompts**

### Better Prompts for Finding Latest Papers:

Instead of:
> "Find the latest paper on the inference of the distribution of fitness effect using population genomics data"

Use:
> "Search for recent papers on fitness effects inference using these approaches:
> 1. Site frequency spectrum methods 
> 2. Selective forces estimation
> 3. Allele frequency-based inference
> Sort by publication date and get the top 20 results from the last 2 years"

### For Comprehensive Literature Reviews:

> "Perform a multi-strategy search for distribution of fitness effects research:
> - Search 'selective forces site frequency spectrum' 
> - Search 'mutation fitness effects inference'
> - Search 'DFE population genomics methods'
> - Get abstracts for the top 10 from each search, sorted by date"

## 🛠 **Advanced Search Techniques**

### 1. Use Field Tags
```
"site frequency spectrum"[ti] AND fitness[ti]
"selective forces"[tiab] AND genomics[mh]
```

### 2. Boolean Combinations
```
(DFE OR "fitness effects") AND ("site frequency" OR SFS)
```

### 3. Author and Journal Targeting
```python
# If you know key researchers
advanced_search(
    terms=["fitness effects", "population genetics"],
    authors=["Eyre-Walker", "Keightley"],
    journals=["PLoS Genetics", "Genetics", "Molecular Biology and Evolution"]
)
```

## 💡 **Pro Tips for Claude Users**

1. **Be Specific About Methods**: Mention specific analytical approaches
2. **Request Multiple Search Strategies**: Ask Claude to try different term combinations
3. **Always Check Recent Papers**: Explicitly request date-sorted results
4. **Use Batch Searches**: Have Claude run multiple searches simultaneously
5. **Cross-Reference Results**: Look for papers appearing in multiple searches

## 🎯 **Example Enhanced Prompt**

```
I'm looking for the most recent advances in inferring the distribution of fitness effects from population genomics data. Please:

1. Search these terms sorted by publication date:
   - "selective forces site frequency spectrum"
   - "mutation fitness effects inference" 
   - "DFE population genetics"
   - "site frequency ratio fitness"

2. Get abstracts for the top 5 papers from each search
3. Focus on papers from 2023-2025
4. Look for methodological advances and new software tools

This should help capture papers using different terminology and approaches.
```

This strategy would have found the PLOS Genetics paper you mentioned!
