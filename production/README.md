# Production RAG Patterns

You've completed the learning track. These modules cover production-grade patterns used in
real systems built for healthcare platforms, pharmacy automation, and SaaS infrastructure.

The learning track taught you the fundamentals through deliberate, isolated examples.
Production systems require all of those pieces working together, plus orchestration,
reliability, and observability layers that don't fit neatly into a single script.

---

## Module Overview

| Module                    | Pattern                    | Real System It Came From                        |
|--------------------------|----------------------------|-------------------------------------------------|
| [01-langgraph](01-langgraph/)             | Multi-agent DAG orchestration | V2 migration tool (7-agent pipeline)         |
| [02-human-in-the-loop](02-human-in-the-loop/)     | Confidence-gated human review | V2 migration — approval between every phase  |
| [03-guardrails](03-guardrails/)            | Production guardrail service  | Healthcare Jira assistant                    |
| [04-mcp-tools](04-mcp-tools/)             | Agent tool servers (MCP)      | Jira assistant + pharmacy API calls          |
| [05-eval-in-ci](05-eval-in-ci/)            | Evaluation in CI/CD           | Regression gates for prompt changes          |
| [06-async-pipelines](06-async-pipelines/)       | Celery/Redis batch ingestion  | Ingesting 400+ PHP files with Claude         |
| [07-knowledge-graphs](07-knowledge-graphs/)      | GraphRAG + Neo4j              | Relationship queries in codebases            |
| [08-document-intelligence](08-document-intelligence/) | OCR + structured extraction | Fax labeling system (9,000+ healthcare faxes)|

---

## How These Connect to the Learning Track

```
Chapter 2 (Hybrid Search)   →  Production 05 (Eval in CI) verifies it stays working
Chapter 4 (Agentic ReAct)   →  Production 01 (LangGraph) scales it to multi-agent
Chapter 5 (Guardrails)      →  Production 03 (Guardrail Service) deploys it as an API
Chapter 5 (Hallucination)   →  Production 02 (Human-in-the-loop) handles the failures
Chapter 6 (Evaluation)      →  Production 05 (Eval in CI) automates the evaluation
```

The production modules assume you've read all 6 chapters of the learning track.
If you haven't, start there.

---

## The Real Systems Behind These Patterns

### V2 Migration Tool

A multi-agent pipeline that migrated a legacy PHP prescription prediction system to a
modern architecture. 7 specialized agents: discovery, planner, reviewer, generator,
validator, fixer, and flip (to production). Human approval gates between every phase.
Built with LangGraph, ran for 6+ hours per migration, handled 400+ source files.

### Healthcare Jira Assistant

An AI-powered Jira ticket management system for a healthcare platform. RAG over internal
documentation, structured workflows for patient transfers, guardrails for PHI compliance.
The system that produced every "real story" in the learning track chapters.

### Fax Labeling System

An automated pipeline for classifying 9,000+ incoming healthcare faxes. AWS Textract for
OCR, Claude for structured data extraction, human verification loop for low-confidence
classifications. 94% automation rate achieved.

---

## Getting Started

Each production module has its own README with:
- The pattern explained
- The real story behind it
- What the implementation covers
- Dependencies and setup

Start with the module most relevant to your current challenge.
