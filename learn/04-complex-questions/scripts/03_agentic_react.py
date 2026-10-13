"""
Chapter 4, Script 3: Agentic RAG with ReAct loop.

The most powerful approach for complex questions. Instead of deciding upfront
how many queries to run, we give Claude a 'search' tool and let it:
  1. Think about what it needs
  2. Search for it
  3. Read the results
  4. Decide if it has enough information
  5. Search again if needed
  6. Return the final answer when satisfied

This is the ReAct (Reason + Act) pattern:
  Thought > Action > Observation > Thought > ... > Final Answer

Max 5 iterations to prevent infinite loops.

Run: python 03_agentic_react.py  (from the learn/ directory)
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils import hybrid_search
import anthropic
import keyring

COMPLEX_QUERY = (
    "Compare how Free and Pro plans handle user limits and project limits, "
    "and what happens when you exceed those limits."
)

# The search tool definition for Claude's tool use
SEARCH_TOOL = {
    "name": "search_docs",
    "description": (
        "Search the NovaDash documentation for relevant information. "
        "Use this to find specific facts, policies, limits, and procedures. "
        "You can call this multiple times with different queries to gather "
        "information from different parts of the documentation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query — be specific for better results. "
                               "Example: 'Free plan project limit' is better than 'plans'.",
            }
        },
        "required": ["query"],
    },
}

AGENT_SYSTEM = """You are a helpful NovaDash support assistant with access to the
NovaDash documentation via a search tool.

When answering questions:
1. Think about what information you need
2. Use the search_docs tool to find relevant documentation
3. You can search multiple times with different queries to gather all needed information
4. Once you have enough information, provide a comprehensive, accurate answer
5. Structure your answer clearly with headers when answering multi-part questions
6. Only state facts that are supported by the documentation you've retrieved

IMPORTANT: Prefer multiple specific searches over one broad search. If a question
asks about multiple topics (e.g., user limits AND project limits), search for each
topic separately."""


def run_search(query: str) -> str:
    """Execute a search and return formatted results as a string for the agent."""
    hits = hybrid_search(query, top_k=5)
    if not hits:
        return "No relevant documentation found for this query."

    results = []
    for i, hit in enumerate(hits[:4], 1):
        results.append(
            f"[{i}] Source: {hit['source']} | Section: {hit['section']}\n"
            f"{hit['text'][:600]}"
        )
    return "\n\n---\n\n".join(results)


def run_react_agent(question: str, max_iterations: int = 5) -> dict:
    """
    Run the ReAct agent loop.

    Returns a dict with:
      - final_answer: str
      - iterations: list of {thought, search_query, results_preview}
      - total_searches: int
    """
    api_key = keyring.get_password("Anthorpic", "API_KEY")
    client = anthropic.Anthropic(api_key=api_key.strip())

    messages = [{"role": "user", "content": question}]
    iterations = []
    total_searches = 0

    print(f"\nStarting ReAct agent loop (max {max_iterations} iterations)...")
    print("-" * 60)

    for iteration in range(max_iterations):
        print(f"\n[Iteration {iteration + 1}]")

        # Call Claude with the search tool available
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=AGENT_SYSTEM,
            tools=[SEARCH_TOOL],
            messages=messages,
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Claude has finished — extract the final answer
            final_answer = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_answer = block.text
            print(f"Agent finished after {iteration + 1} iteration(s).")
            return {
                "final_answer": final_answer,
                "iterations": iterations,
                "total_searches": total_searches,
            }

        elif response.stop_reason == "tool_use":
            # Claude wants to use the search tool
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for tool_use in tool_uses:
                query = tool_use.input.get("query", "")
                total_searches += 1

                print(f"  Searching: '{query}'")

                # Execute the search
                results = run_search(query)
                results_preview = results[:300]

                print(f"  Results preview: {results_preview[:150]}...")

                iterations.append({
                    "iteration": iteration + 1,
                    "search_query": query,
                    "results_preview": results_preview,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": results,
                })

            # Add Claude's response and tool results to message history
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Unexpected stop reason
            print(f"  Unexpected stop_reason: {response.stop_reason}")
            break

    # If we hit max_iterations, extract whatever Claude has so far
    print(f"\nReached max iterations ({max_iterations}). Extracting final answer...")
    final_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=AGENT_SYSTEM + "\n\nYou have reached the maximum number of searches. "
               "Synthesize what you know into a final answer now.",
        messages=messages + [{"role": "user", "content": "Please provide your final answer now."}],
    )
    final_text = ""
    for block in final_response.content:
        if hasattr(block, "text"):
            final_text += block.text

    return {
        "final_answer": final_text,
        "iterations": iterations,
        "total_searches": total_searches,
    }


# -----------------------------------------------------------------------------
# Run the agent
# -----------------------------------------------------------------------------
print("=" * 70)
print("  Chapter 4 — Agentic RAG with ReAct Loop")
print("=" * 70)
print(f"\nQuestion: {COMPLEX_QUERY}\n")

result = run_react_agent(COMPLEX_QUERY)

# Print the reasoning trace
print("\n\n" + "=" * 70)
print("  Agent Reasoning Trace")
print("=" * 70)
print(f"\nTotal searches performed: {result['total_searches']}")
for it in result["iterations"]:
    print(f"\n  Iteration {it['iteration']}: Searched for '{it['search_query']}'")
    print(f"  Results: {it['results_preview'][:120].strip()}...")

# Print the final answer
print("\n\n" + "=" * 70)
print("  Final Answer")
print("=" * 70)
print(result["final_answer"])

# -----------------------------------------------------------------------------
# Comparison summary
# -----------------------------------------------------------------------------
print("\n\n" + "=" * 70)
print("  Why Agentic RAG Works for This Question")
print("=" * 70)
print(f"""
The agent made {result['total_searches']} targeted searches:
{chr(10).join(f"  {i+1}. '{it['search_query']}'" for i, it in enumerate(result['iterations']))}

Each search was MORE targeted than the last — the agent used what it found
to formulate better follow-up queries. This adaptive search strategy is
why agentic RAG succeeds where fixed-pipeline approaches struggle.

Compare with:
  Single-query RAG: 1 search, misses critical sections
  Multi-query:      4 predefined searches, more coverage but not adaptive
  Decomposition:    2-3 predefined searches, structured but not adaptive
  Agentic ReAct:   {result['total_searches']} adaptive searches, self-correcting

For this type of multi-faceted question, agentic RAG is clearly superior.
The cost: {result['total_searches'] + 1} API calls and ~10-15 seconds vs ~1s for single-query.

Next: Chapter 5 — Even perfect retrieval can produce hallucinated answers.
""")
