# RAG Wiki System - Quick Start Guide

## What You Have

A complete 4-stage Retrieval-Augmented Generation (RAG) pipeline system that:
1. **Retrieves** relevant documents from markdown files
2. **Generates** grounded answers combining those documents
3. **Verifies** answer quality and confidence
4. **Gates** (blocks) low-confidence responses to prevent hallucination

## Quick Start (2 minutes)

### 1. Run the System
```bash
python app.py
```

### 2. Ask a Question
```
Ask: What is RAG?
```

### 3. Get a Grounded Answer
```
PIPELINE EXECUTION
[1] RETRIEVE: Found 1 relevant documents
[2] GENERATE: Answer generated
[3] VERIFY:   Answer passed quality checks
[4] GATE:     PASSED

ANSWER:
Based on knowledge from rag.md:
# RAG
RAG stands for Retrieval Augmented Generation...

SOURCES:
  • rag.md (relevance: 27.9%)

CONFIDENCE: 27.9%
GATED: No (high confidence)
```

### 4. Type 'exit' to Quit
```
Ask: exit
👋 Goodbye!
```

## The 4 Stages Explained Simply

### Stage 1: RETRIEVE
"Find the relevant documents"
- Calculates similarity between question and wiki documents
- Returns most relevant documents above threshold
- Uses keyword matching with intelligent scoring

### Stage 2: GENERATE
"Combine the documents into an answer"
- Takes retrieved documents
- Formats them nicely with sources listed
- Calculates confidence based on relevance

### Stage 3: VERIFY
"Check if the answer is good quality"
- Checks if answer is not empty
- Checks if answer is long enough (50+ chars)
- Checks if confidence is high enough (25%+)

### Stage 4: GATE
"Decide whether to show the answer or not"
- If all checks passed: Return the answer
- If any check failed: Return safe "I don't know" message

## Adding Your Own Knowledge

Just add markdown files to the `/wiki` folder!

Example:
```bash
# Create a new knowledge file
cat > wiki/my-topic.md << 'EOF'
# My Topic

This is information about my topic.
It can be multiple paragraphs.
EOF

# Restart the app
python app.py
```

Now you can ask questions about your topic:
```
Ask: Tell me about my topic
```

## Configuration

Edit `app.py` to customize:

```python
THRESHOLD = 0.15      # Minimum relevance score (lower = more results)
MAX_RESULTS = 2       # Max documents to return
WIKI_PATH = "wiki"    # Where to load .md files from
LOG_FILE = "logs.txt" # Where to save query logs
```

## Understanding the Output

### When You Get an Answer
```
CONFIDENCE: 27.9%         ← Score based on relevance (0-100%)
GATED: No                 ← Answer is trusted
SOURCES: rag.md           ← Where the answer came from
```

### When You Get "I don't know"
```
CONFIDENCE: 0.0%          ← Too low to be trusted
GATED: Yes                ← Answer was blocked
SOURCES: (empty)          ← Not enough relevant info
```

## Example Interactions

### Q: What is RAG?
```
Retrieved: rag.md (59.4% match)
Answer: Generated from rag.md
Confidence: 59.4%
Status: PASSED - Answer returned
```

### Q: Tell me about something random
```
Retrieved: No documents above threshold
Answer: "I don't know"
Confidence: 0.0%
Status: BLOCKED - No relevant sources found
```

### Q: Can you verify this?
```
Retrieved: verification.md (15.0% match)
Answer: Generated but too low confidence
Confidence: 15.0%
Status: BLOCKED - Score below 25% minimum
```

## Checking Logs

Your queries are automatically logged:
```bash
cat logs.txt
```

Output:
```
Q: What is RAG?
Sources: rag.md
A: Based on knowledge from rag.md: # RAG...
---
Q: Tell me about verification
A: ESCALATED - No relevant sources
---
```

## Troubleshooting

### No documents found
- Make sure .md files are in `/wiki` folder
- Check file extensions (must be `.md`)
- Verify files contain actual content

### Always getting "I don't know"
- The confidence threshold might be too high
- Try lowering `THRESHOLD` in app.py
- Check if your question matches the wiki content

### Python not found
- Make sure Python 3.7+ is installed
- Use `python3 app.py` if `python` doesn't work

## File Locations

```
rag-wiki-app/
├── app.py              ← Main application
├── README.md           ← Full documentation
├── QUICK_START.md      ← This file
├── PIPELINE.md         ← Technical details
├── ARCHITECTURE.md     ← System design
├── logs.txt            ← Query history (auto-created)
└── wiki/               ← Your knowledge base
    ├── rag.md
    ├── verification.md
    └── wiki.md
```

## Key Concepts

**Retrieval**: Finding relevant documents
- Keyword matching with smart scoring
- Returns top matches above threshold

**Generation**: Creating the answer
- Combines retrieved documents
- Maintains source attribution

**Verification**: Quality control
- Checks for minimum length
- Checks for minimum confidence
- Prevents empty or low-quality answers

**Gating**: Safety mechanism
- Blocks low-confidence answers
- Prevents hallucination
- Always provides safe response

## Example Scenario

You have a knowledge base about AI:
```
wiki/
├── rag.md          → About RAG systems
├── llm.md          → About LLMs
└── embeddings.md   → About embeddings
```

**User asks**: "What is RAG?"
```
1. RETRIEVE: Searches wiki/ finds rag.md (high relevance)
2. GENERATE: Combines rag.md into answer
3. VERIFY: Checks quality (passes all checks)
4. GATE: Allows answer through
5. OUTPUT: Returns grounded answer with source

User gets accurate information with source attribution!
```

**User asks**: "What is everything?"
```
1. RETRIEVE: Searches wiki/ but low relevance
2. GENERATE: Creates weak answer
3. VERIFY: Fails (low confidence)
4. GATE: Blocks answer
5. OUTPUT: Returns safe "I don't know"

User won't get inaccurate information!
```

## Next Steps

1. **Run it**: `python app.py`
2. **Test it**: Ask "What is RAG?"
3. **Expand it**: Add more .md files to `/wiki`
4. **Customize it**: Edit thresholds in `app.py`
5. **Deploy it**: Integrate with your application

## For More Information

- **README.md** - Full system overview
- **PIPELINE.md** - How each stage works
- **ARCHITECTURE.md** - System design diagrams
- **IMPLEMENTATION_SUMMARY.md** - Complete technical details
- **TEST_RESULTS.md** - Test results and verification

## Happy RAG-ing!

Your RAG system is ready to use. Start adding knowledge and asking questions!
