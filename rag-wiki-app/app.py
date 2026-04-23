import os
import sys
import json
from pathlib import Path

# --- CONFIG ---
WIKI_DOMAINS = {
    "tech": {"path": "wiki/tech", "keywords": ["python", "code", "programming", "software", "api", "database", "algorithm", "data", "system", "computer", "rag", "retrieval", "augmented", "generation"]},
    "general": {"path": "wiki/general", "keywords": ["wiki", "knowledge", "base", "information", "learning", "education", "verification", "answer", "question"]},
    "business": {"path": "wiki/business", "keywords": ["business", "market", "sales", "management", "strategy", "company", "profit", "revenue"]},
}

LOG_FILE = "logs.txt"
THRESHOLD = 0.15
MAX_RESULTS = 2

STOPWORDS = [
    "nedir", "ne", "kim", "kaç", "mı", "mi", "mu", "mü",
    "ve", "veya", "ile", "da", "de", "bu", "şu", "o",
    "için", "ama", "fakat", "gibi", "daha", "en",
    "bir", "çok", "az", "var", "yok",
    "the", "a", "an", "is", "are", "was", "were", "and", "or", "but"
]

# --- LOAD MICRO-WIKIS ---
def load_all_wikis():
    """Load all markdown files from all wiki domain folders.
    
    Returns:
        dict: {domain: {filename: content}}
    """
    all_wikis = {}
    
    for domain, config in WIKI_DOMAINS.items():
        wiki_dir = Path(config["path"])
        
        if not wiki_dir.exists():
            print(f"⚠️  Wiki folder not found for domain '{domain}' at {config['path']}")
            all_wikis[domain] = {}
            continue
        
        docs = {}
        for file_path in wiki_dir.glob("*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        docs[file_path.name] = content
            except Exception as e:
                print(f"⚠️  Error loading {file_path.name}: {e}")
        
        all_wikis[domain] = docs
    
    return all_wikis

def load_wiki_for_domain(domain):
    """Load all markdown files from a specific wiki domain folder.
    
    Args:
        domain (str): Domain name (e.g., 'tech', 'general')
    
    Returns:
        dict: {filename: content}
    """
    if domain not in WIKI_DOMAINS:
        return {}
    
    config = WIKI_DOMAINS[domain]
    wiki_dir = Path(config["path"])
    docs = {}
    
    if not wiki_dir.exists():
        print(f"⚠️  Wiki folder not found for domain '{domain}' at {config['path']}")
        return docs
    
    for file_path in wiki_dir.glob("*.md"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    docs[file_path.name] = content
        except Exception as e:
            print(f"⚠️  Error loading {file_path.name}: {e}")
    
    return docs

# --- DETECT DOMAIN ---
def detect_domain(query):
    """Detect which domain a query belongs to based on keyword matching.
    
    Uses a scoring system where each domain gets points for matching keywords.
    
    Args:
        query (str): User query
    
    Returns:
        tuple: (domain_name, confidence)
    """
    q_words = set(tokenize(query))
    domain_scores = {}
    
    for domain, config in WIKI_DOMAINS.items():
        keywords = set([kw.lower() for kw in config["keywords"]])
        matching_words = q_words.intersection(keywords)
        score = len(matching_words) / len(keywords) if keywords else 0
        domain_scores[domain] = score
    
    # Find domain with highest score
    best_domain = max(domain_scores, key=domain_scores.get)
    best_score = domain_scores[best_domain]
    
    return best_domain, best_score

# --- TOKENIZE ---
def tokenize(text):
    """Extract meaningful words by removing stopwords."""
    words = text.lower().split()
    return [w.strip('.,!?;:') for w in words if w.strip('.,!?;:') and w.lower() not in STOPWORDS]

# --- SCORING ---
def score(query, doc):
    """Calculate similarity score between query and document using keyword overlap."""
    q_words = set(tokenize(query))
    d_words = set(tokenize(doc))
    
    if not q_words:
        return 0
    
    # Count matching keywords
    intersection = q_words.intersection(d_words)
    
    # Jaccard similarity: intersection / union
    union = q_words.union(d_words)
    jaccard_score = len(intersection) / len(union) if union else 0
    
    # Simple overlap score: what percentage of query words appear in doc
    overlap_score = len(intersection) / len(q_words)
    
    # Return weighted combination (50/50)
    return (jaccard_score + overlap_score) / 2

# --- RETRIEVE ---
def retrieve(query, docs):
    """Find relevant documents based on keyword similarity scoring."""
    if not docs:
        return []
    
    scored = []
    
    for name, content in docs.items():
        s = score(query, content)
        
        if s >= THRESHOLD:
            scored.append((s, name, content))
    
    # Sort by score (descending) and return top results
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[:MAX_RESULTS]

# --- GENERATE ---
def generate(query, retrieved):
    """Generate answer by combining retrieved documents with template.
    
    Uses a template-based approach to create a more cohesive answer.
    """
    if not retrieved:
        return None, 0, []
    
    # Extract documents and scores
    sources = []
    combined_content = []
    
    for score, name, content in retrieved:
        sources.append({
            "file": name,
            "score": score,
            "content": content
        })
        combined_content.append(content)
    
    # Calculate average confidence score
    avg_score = sum(r[0] for r in retrieved) / len(retrieved)
    
    # Template-based answer generation
    source_list = ", ".join([s["file"] for s in sources])
    combined_docs = "\n\n---\n\n".join(combined_content)
    
    answer = (
        f"Based on knowledge from {source_list}:\n\n"
        f"{combined_docs}"
    )
    
    return answer, avg_score, sources

# --- VERIFY (Stage 3) ---
def verify(answer, confidence):
    """Verify if answer meets quality criteria.
    
    Checks:
    - Answer is not None
    - Minimum length (50 characters)
    - Minimum confidence (0.3)
    """
    if answer is None:
        return False
    
    if len(answer) < 50:
        return False
    
    if confidence < 0.3:
        return False
    
    return True

# --- GATE (Stage 4) ---
def gate(query, answer, confidence, sources):
    """Gate function: return answer or appropriate refusal based on checks.
    
    Returns:
        dict with keys: answer, sources, confidence, gated
    """
    unsafe_keywords = ["hack", "bypass", "ignore previous", "system prompt", "forget", "instruction"]
    query_lower = query.lower()
    if any(kw in query_lower for kw in unsafe_keywords):
        return {
            "answer": "I cannot fulfill this request. Unsafe query detected.",
            "sources": [],
            "confidence": 0.0,
            "gated": True
        }

    if not sources:
        return {
            "answer": "Out of scope.",
            "sources": [],
            "confidence": 0.0,
            "gated": True
        }

    if not verify(answer, confidence):
        return {
            "answer": "I don't know.",
            "sources": [],
            "confidence": 0.0,
            "gated": True
        }

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "gated": False
    }

# --- LOG ---
def log(query, result, sources=None, domain=None, confidence=None):
    """Log queries and results to file."""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Q: {query}\n")
            if domain:
                f.write(f"Domain: {domain}\n")
            if confidence is not None:
                f.write(f"Confidence: {confidence:.2%}\n")
            if sources:
                f.write(f"Sources: {', '.join(sources)}\n")
            f.write(f"A: {result}\n")
            f.write("---\n")
    except Exception as e:
        print(f"⚠️  Logging error: {e}")

# --- WRITEBACK ---
def writeback(query, answer, confidence):
    """Save high-confidence Q/A pairs to wiki/updates.md."""
    if confidence > 0.8:
        try:
            updates_path = Path("wiki/updates.md")
            updates_path.parent.mkdir(parents=True, exist_ok=True)
            with open(updates_path, "a", encoding="utf-8") as f:
                f.write(f"## Question: {query}\n\n")
                f.write(f"**Confidence:** {confidence:.2%}\n\n")
                f.write(f"**Answer:**\n{answer}\n\n")
                f.write("---\n\n")
        except Exception as e:
            print(f"⚠️  Writeback error: {e}")

def rag_pipeline(query, docs, domain=None):
    """Execute the complete RAG pipeline with 4 stages.
    
    Stages:
    1. RETRIEVE - Find relevant documents using keyword similarity
    2. GENERATE - Combine documents into a coherent answer
    3. VERIFY   - Check if answer meets quality criteria
    4. GATE     - Return answer or "I don't know" based on confidence
    
    Args:
        query (str): User query
        docs (dict): Documents to search in
        domain (str): Domain name (for metadata)
    
    Returns:
        dict with keys: answer, sources, confidence, gated, stages, domain
    """
    # Stage 1: RETRIEVE
    retrieved = retrieve(query, docs)
    
    # Stage 2: GENERATE
    answer, confidence, sources = generate(query, retrieved)
    
    # Stage 3: VERIFY (implicit in gate)
    # Stage 4: GATE
    result = gate(query, answer, confidence, sources)
    
    # Add stage details for debugging
    result["stages"] = {
        "retrieve": len(retrieved),
        "generate": answer is not None,
        "verify": verify(answer, confidence) if answer else False,
        "gate": not result["gated"]
    }
    
    result["domain"] = domain
    
    return result

# --- MICRO-WIKI ROUTER ---
def route_query(query, all_wikis):
    """Route a query to the most relevant wiki domain.
    
    Process:
    1. Detect domain from query keywords
    2. Load documents from that domain
    3. Execute RAG pipeline on that domain
    4. Return result with domain info
    
    Args:
        query (str): User query
        all_wikis (dict): All loaded wikis {domain: {file: content}}
    
    Returns:
        dict: RAG pipeline result with domain routing info
    """
    # Detect domain
    detected_domain, confidence = detect_domain(query)
    
    # Get documents from detected domain
    docs = all_wikis.get(detected_domain, {})
    
    if not docs:
        return {
            "answer": f"No knowledge base found for domain '{detected_domain}'.",
            "sources": [],
            "confidence": 0.0,
            "gated": True,
            "domain": detected_domain,
            "domain_confidence": confidence,
            "stages": {
                "retrieve": 0,
                "generate": False,
                "verify": False,
                "gate": False
            }
        }
    
    # Execute RAG pipeline on the domain
    result = rag_pipeline(query, docs, domain=detected_domain)
    result["domain_confidence"] = confidence
    
    return result


# --- EVALUATION ---
def run_evaluation(all_wikis):
    """Run evaluation over the dataset and print accuracy and failures."""
    eval_file = "eval_dataset.json"
    if not os.path.exists(eval_file):
        print(f"❌ Evaluation dataset '{eval_file}' not found.")
        return

    try:
        with open(eval_file, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except Exception as e:
        print(f"❌ Error loading evaluation dataset: {e}")
        return

    total = len(dataset)
    if total == 0:
        print("⚠️ Evaluation dataset is empty.")
        return

    correct = 0
    failures = []

    print(f"Running evaluation over {total} examples...")
    print("-" * 50)

    for i, entry in enumerate(dataset):
        query = entry.get("question", "")
        expected = entry.get("expected_keyword", "").lower()
        
        if not query or not expected:
            continue
            
        result = route_query(query, all_wikis)
        answer = result.get("answer", "")
        
        if answer and expected in answer.lower():
            correct += 1
        else:
            failures.append({
                "question": query,
                "expected": expected,
                "actual": answer
            })

    accuracy = (correct / total) * 100
    
    print(f"\nEVALUATION RESULTS")
    print(f"Accuracy: {accuracy:.2f}% ({correct}/{total})")
    
    if failures:
        print("\nFAILURES:")
        for i, f in enumerate(failures, 1):
            print(f"[{i}] Q: {f['question']}")
            print(f"    Expected keyword: '{f['expected']}'")
            print(f"    Actual answer: {f['actual'][:100]}...\n")


# --- MAIN ---
def main():
    """Main Micro-Wiki RAG system with domain routing."""
    # Load all wikis from all domains
    all_wikis = load_all_wikis()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--eval":
        run_evaluation(all_wikis)
        return
    
    total_docs = sum(len(docs) for docs in all_wikis.values())
    if total_docs == 0:
        print("❌ No wiki documents found. Please add .md files to wiki subfolders.")
        return
    
    print("🚀 Micro-Wiki RAG System - Domain Routing")
    print(f"📚 Loaded {total_docs} wiki documents across {len(all_wikis)} domains")
    print(f"📍 Domains: {', '.join(all_wikis.keys())}")
    print("Stages: [1] Detect Domain [2] Retrieve [3] Generate [4] Verify [5] Gate")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            query = input("Ask: ").strip()
            
            if not query:
                continue
            
            if query.lower() == "exit":
                print("👋 Goodbye!")
                break
            
            # Validate query has meaningful content
            if not tokenize(query):
                print("⚠️ Please ask a meaningful question.\n")
                continue
            
            # Route query to appropriate domain
            result = route_query(query, all_wikis)
            
            # Display results
            print("\n" + "="*70)
            print("📊 DOMAIN ROUTING & PIPELINE EXECUTION")
            print("="*70)
            print(f"[0] DETECT: Domain '{result['domain']}' (confidence: {result.get('domain_confidence', 0):.1%})")
            print(f"[1] RETRIEVE: Found {result['stages']['retrieve']} relevant documents")
            print(f"[2] GENERATE: Answer {'generated' if result['stages']['generate'] else 'FAILED'}")
            print(f"[3] VERIFY:   Answer {'passed' if result['stages']['verify'] else 'FAILED'} quality checks")
            print(f"[4] GATE:     {'PASSED' if result['stages']['gate'] else 'BLOCKED - Low confidence'}")
            print("="*70)
            
            # Display answer
            print("\n📝 ANSWER:")
            print(result["answer"])
            
            # Display sources and confidence
            if result["sources"]:
                print("\n📚 SOURCES:")
                for source in result["sources"]:
                    print(f"  • {source['file']} (relevance: {source['score']:.2%})")
            
            print(f"\n🎯 CONFIDENCE: {result['confidence']:.2%}")
            print(f"🚪 GATED: {'Yes (low confidence)' if result['gated'] else 'No (high confidence)'}")
            print()
            
            # Log the interaction
            if result["sources"]:
                source_names = [s["file"] for s in result["sources"]]
                log(query, result["answer"], source_names, domain=result['domain'], confidence=result['confidence'])
                writeback(query, result["answer"], result["confidence"])
            else:
                log(query, "ESCALATED - No relevant sources", domain=result['domain'], confidence=result['confidence'])
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()