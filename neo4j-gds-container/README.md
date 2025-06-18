# Neo4j with Graph Data Science (GDS) Docker Setup

This repository contains the necessary files to run Neo4j with the Graph Data Science plugin in a Docker container.

## Prerequisites

- Docker installed on your system
- The Neo4j Graph Data Science plugin JAR file (version 2.7.0)

## Directory Structure

```
neo4j-gds-container/
├── Dockerfile
├── README.md
└── plugins/
    └── neo4j-graph-data-science-2.7.0.jar
```

## Setup Instructions

1. Create the directory structure:
```bash
mkdir -p neo4j-gds-container/plugins
```

2. Download the GDS plugin (2.7.0) and place it in the plugins directory:
```bash
# Using PowerShell:
Invoke-WebRequest -Uri https://graphdatascience.ninja/neo4j-graph-data-science-2.7.0.jar -OutFile neo4j-gds-container/plugins/neo4j-graph-data-science-2.7.0.jar
```

3. Build the Docker image:
```bash
cd neo4j-gds-container
docker build -t neo4j-gds-custom .
```

4. Run the container:
```bash
docker run -d --name neo4j-gds -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/testpass neo4j-gds-custom
```

## Accessing Neo4j

- **Neo4j Browser**: http://localhost:7474
- **Bolt URL**: bolt://localhost:7687
- **Username**: neo4j
- **Password**: testpass

## Verifying GDS Installation

To verify that GDS is working, run this Cypher query in the Neo4j Browser:
```cypher
CALL gds.version();
```

## Container Management

Stop the container:
```bash
docker stop neo4j-gds
```

Start the container:
```bash
docker start neo4j-gds
```

Remove the container:
```bash
docker rm neo4j-gds
```

## Troubleshooting

If the container exits immediately after starting:
1. Check the logs:
```bash
docker logs neo4j-gds
```

2. Make sure the GDS plugin version (2.7.0) is compatible with the Neo4j version (5.16.0)

3. If you need to rebuild:
```bash
docker rm neo4j-gds              # Remove old container
docker build -t neo4j-gds-custom .  # Rebuild image
# Then run the container again with the command from step 4
``` 