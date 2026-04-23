# Micro-Wiki System - Domain Routing

## Overview

The Micro-Wiki system extends the RAG pipeline to support **multiple domain-specific knowledge bases** with automatic query routing.

### Key Features

- **Multi-domain support** - Organize knowledge by domain (tech, general, business, etc.)
- **Automatic domain detection** - Routes queries to correct domain
- **Keyword-based routing** - Uses domain keywords for classification
- **Isolated knowledge bases** - Each domain has separate wiki files
- **Confidence scoring** - Shows how well query matches detected domain

## System Architecture

```
User Query
    ↓
[DETECT DOMAIN]
    ├─ Score query against domain keywords
    ├─ Select best-matching domain
    └─ Return domain + confidence
    ↓
[ROUTE TO DOMAIN WIKI]
    ├─ Load documents from detected domain
    ├─ Search only within domain
    └─ Maintain domain context
    ↓
[4-STAGE RAG PIPELINE]
    ├─ RETRIEVE (from domain wiki)
    ├─ GENERATE (domain-specific answer)
    ├─ VERIFY (quality checks)
    └─ GATE (confidence gating)
    ↓
[ANSWER WITH DOMAIN INFO]
    ├─ Answer from correct domain
    ├─ Domain routing confidence
    ├─ Source attribution
    └─ Overall confidence score
```

## Configuration

### Domain Setup

Edit the `WIKI_DOMAINS` dictionary in `app.py`:

```python
WIKI_DOMAINS = {
    "tech": {
        "path": "wiki/tech",
        "keywords": ["python", "code", "programming", "software", "api", "database"]
    },
    "general": {
        "path": "wiki/general",
        "keywords": ["wiki", "knowledge", "base", "information", "learning"]
    },
    "business": {
        "path": "wiki/business",
        "keywords": ["business", "market", "sales", "strategy", "company"]
    },
}
```

### Adding a New Domain

1. **Add to WIKI_DOMAINS**:
```python
"healthcare": {
    "path": "wiki/healthcare",
    "keywords": ["health", "medical", "disease", "treatment", "patient"]
}
```

2. **Create directory and files**:
```bash
mkdir wiki/healthcare
echo "# Topic\nContent here" > wiki/healthcare/topic.md
```

3. **Restart the application**

## Domain Detection Algorithm

The system uses **keyword matching with confidence scoring**:

### Process

1. Tokenize the user query
2. Remove stopwords
3. For each domain:
   - Count matching keywords
   - Calculate: `matches / total_keywords`
4. Select domain with highest score

### Example

```
Query: "Tell me about Python programming"
Tokens: ["python", "programming"]

Scores:
  tech: 2/18 keywords match = 11.1%
  general: 0/9 keywords match = 0.0%
  business: 0/8 keywords match = 0.0%

Result: Route to "tech" domain
```

## File Organization

```
rag-wiki-app/
├── app.py                 ← Micro-wiki implementation
├── wiki/
│   ├── tech/              ← Technology domain
│   │   ├── rag.md
│   │   └── python.md
│   ├── general/           ← General knowledge domain
│   │   ├── wiki.md
│   │   └── verification.md
│   └── business/          ← Business domain
│       ├── strategy.md
│       └── sales.md
└── logs.txt               ← Includes domain routing logs
```

## API Reference

### `detect_domain(query)`

Detects which domain a query belongs to.

**Input**: `query` (str)

**Output**: `(domain_name, confidence)`

```python
domain, conf = detect_domain("What is Python?")
# Returns: ("tech", 0.143)
```

### `load_all_wikis()`

Loads all documents from all configured domains.

**Input**: None

**Output**: `{domain: {filename: content}}`

```python
all_wikis = load_all_wikis()
# Returns: {
#   "tech": {"rag.md": "# RAG\n...", "python.md": "# Python\n..."},
#   "general": {...},
#   "business": {...}
# }
```

### `load_wiki_for_domain(domain)`

Loads documents from a specific domain.

**Input**: `domain` (str)

**Output**: `{filename: content}`

```python
tech_docs = load_wiki_for_domain("tech")
# Returns: {"rag.md": "# RAG\n...", "python.md": "# Python\n..."}
```

### `route_query(query, all_wikis)`

Full query routing pipeline with domain detection and RAG.

**Input**: `query` (str), `all_wikis` (dict)

**Output**: `{answer, sources, confidence, gated, domain, domain_confidence, stages}`

```python
result = route_query("Tell me about Python", all_wikis)
# Returns: {
#   "answer": "Based on knowledge from python.md: # Python\n...",
#   "sources": [{"file": "python.md", "score": 0.28, ...}],
#   "confidence": 0.28,
#   "domain": "tech",
#   "domain_confidence": 0.143,
#   "gated": False,
#   "stages": {...}
# }
```

### `rag_pipeline(query, docs, domain=None)`

Traditional RAG pipeline with optional domain parameter.

**Input**: `query` (str), `docs` (dict), `domain` (str, optional)

**Output**: `{answer, sources, confidence, gated, domain, stages}`

## Output Format

### Successful Query with Domain Routing

```python
{
    "answer": "Based on knowledge from python.md: # Python\n...",
    "sources": [
        {
            "file": "python.md",
            "score": 0.28,
            "content": "# Python\nPython is a programming language..."
        }
    ],
    "confidence": 0.28,          # Document relevance confidence
    "domain": "tech",            # Detected domain
    "domain_confidence": 0.143,  # How well query matches domain keywords
    "gated": False,              # Answer passed all checks
    "stages": {
        "retrieve": 1,           # 1 document retrieved
        "generate": True,        # Answer generated
        "verify": True,          # Passed verification
        "gate": True             # Passed gating
    }
}
```

### Gated Query (Low Confidence)

```python
{
    "answer": "I don't know. Please provide more context...",
    "sources": [],
    "confidence": 0.0,
    "domain": "tech",
    "domain_confidence": 0.143,
    "gated": True,               # Answer was blocked
    "stages": {
        "retrieve": 0,
        "generate": False,
        "verify": False,
        "gate": False
    }
}
```

## Query Routing Examples

### Example 1: Tech Domain Query
```
User: "Tell me about Python programming"

Detection:
  Query tokens: ["python", "programming"]
  tech keywords matched: ["python"] = 1 match
  Detected domain: tech (11.1% confidence)

Routing:
  Search in: wiki/tech/
  Found: python.md (28% relevance)
  Answer: Python is a programming language...
```

### Example 2: Business Domain Query
```
User: "What is business strategy?"

Detection:
  Query tokens: ["business", "strategy"]
  business keywords matched: ["business", "strategy"] = 2 matches
  Detected domain: business (25% confidence)

Routing:
  Search in: wiki/business/
  Found: strategy.md (45% relevance)
  Answer: Business strategy involves planning...
```

### Example 3: Ambiguous Query
```
User: "What is information?"

Detection:
  Query tokens: ["information"]
  tech: 0 matches
  general: 1 match (keyword: "information")
  business: 0 matches
  Detected domain: general (11.1% confidence)

Routing:
  Search in: wiki/general/
  Result: No documents above threshold
  Answer: I don't know (gated)
```

## Logging with Domain Info

Logs now include domain routing information:

```
Q: What is RAG?
Domain: tech
Sources: rag.md
A: Based on knowledge from rag.md: # RAG...
---
Q: Tell me about sales
Domain: business
Sources: sales.md
A: Based on knowledge from sales.md: # Sales...
---
Q: Random question
Domain: general
A: ESCALATED - No relevant sources
---
```

## Performance Considerations

### Domain Detection
- **Time**: O(q * d * k) where q = query words, d = domains, k = keywords
- **Typical**: < 1ms

### Document Loading
- **Time**: O(d * f) where d = domains, f = files per domain
- **Typical**: 10-50ms (done once at startup)

### Query Processing
- **Time**: Same as traditional RAG (domain isolation doesn't change complexity)
- **Typical**: < 100ms

## Extending with More Domains

### Quick Add Example

```python
# 1. Add to WIKI_DOMAINS
WIKI_DOMAINS = {
    # ... existing domains ...
    "healthcare": {
        "path": "wiki/healthcare",
        "keywords": ["health", "medical", "disease", "treatment", "patient", "doctor"]
    }
}

# 2. Create directory and files
# mkdir wiki/healthcare
# echo "# Health Topic\n..." > wiki/healthcare/topic.md

# 3. Run the system - automatically detects new domain
```

## Advanced: Custom Domain Scoring

To customize domain scoring, modify `detect_domain()`:

```python
def detect_domain(query):
    """Detect domain with custom scoring logic."""
    q_words = set(tokenize(query))
    domain_scores = {}
    
    for domain, config in WIKI_DOMAINS.items():
        keywords = set([kw.lower() for kw in config["keywords"]])
        
        # Custom: Weight recent keywords higher
        matching = q_words.intersection(keywords)
        score = len(matching) / len(keywords)
        
        # Custom: Boost scores for certain domains
        if domain == "tech":
            score *= 1.2  # Boost tech domain
        
        domain_scores[domain] = score
    
    best_domain = max(domain_scores, key=domain_scores.get)
    return best_domain, domain_scores[best_domain]
```

## Troubleshooting

### All Queries Route to Same Domain
- **Cause**: Overlapping keywords between domains
- **Solution**: Make domain keywords more distinct

### Domain Not Detected
- **Cause**: Query has no matching keywords
- **Solution**: Add more keywords to domain config, or check for typos

### Empty Domain Returns Error
- **Cause**: Domain folder exists but has no .md files
- **Solution**: Create at least one .md file in the domain folder

## Comparison: Single Wiki vs Micro-Wiki

| Aspect | Single Wiki | Micro-Wiki |
|--------|-----------|-----------|
| Search speed | Fast (small set) | Very fast (domain isolation) |
| Accuracy | Medium (mixed contexts) | High (domain-specific) |
| Scalability | Limited | Excellent |
| Setup complexity | Simple | Moderate |
| Extensibility | Low | High |
| Use cases | General knowledge | Specialized domains |

## Future Enhancements

1. **ML-based routing** - Train classifier on query-domain pairs
2. **Hybrid domains** - Allow documents in multiple domains
3. **Domain weights** - Prioritize certain domains
4. **Cross-domain queries** - Search multiple domains and merge results
5. **Domain fallback** - Search other domains if primary returns nothing
