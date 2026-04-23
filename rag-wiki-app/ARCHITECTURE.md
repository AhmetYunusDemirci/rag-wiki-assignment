# RAG Pipeline Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                USER INPUT                                   │
│                         "What is RAG?"                                      │
└────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                        ┌─────────────▼─────────────┐
                        │   INPUT VALIDATION        │
                        │ - Strip whitespace        │
                        │ - Check for empty input   │
                        │ - Validate query meaning  │
                        └─────────────┬─────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                      STAGE 1: RETRIEVE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: Query string                                                         │
│                                                                             │
│ Process:                                                                    │
│  1. Tokenize query (split on whitespace)                                  │
│  2. Remove stopwords and punctuation                                       │
│  3. For each document in wiki:                                             │
│     - Tokenize document                                                    │
│     - Calculate: Jaccard = intersection / union                            │
│     - Calculate: Overlap = intersection / query_words                      │
│     - Score = (Jaccard + Overlap) / 2                                      │
│  4. Filter documents with score >= THRESHOLD (0.15)                        │
│  5. Sort by score (descending)                                             │
│  6. Return top MAX_RESULTS (2) documents                                   │
│                                                                             │
│ Output: [(score, filename, content), ...]                                  │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      ├──► If 0 docs: score = 0, empty sources
                                      │
                                      └──► Proceed with retrieved docs
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                      STAGE 2: GENERATE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: Retrieved documents list, Query (unused in current version)          │
│                                                                             │
│ Process:                                                                    │
│  1. Extract metadata from retrieved docs:                                  │
│     - Filename, score, content                                             │
│  2. Calculate average confidence:                                          │
│     - confidence = avg(all_scores)                                         │
│  3. Format answer using template:                                          │
│     - "Based on knowledge from {sources}:\n\n{content}"                    │
│  4. Maintain source attribution:                                           │
│     - Store {file, score, content} for each source                         │
│                                                                             │
│ Output: (answer, confidence, [{file, score, content}, ...])                │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                                      └──► Always succeeds if docs exist
                                          Confidence = avg(scores)
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                      STAGE 3: VERIFY                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: Answer (str), Confidence (float)                                    │
│                                                                             │
│ Verification Checks:                                                       │
│  ┌─ Check 1: Answer is not None                                           │
│  │           Result: PASS / FAIL                                          │
│  │                                                                         │
│  ├─ Check 2: len(answer) >= 50 characters                                 │
│  │           Result: PASS / FAIL                                          │
│  │                                                                         │
│  └─ Check 3: confidence >= 0.25 (minimum 25%)                             │
│              Result: PASS / FAIL                                          │
│                                                                             │
│ Output: Boolean (True = ALL checks passed, False = ANY check failed)        │
│                                                                             │
│ Purpose: Prevent hallucination, ensure quality answers                     │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        │                           │
                     PASS                        FAIL
                        │                           │
┌───────────────────────▼─────────────────────────────▼──────────────────────┐
│                      STAGE 4: GATE                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: Verification result (True/False)                                    │
│                                                                             │
│ Gate Logic:                                                                │
│  If VERIFY PASSED:                                                        │
│    ├─ Return the generated answer                                         │
│    ├─ Include sources with relevance scores                               │
│    ├─ Set confidence to calculated value                                  │
│    ├─ Set gated = False                                                   │
│    └─ ALLOW ANSWER THROUGH                                                │
│                                                                             │
│  If VERIFY FAILED:                                                        │
│    ├─ Return safe "I don't know" message                                  │
│    ├─ Empty sources list                                                  │
│    ├─ Set confidence = 0.0                                                │
│    ├─ Set gated = True                                                    │
│    └─ BLOCK ANSWER (PREVENT HALLUCINATION)                                │
│                                                                             │
│ Output:                                                                    │
│  {                                                                        │
│      "answer": str,                # The response or "I don't know"        │
│      "sources": list,              # [{file, score, content}, ...] or []   │
│      "confidence": float,          # 0.0 or calculated confidence          │
│      "gated": bool,                # True if blocked, False if passed      │
│      "stages": {                   # Pipeline status for debugging          │
│          "retrieve": int,          # Number of docs retrieved              │
│          "generate": bool,         # Success/failure                       │
│          "verify": bool,           # Pass/fail                             │
│          "gate": bool              # Pass/fail (not gated)                 │
│      }                                                                     │
│  }                                                                        │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                    ORCHESTRATOR: rag_pipeline()                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Call sequence:                                                            │
│   1. retrieved = retrieve(query, docs)                                     │
│   2. answer, conf, sources = generate(query, retrieved)                    │
│   3. result = gate(answer, conf, sources)  [verify called inside gate]    │
│   4. Add stage metrics to result                                           │
│   5. Return complete result dict                                           │
│                                                                             │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                        LOGGING: log()                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: query, answer/status, sources                                       │
│ Process: Append to logs.txt                                                │
│ Format:                                                                    │
│   Q: [query]                                                               │
│   Sources: [source list]                                                   │
│   A: [answer or ESCALATED]                                                 │
│   ---                                                                      │
│                                                                             │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                        USER OUTPUT                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PIPELINE EXECUTION (visual feedback)                                      │
│  [1] RETRIEVE: Found X documents                                           │
│  [2] GENERATE: Answer generated                                            │
│  [3] VERIFY: Answer passed/failed quality checks                           │
│  [4] GATE: PASSED/BLOCKED                                                  │
│                                                                             │
│  ANSWER:                                                                   │
│  [Generated response or "I don't know"]                                    │
│                                                                             │
│  SOURCES:                                                                  │
│  • file.md (relevance: XX%)                                                │
│                                                                             │
│  CONFIDENCE: XX%                                                            │
│  GATED: Yes/No                                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
WIKI LOADING (happens once at startup)
├─ Load all .md files from /wiki folder
├─ Parse each file content
└─ Store in docs dict: {filename: content}

FOR EACH QUERY
├─ STAGE 1: RETRIEVE
│  ├─ Tokenize query
│  ├─ Calculate scores for each doc
│  └─ Return top docs
│
├─ STAGE 2: GENERATE
│  ├─ Structure retrieved docs
│  ├─ Calculate average confidence
│  └─ Format answer with template
│
├─ STAGE 3: VERIFY
│  ├─ Check answer quality
│  ├─ Apply verification rules
│  └─ Return pass/fail
│
├─ STAGE 4: GATE
│  ├─ Check verification result
│  ├─ Return answer or safe message
│  └─ Set gated flag
│
└─ OUTPUT + LOGGING
   ├─ Display results to user
   └─ Log to file
```

## Component Dependencies

```
app.py
├── Main components
│   ├── load_wiki()           [No dependencies]
│   ├── tokenize()            [Uses STOPWORDS config]
│   ├── score()               [Uses tokenize()]
│   ├── retrieve()            [Uses score(), THRESHOLD, MAX_RESULTS]
│   ├── generate()            [No internal dependencies]
│   ├── verify()              [No internal dependencies]
│   ├── gate()                [Uses verify()]
│   ├── rag_pipeline()        [Uses retrieve(), generate(), gate(), verify()]
│   ├── log()                 [Uses LOG_FILE config]
│   └── main()                [Uses all above functions]
│
└── Configuration
    ├── WIKI_PATH
    ├── LOG_FILE
    ├── THRESHOLD
    ├── MAX_RESULTS
    └── STOPWORDS
```

## Error Handling Flow

```
Query Processing
├─ Empty query? → Skip to next iteration
├─ Tokenization yields nothing? → Return error message
├─ RETRIEVE finds 0 docs?
│  ├─ GENERATE: answer=None, confidence=0
│  ├─ VERIFY: FAIL (None answer)
│  └─ GATE: Return "I don't know"
├─ GENERATE fails?
│  └─ Treated as None answer → FAIL
├─ VERIFY fails?
│  └─ GATE: Return "I don't know"
└─ Log failures
   ├─ Successful answers: log full answer
   └─ Failed answers: log "ESCALATED - ..."
```

## Configuration Impact Matrix

| Config | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|--------|---------|---------|---------|---------|
| `THRESHOLD` | ✓ (retrieval filter) | - | - | - |
| `MAX_RESULTS` | ✓ (limit docs) | ✓ (input docs) | - | - |
| `STOPWORDS` | ✓ (tokenization) | - | - | - |
| `VERIFY_MIN_CONFIDENCE` | - | - | ✓ (check) | ✓ (gating) |
| `VERIFY_MIN_LENGTH` | - | - | ✓ (check) | ✓ (gating) |

## Performance Characteristics

- **Load time**: O(n) where n = number of .md files
- **Per-query time**:
  - RETRIEVE: O(n*m) where m = average doc length
  - GENERATE: O(k) where k = number of retrieved docs
  - VERIFY: O(1)
  - GATE: O(1)
  - Total: O(n*m) dominated by retrieval

## Extensibility Points

```
Current Architecture
├─ retrieve() → Can be replaced with:
│  ├─ Semantic search (embeddings)
│  ├─ BM25 ranking
│  └─ Vector database queries
│
├─ generate() → Can be replaced with:
│  ├─ LLM-based generation (GPT, Claude)
│  ├─ Abstractive summarization
│  └─ Template expansion
│
├─ verify() → Can be extended with:
│  ├─ Fact-checking
│  ├─ Semantic coherence
│  └─ User feedback
│
└─ score() → Can be improved with:
   ├─ TF-IDF
   ├─ BM25
   └─ Neural semantic similarity
```
