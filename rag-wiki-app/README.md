## Markdown-based RAG Wiki System

A simple Retrieval-Augmented Generation (RAG) system with a 4-stage pipeline that loads knowledge from markdown files in the `/wiki` folder and retrieves relevant documents based on keyword similarity.

### Features

- **4-Stage RAG Pipeline** - Retrieve → Generate → Verify → Gate
- **Wiki-based retrieval** - Load and retrieve from markdown (.md) files
- **Full document retrieval** - No chunking, returns complete documents
- **Keyword similarity scoring** - Hybrid Jaccard + Overlap metrics
- **Answer generation** - Template-based response combining retrieved docs
- **Verification layer** - Prevents low-confidence answers (anti-hallucination)
- **Gating mechanism** - Returns "I don't know" if confidence is below threshold
- **Source attribution** - Shows which documents were used with relevance scores
- **Query logging** - Records all queries and responses

### The 4-Stage RAG Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: RETRIEVE                                           │
│ Find relevant documents using keyword similarity scoring    │
│ Output: List of documents with relevance scores             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: GENERATE                                           │
│ Combine retrieved documents into a coherent answer          │
│ Uses template-based generation for consistency              │
│ Output: Answer text + average confidence score              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: VERIFY                                             │
│ Verify answer quality:                                      │
│  • Non-null answer                                          │
│  • Minimum length (50 chars)                                │
│  • Minimum confidence (0.25)                                │
│ Output: Pass/Fail decision                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: GATE                                               │
│ Return answer or generic "I don't know" based on verify     │
│ Prevents hallucination by gating low-confidence responses   │
│ Output: Final answer + sources + confidence + gating status │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

1. **Load Phase**: All .md files from the `/wiki` folder are loaded into memory
2. **Tokenize Phase**: Queries and documents are tokenized, removing stopwords
3. **Scoring Phase**: Each document receives a similarity score:
   - Jaccard similarity = intersection / union
   - Overlap score = intersection / query_words
   - Final score = (Jaccard + Overlap) / 2
4. **Retrieve Phase**: Top 2 documents scoring ≥ 0.15 are retrieved
5. **Generate Phase**: Documents are combined using a template
6. **Verify Phase**: Answer checked for quality (length, confidence)
7. **Gate Phase**: High-confidence answers pass, low-confidence are blocked
8. **Log Phase**: All interactions recorded to logs.txt

### Configuration

Edit these variables in `app.py`:
- `WIKI_PATH`: Directory containing .md files (default: "wiki")
- `LOG_FILE`: File to log queries (default: "logs.txt")
- `THRESHOLD`: Minimum retrieval score (default: 0.15)
- `MAX_RESULTS`: Maximum documents to retrieve (default: 2)
- `STOPWORDS`: Words to ignore during tokenization

### Usage

```bash
python app.py
```

Then type your questions at the prompt. Type "exit" to quit.

**Output includes:**
- Answer (with sources listed)
- Sources (file names with relevance scores)
- Confidence score (0.0 - 1.0)
- Pipeline execution status

### Example Interaction

```
Ask: What is RAG?

======================================================================
PIPELINE EXECUTION
======================================================================
[1] RETRIEVE: Found 1 relevant documents
[2] GENERATE: Answer generated
[3] VERIFY:   Answer passed quality checks
[4] GATE:     PASSED
======================================================================

ANSWER:
Based on knowledge from rag.md:

# RAG

RAG stands for Retrieval Augmented Generation.

It retrieves documents and uses them to generate grounded answers.

SOURCES:
  • rag.md (relevance: 27.9%)

CONFIDENCE: 27.9%
GATED: No (high confidence)
```

### Scoring Algorithm

The system uses a hybrid similarity approach:

```
Jaccard Score = intersection(query_words, doc_words) / union(query_words, doc_words)
Overlap Score = intersection(query_words, doc_words) / len(query_words)
Final Score = (Jaccard Score + Overlap Score) / 2
```

This ensures both broad relevance (Jaccard) and query completeness (Overlap).

### Verification Criteria

An answer passes verification if:
1. It is not None
2. Length >= 50 characters
3. Confidence score >= 0.25

If verification fails, the Gate stage returns a generic "I don't know" response to prevent hallucination.

### Adding Knowledge

Simply add .md files to the `/wiki` folder. Each file becomes a knowledge page. The system will automatically load them on next startup.

### Output Format

The system returns a structured result with:
- **answer**: The generated response or "I don't know"
- **sources**: List of retrieved documents with relevance scores
- **confidence**: Average confidence score (0.0-1.0)
- **gated**: Boolean indicating if answer was blocked by gating
- **stages**: Status of each pipeline stage for debugging