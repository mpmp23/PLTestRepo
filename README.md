# PLTestRepo


# If you know nothing else...
1. ollama run gemma3:4b-it-qat in one terminal
2. in the other terminal, run the rest of this:
3. docker run -d --name neo4j-gds-new -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/testpass neo4j-gds-custom
4. python ingest_case.py


## to add in new information for now
- drag in files you want it to ingest -- i used https://github.com/BlairStanek/BLT/blob/master/RawData/Transcripts/Karin%20Lang%20deposition.txt and https://www.courtlistener.com/docket/17044058/625/delta-air-lines-inc-v-marriott-international-inc/

- run python ingest_case.py
- wait for it to finish ingesting! once ready, you should be free to ask it anything

## to ask it a question
- open computer terminal
- run madeleinepelli@Madeleines-Laptop-2 ~ % ollama run gemma3:4b-it-qat
- then you can ask it whatever!

## to connect to neo4j
- make sure the docker daemon is running -> docker run -d --name neo4j-gds-new -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/testpass neo4j-gds-custom
- open http://localhost:7474/browser/

## To delete all info in the DB:
MATCH (n)
DETACH DELETE n

## Front End Use
- Paralegals or attorneys add in queries about cases, akin to relativity's pitch about keeping data.
## RAG Database
- Currently pulling from random online depositions.
- Since my local model is so small, I'm running only one .txt file.
- CAN OCR pdfs and read them too.

## LLM Used
- Locally hosted Ollama LLM (gemma3:4b-it-qat)
- Azure's API use instead of local ollama? (for more parameters)

# Explanation
- This functions as an in-house Relativity competitor.
- GraphRAG is a way to enrich the context of any query using a graph data structure. Neo4j uses llms to generate cypher to be inserted. In order to generate the best 'links' and context for each case, we need a better model (where Azure API comes in).
- This model doesn't use memory - each query pulls from the same database-created 'context graph' to derive its answer.


## Problem
- i lack vram - need azure openai api key. better than using on ollama. i can't really process anything. azure openai - need access to generate better compute power.
