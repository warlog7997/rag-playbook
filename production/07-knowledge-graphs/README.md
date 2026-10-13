# Production 07 — Knowledge Graphs: GraphRAG and Neo4j

## When Vector Search Isn't Enough

Vector search is excellent at answering: *"What does this document say about topic X?"*

It struggles with: *"What calls what? Which modules depend on this function? How does
data flow from endpoint A to database table B?"*

These are **relationship queries** — and relationship queries are where knowledge graphs
shine. Vector similarity cannot express "depends on," "calls," "is a subtype of," or
"was modified after."

---

## The Real Story

During the V2 migration tool's discovery phase, we needed to answer questions like:
- "Which PHP files call `prescriptionCheck()`?"
- "If we change the database schema for `tbl_prescriptions`, which files break?"
- "What is the full call chain from the API endpoint to the database query?"

The discovery agent tried vector search first. It retrieved the function definition and
a few callers — but missed deeply nested callers three or four levels down the call chain.

We added a Neo4j graph alongside the vector index:
```
(api_endpoint) -[:CALLS]-> (service_function) -[:CALLS]-> (db_query) -[:READS]-> (table)
```

Now: "What breaks if tbl_prescriptions changes?"
```cypher
MATCH (f:File)-[:CALLS*]->(:Query)-[:READS]->(:Table {name: 'tbl_prescriptions'})
RETURN DISTINCT f.name
```

The graph returned 23 files. Vector search had found 7.

---

## Graph vs. Vector: When to Use Each

| Query Type                                    | Vector  | Graph   |
|----------------------------------------------|---------|---------|
| "What does X mean?"                           | ✓       | ~       |
| "How does feature X work?"                    | ✓       | ~       |
| "What calls function X?"                      | ~       | ✓       |
| "What would break if I change Y?"             | ✗       | ✓       |
| "Show me all dependencies of module Z"        | ✗       | ✓       |
| "Find all tasks assigned to Alice"            | ✗       | ✓       |
| "What tasks block this task?"                 | ✗       | ✓       |
| "Find content similar to this paragraph"      | ✓       | ✗       |

The pattern: use vector for semantic similarity, use graph for structural relationships.
For complex questions, use both — retrieve candidates with vector, filter/expand with graph.

---

## NovaDash Knowledge Graph Model

For NovaDash, a knowledge graph would model:

```
(:Project {name, status, visibility})
    -[:HAS_TASK]-> (:Task {title, priority, status})
    -[:HAS_MEMBER]-> (:User {name, role})

(:Task)
    -[:BLOCKS]-> (:Task)           // dependency
    -[:ASSIGNED_TO]-> (:User)
    -[:HAS_SUBTASK]-> (:Task)
    -[:TRIGGERS]-> (:Notification)

(:User)
    -[:MEMBER_OF]-> (:Project)
    -[:INVITED_BY]-> (:User)
```

This enables queries vector search can't handle:
```cypher
// Find all tasks that are (directly or indirectly) blocked by TASK-42
MATCH (root:Task {id: 'TASK-42'})<-[:BLOCKS*]-(dependent:Task)
RETURN dependent.title, length(path) as blocking_depth

// Find users who have access to both Project Alpha and Project Beta
MATCH (u:User)-[:MEMBER_OF]->(:Project {name: 'Alpha'})
MATCH (u)-[:MEMBER_OF]->(:Project {name: 'Beta'})
RETURN u.name
```

---

## GraphRAG Architecture

GraphRAG combines vector retrieval with graph traversal:

```
User Query: "What are all the dependencies of the authentication module?"
     │
     ├── Vector Search: finds relevant documentation chunks
     │   Result: authentication.md overview, SSO setup section
     │
     └── Graph Query: traverses dependency relationships
         MATCH (m:Module {name: 'auth'})-[:DEPENDS_ON*]->(dep)
         RETURN dep.name, dep.type
         Result: session_manager, jwt_validator, rate_limiter, db_connection_pool

Combined context:
  Documentation text (from vector) + Dependency list (from graph)
     │
     ▼
Claude synthesizes a complete answer
```

---

## Building a Knowledge Graph with Neo4j

### Defining the Schema

```python
from neo4j import GraphDatabase

# Create constraints for uniqueness
def setup_schema(driver):
    with driver.session() as session:
        session.run("CREATE CONSTRAINT task_id IF NOT EXISTS "
                    "FOR (t:Task) REQUIRE t.id IS UNIQUE")
        session.run("CREATE CONSTRAINT user_id IF NOT EXISTS "
                    "FOR (u:User) REQUIRE u.id IS UNIQUE")
        session.run("CREATE INDEX task_status IF NOT EXISTS "
                    "FOR (t:Task) ON (t.status)")
```

### Ingesting Relationships

```python
def ingest_task_dependencies(tasks: list[dict], dependencies: list[dict]):
    with driver.session() as session:
        # Create tasks
        for task in tasks:
            session.run(
                "MERGE (t:Task {id: $id}) SET t.title = $title, t.status = $status",
                id=task["id"], title=task["title"], status=task["status"]
            )

        # Create dependency relationships
        for dep in dependencies:
            session.run(
                "MATCH (a:Task {id: $blocker_id}), (b:Task {id: $blocked_id}) "
                "MERGE (a)-[:BLOCKS]->(b)",
                blocker_id=dep["blocker_id"],
                blocked_id=dep["blocked_id"],
            )
```

---

## Coming Soon

Full implementation covering:
- Neo4j setup with Docker
- Knowledge graph schema for NovaDash (tasks, projects, users, dependencies)
- Ingestion pipeline: parse docs into graph entities
- GraphRAG query pipeline: vector + graph combined retrieval
- Comparison queries showing where graph beats vector search
- Agent with both vector_search and graph_query tools

**Prerequisites:** `pip install neo4j`, `docker run neo4j`
