# Production 01 — LangGraph: Multi-Agent Orchestration

## What is LangGraph?

LangGraph is a library for building stateful, multi-actor AI applications. It extends
LangChain's concept of a "chain" into a **directed graph** where:

- **Nodes** are processing steps (LLM calls, tool executions, human reviews)
- **Edges** are the transitions between steps
- **State** is a typed dictionary that flows through the graph, accumulating results
- **Conditional edges** allow branching based on the current state

Unlike a linear pipeline (A → B → C), LangGraph lets you build:
- Cycles (loops until a condition is met)
- Parallel branches
- Conditional routing (go to X if confident, go to Y if not)
- Human interrupt points

---

## The Real Story

We built a V2 migration tool to move a 400+ file PHP codebase to a new architecture.
The pipeline used 7 specialized agents connected as a directed graph:

```
[Discovery] → [Planner] → [Human Approval] → [Reviewer] → [Human Approval]
                                                                    ↓
[Flip to Production] ← [Human Approval] ← [Validator] ← [Fixer] ← [Generator]
```

Each node was a specialized Claude agent with a focused role:

1. **Discovery**: Reads all PHP files, builds a dependency map of what calls what
2. **Planner**: Generates a migration plan — which files to change and in what order
3. **Reviewer**: Reviews the plan for logical errors and missing dependencies
4. **Generator**: Writes the actual migrated code for each file
5. **Validator**: Tests the generated code against the original behavior
6. **Fixer**: Fixes validation failures (loops back to Generator if needed)
7. **Flip**: Deploys the validated code to production

**Human approval gates** sat between Discovery→Planner, Reviewer→Generator, and
Validator→Flip. No phase could proceed without explicit human sign-off.

The graph ran for 6-8 hours per migration. LangGraph's persistent state meant the
graph could be paused, inspected, and resumed — critical for a long-running process
where a human might need to sleep between phases.

---

## Why LangGraph Over Simple Function Calls?

**State persistence**: LangGraph checkpoints the graph state after every node.
If the process crashes after hour 5, you resume from the last checkpoint — not from scratch.

**Conditional routing**: The Validator node conditionally routes to Fixer (if tests fail)
or to the Human Approval gate (if tests pass). This would be spaghetti code with manual
if/else chains.

**Parallel execution**: Discovery can analyze multiple PHP files simultaneously via
parallel branches. LangGraph handles the fan-out and fan-in.

**Visualization**: LangGraph generates a Mermaid diagram of your graph automatically.
Essential for explaining the system to stakeholders.

**Human-in-the-loop**: Interrupt points are first-class citizens in LangGraph — not
an afterthought you bolt on with sleep() and input().

---

## Core Concepts

### Defining State

```python
from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class MigrationState(TypedDict):
    files_discovered: list[str]
    migration_plan: dict
    generated_code: dict[str, str]
    validation_results: list[dict]
    human_approved: bool
    current_phase: str
```

### Defining Nodes

```python
def discovery_node(state: MigrationState) -> MigrationState:
    """Read all PHP files and build dependency map."""
    # ... LLM call or code analysis here
    return {**state, "files_discovered": [...], "current_phase": "planning"}
```

### Conditional Edges

```python
def route_after_validation(state: MigrationState) -> str:
    """Route to fixer if tests fail, human approval if tests pass."""
    if all(r["passed"] for r in state["validation_results"]):
        return "human_approval"
    return "fixer"
```

### Building the Graph

```python
from langgraph.graph import StateGraph

workflow = StateGraph(MigrationState)
workflow.add_node("discovery", discovery_node)
workflow.add_node("planner", planner_node)
workflow.add_conditional_edges("validator", route_after_validation)
workflow.set_entry_point("discovery")
graph = workflow.compile(checkpointer=memory_saver)
```

---

## Coming Soon

Full implementation covering:
- Complete 7-node migration pipeline adapted for NovaDash API client generation
- Persistent checkpointing with SQLite
- Human interrupt points with a simple CLI approval interface
- Parallel file processing with fan-out/fan-in
- State inspection and debugging tools
- Mermaid diagram generation

**Prerequisites:** `pip install langgraph langchain-anthropic`
