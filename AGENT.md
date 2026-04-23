# AGENT.md

## Role

You are a coding and reasoning agent tasked with implementing a prototype based on the "rag-wiki" idea.

## Objective

Build a minimal working prototype of a rag-wiki system:

* Accepts a user question
* Retrieves relevant wiki pages (mock or simple markdown files)
* Generates an answer
* Verifies the answer against guidelines
* Either returns the answer or refuses/escalates

## Constraints

* Do NOT hallucinate outside the provided wiki content
* If unsure, respond with "I don't know" or escalate
* Stay within the defined domain (micro-wiki concept)

## System Design

Implement a simplified pipeline:

1. Input: user query
2. Classification:

   * Is this in-domain or out-of-domain?
3. Retrieval:

   * Load relevant markdown files
4. Generation:

   * Produce a draft answer
5. Verification:

   * Check:

     * grounded in sources
     * no hallucination
     * within scope
6. Gate:

   * If passes → return answer with sources
   * If fails → refuse or escalate

## Output Format

* Answer
* Sources used
* Confidence level (high / medium / low)

## Stretch Goals (optional)

* Add simple evaluation set
* Add logging of failed queries
* Simulate writeback mechanism

## Tech Suggestion

You may use:

* Python
* Node.js
* Simple file-based wiki (markdown)

Focus on clarity over complexity.
