# RAG Pipeline Implementation

## Overview

This document describes the 4-stage RAG (Retrieval-Augmented Generation) pipeline implementation.

## Pipeline Stages

### Stage 1: RETRIEVE
**Function**: `retrieve(query: str, docs: dict) -> list`

Finds relevant documents using keyword similarity scoring.

**Process**:
1. Tokenize the query (remove stopwords, clean punctuation)
2. For each document:
   - Tokenize the document
   - Calculate Jaccard similarity: `intersection / union`
   - Calculate overlap score: `intersection / len(query_words)`
   - Final score: `(Jaccard + Overlap) / 2`
3. Filter documents with score >= THRESHOLD (0.15)
4. Return top MAX_RESULTS (2) documents sorted by score

**Output**: List of tuples `(score, filename, content)`

---

### Stage 2: GENERATE
**Function**: `generate(query: str, retrieved: list) -> (str, float, list)`

Combines retrieved documents into a coherent answer using template-based generation.

**Process**:
1. Extract and structure source information:
   - File name, relevance score, content
2. Calculate average confidence: `sum(scores) / len(retrieved)`
3. Combine documents with clear separators
4. Apply answer template:
   ```
   Based on knowledge from [sources]:
   
   [document 1]
   
   ---
   
   [document 2]
   ```

**Output**: 
- Answer text (str)
- Average confidence score (float)
- Source list (list of dicts with file, score, content)

---

### Stage 3: VERIFY
**Function**: `verify(answer: str, confidence: float) -> bool`

Checks if the generated answer meets quality criteria.

**Verification Checks**:
1. Answer is not None
2. Answer length >= 50 characters
3. Confidence score >= 0.25

**Rationale**:
- Prevents empty or malformed responses
- Ensures sufficient content in answer
- Blocks low-confidence (potentially hallucinated) responses

**Output**: Boolean (True = Pass, False = Fail)

---

### Stage 4: GATE
**Function**: `gate(answer: str, confidence: float, sources: list) -> dict`

Returns either the answer or a safe "I don't know" response.

**Process**:
1. Call `verify()` to check answer quality
2. If verify passes:
   - Return answer, sources, confidence, gated=False
3. If verify fails:
   - Return safe message, empty sources, confidence=0, gated=True

**Output**: Dictionary with keys:
```python
{
    "answer": str,           # The response or "I don't know"
    "sources": list,         # Retrieved documents (empty if gated)
    "confidence": float,     # Average confidence (0.0 if gated)
    "gated": bool           # True if response was blocked
}
```

---

## Orchestration Function

**Function**: `rag_pipeline(query: str, docs: dict) -> dict`

Orchestrates the complete 4-stage pipeline and returns detailed results.

**Execution Flow**:
```
Query
  ↓
[1] RETRIEVE → retrieved_docs
  ↓
[2] GENERATE → answer, confidence, sources
  ↓
[3] VERIFY → pass/fail (implicit in GATE)
  ↓
[4] GATE → final_result
  ↓
Output with stage status
```

**Output**: Dictionary with:
- Standard output (answer, sources, confidence, gated)
- Stage execution details:
  ```python
  "stages": {
      "retrieve": int,      # Number of documents retrieved
      "generate": bool,     # Answer generated successfully
      "verify": bool,       # Answer passed verification
      "gate": bool         # Answer passed gating (not blocked)
  }
  ```

---

## Data Flow Example

### Input
```
Query: "What is RAG?"
Documents: {
    "rag.md": "# RAG\nRAG stands for Retrieval Augmented Generation...",
    "wiki.md": "# Wiki\nA wiki is a structured knowledge base...",
    "verification.md": "# Verification\nVerification ensures..."
}
```

### Stage 1: RETRIEVE
```
Scores:
  rag.md: 0.279 ✓ (above threshold)
  wiki.md: 0.050 ✗ (below threshold)
  verification.md: 0.062 ✗ (below threshold)

Output: [(0.279, "rag.md", "# RAG\nRAG stands...")]
```

### Stage 2: GENERATE
```
Answer:
  "Based on knowledge from rag.md:\n\n# RAG\nRAG stands..."

Confidence: 0.279 (average of retrieved scores)
Sources: [{"file": "rag.md", "score": 0.279, "content": "..."}]
```

### Stage 3: VERIFY
```
Check answer length: 159 >= 50 ✓
Check confidence: 0.279 >= 0.25 ✓
Check non-null: Not None ✓

Result: PASS
```

### Stage 4: GATE
```
Since VERIFY passed:
  Return answer with sources
  gated = False
  confidence = 0.279
```

### Final Output
```python
{
    "answer": "Based on knowledge from rag.md:\n\n# RAG\n...",
    "sources": [{"file": "rag.md", "score": 0.279}],
    "confidence": 0.279,
    "gated": False,
    "stages": {
        "retrieve": 1,
        "generate": True,
        "verify": True,
        "gate": True
    }
}
```

---

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `THRESHOLD` | 0.15 | Minimum similarity score for retrieval |
| `MAX_RESULTS` | 2 | Maximum documents to retrieve |
| `Verify confidence` | 0.25 | Minimum confidence to pass verification |
| `Verify length` | 50 | Minimum answer length (characters) |

---

## Failure Modes

### Low Relevance (Stage 1 Fails)
```
RETRIEVE: 0 documents found
GENERATE: answer=None, confidence=0
VERIFY: FAIL (None answer)
GATE: Returns "I don't know"
```

### Low Confidence (Stage 3 Fails)
```
RETRIEVE: 1 document found
GENERATE: answer generated, confidence < 0.25
VERIFY: FAIL (low confidence)
GATE: Returns "I don't know"
```

### Short Answer (Stage 3 Fails)
```
RETRIEVE: 1 document found
GENERATE: answer < 50 chars
VERIFY: FAIL (too short)
GATE: Returns "I don't know"
```

---

## Advantages of This Pipeline

1. **Modularity**: Each stage is independent and testable
2. **Transparency**: Pipeline execution status visible to user
3. **Safety**: Gating prevents low-confidence hallucinations
4. **Quality Control**: Multiple verification checkpoints
5. **Traceability**: Full source attribution and scoring
6. **Flexibility**: Easy to adjust thresholds and criteria

---

## Extension Points

The pipeline can be extended by:

1. **Improving RETRIEVE**: 
   - Add semantic similarity (embeddings)
   - Implement ranking algorithms
   - Add query expansion

2. **Improving GENERATE**:
   - Use actual LLM (GPT, Claude)
   - Add summarization
   - Handle multiple documents better

3. **Improving VERIFY**:
   - Add semantic coherence checks
   - Implement fact-checking
   - Add user feedback loop

4. **Improving GATE**:
   - Adaptive thresholds
   - User preferences
   - Context-aware gating
