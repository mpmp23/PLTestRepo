# case_api.py
# API to expose to frontend
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase

from ingest_case import (
    extract_content,
    neo4j_config,
)  # adjust if your module name differs
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._storage import Neo4jStorage
from neo4j_vis import visualize_neo4j_graph
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)


# TO DO: One DB per case_id
# def ensure_case_database(case_id: str):
#     """
#     Create a Neo4j database named `case_id` if it doesn't already exist.
#     Requires Neo4j 4.x+ and admin privileges.
#     """
#     uri = neo4j_config["neo4j_url"]
#     auth = neo4j_config["neo4j_auth"]
#     driver = GraphDatabase.driver(uri, auth=auth)
#     with driver.session(database="system") as session:
#         session.run(f"CREATE DATABASE {case_id} IF NOT EXISTS;")
#     driver.close()


def make_case_graph(case_id: str) -> GraphRAG:
    """
    Return a GraphRAG instance pointed at the per‑case database.
    """
    params = {**neo4j_config, "database": case_id}
    graph = GraphRAG(
        graph_storage_cls=Neo4jStorage,
        addon_params=params,
        working_dir=f"./deposition_info/graph_data/",  # TO DO: Must always be case-specific!
    )
    return graph


@app.post("/cases/{case_id}/ingest")
async def ingest_case(case_id: str, files: list[UploadFile] = File(...)):
    """
    Upload and ingest multiple files for a given case_id.
    Uses async insertion to avoid event-loop conflicts.
    """
    if not files:
        raise HTTPException(400, "No files provided for ingestion.")

    # # 1) Ensure the Neo4j DB exists
    # try:
    #     ensure_case_database(case_id)
    # except Exception as e:
    #     raise HTTPException(500, f"Could not create DB: {e}")

    # 2) Save uploads and extract text
    upload_dir = Path("graph_rag") / "uploads" / case_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    ingested = []
    texts = []
    for upload in files:
        dest = upload_dir / upload.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(upload.file, f)
        text = extract_content(str(dest))
        texts.append(text)
        ingested.append(upload.filename)
    # 3) Async insert into GraphRAG
    graph = make_case_graph(case_id)
    await graph.ainsert(text)

    # 4) Visualize the graph
    out_file = (
        Path("depositions") / "deposition_graphs" / f"{case_id}_deposition_graph.html"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    visualize_neo4j_graph(output_file=str(out_file))  # Convert Path to string

    return {"case_id": case_id, "ingested_files": ingested}


@app.post("/cases/{case_id}/query")
def query_case(case_id: str, prompt: str = Form(...)):
    """
    Run a RAG query against the case-specific GraphRAG.
    """
    # ensure_case_database(case_id)

    graph = make_case_graph(case_id)
    suffix = (
        "\nYou are analyzing a legal deposition transcript. "
        "Summarize key witness statements, extract facts and events, "
        "and list follow-up questions in 5-6 bullet points."
    )
    answer = graph.query(prompt + suffix, param=QueryParam(mode="local"))
    return {"case_id": case_id, "analysis": answer}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "rag_api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8002)), reload=True
    )
