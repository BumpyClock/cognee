This is a fork of the original cognee project with a focus on giving AI agents long term memory that evolves over time rather than static linear memory. The goal is to create a more dynamic and adaptable memory system that can better support complex tasks and interactions.


## Getting Started

1. Clone the repository.
2. Install dependencies `uv, docker`
3. navigate to cognee-mcp directory.

You have two paths to run the mcp server 

### Docker (HTTP)
This is a single instance that can be used by several agents at once but has some latency due to the HTTP calls.

```bash
uv run python src/server.py --transport http --host 127.0.0.1 --port 8000 --path /mcp
```

### Local (Stdio)
```bash
uv run python src/server.py --transport stdio
```
You can still share the memory between agents in Stdio mode by using the same db. I recommend using the PG vector db for this.

Set the correct environment variables for the db connection in the .env file.

```bash

### PG Vector DB Setup

```bash
docker run --name pgv \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=mydb \
  -p 5432:5432 \
  -d pgvector/pgvector:pg17
```

### Neo4j setup
```bash
docker run \
    --name neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -e NEO4J_AUTH=neo4j/{password} \
    neo4j:latest
```
