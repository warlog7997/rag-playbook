"""
Chapter 1: The simplest possible RAG system.

What it does:
  1. Loads the NovaDash docs from ChromaDB
  2. Embeds a question
  3. Retrieves the top 3 most similar chunks
  4. Asks Claude to answer using those chunks

Run: python demo.py  (make sure you ran ../ingest.py first)
"""
import sys
from pathlib import Path

# Allow importing from learn/utils.py regardless of where we run from
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import vector_search, ask_claude, format_results

# -----------------------------------------------------------------------------
# The question we want to answer
# -----------------------------------------------------------------------------
QUESTION = "How do I reset my password in NovaDash?"

print(f"\nQuestion: {QUESTION}\n")

# -----------------------------------------------------------------------------
# STEP 1: RETRIEVE — find the most relevant chunks via vector similarity
# -----------------------------------------------------------------------------
print("Step 1: Searching for relevant docs...")
hits = vector_search(QUESTION, top_k=3)
format_results(hits, title="Retrieved Chunks")

# -----------------------------------------------------------------------------
# STEP 2: BUILD CONTEXT — format the chunks into a readable prompt
# -----------------------------------------------------------------------------
context = "\n\n---\n\n".join([
    f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
    for h in hits
])

# -----------------------------------------------------------------------------
# STEP 3: GENERATE — ask Claude to answer using only the retrieved context
# -----------------------------------------------------------------------------
print("Step 2: Asking Claude to answer using retrieved context...\n")

system_prompt = """You are a helpful support assistant for NovaDash.
Answer the user's question using ONLY the provided documentation context.
If the answer isn't in the context, say "I don't have enough information to answer that."
Be concise and direct."""

user_prompt = f"""Documentation context:
{context}

Question: {QUESTION}"""

answer = ask_claude(system=system_prompt, user=user_prompt, model="claude-haiku-4-5-20251001")

print("=" * 60)
print("  Answer")
print("=" * 60)
print(answer)
print()

# -----------------------------------------------------------------------------
# BONUS: Show what happens when we ask something NOT in the docs
# -----------------------------------------------------------------------------
print("\n" + "=" * 60)
print("  Testing with a question NOT in the docs...")
print("=" * 60)

unknown_question = "What is NovaDash's office address?"
hits2 = vector_search(unknown_question, top_k=3)
context2 = "\n\n---\n\n".join([
    f"Source: {h['source']} | Section: {h['section']}\n{h['text']}"
    for h in hits2
])

answer2 = ask_claude(
    system=system_prompt,
    user=f"Documentation context:\n{context2}\n\nQuestion: {unknown_question}"
)

print(f"Question: {unknown_question}")
print(f"\nAnswer: {answer2}")
print()

# -----------------------------------------------------------------------------
# Key insight
# -----------------------------------------------------------------------------
print("=" * 60)
print("  Key Insight")
print("=" * 60)
print("""
The first answer was grounded in real docs.
The second answer correctly said it doesn't know.

But notice: the first question used 'reset my password' — and the docs
call this 'account recovery via email verification token flow'.

Vector search happened to bridge this gap because the intro section
mentions both concepts. But it doesn't ALWAYS work.

See Chapter 2 to learn when naive vector search fails.
""")
