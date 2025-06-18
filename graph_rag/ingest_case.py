import logging
from pathlib import Path
from dotenv import load_dotenv
import ollama

import os
import sys

sys.path.append("..")
import logging
import numpy as np
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash, wrap_embedding_func_with_attrs

load_dotenv(override=True)

# Load environment variables from .env, override existing ones\ nload_dotenv(override=True)

# Configure logging\ nlogging.basicConfig(level=logging.WARNING)
logging.getLogger("nano-graphrag").setLevel(logging.INFO)

# Import GraphRAG and storage backend
from nano_graphrag import GraphRAG, QueryParam
from nano_graphrag._storage import Neo4jStorage
from neo4j_vis import visualize_neo4j_graph

# Assumed llm model settings
MODEL = "gemma3:4b-it-qat"

# Assumed embedding model settings
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_MODEL_DIM = 768
EMBEDDING_MODEL_MAX_TOKENS = 8192


async def ollama_model_if_cache(
    prompt, system_prompt=None, history_messages=[], **kwargs
) -> str:
    # remove kwargs that are not supported by ollama
    kwargs.pop("max_tokens", None)
    kwargs.pop("response_format", None)

    ollama_client = ollama.AsyncClient()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Get the cached response if having-------------------
    hashing_kv: BaseKVStorage = kwargs.pop("hashing_kv", None)
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    if hashing_kv is not None:
        args_hash = compute_args_hash(MODEL, messages)
        if_cache_return = await hashing_kv.get_by_id(args_hash)
        if if_cache_return is not None:
            return if_cache_return["return"]
    # -----------------------------------------------------
    response = await ollama_client.chat(model=MODEL, messages=messages, **kwargs)

    result = response["message"]["content"]
    # Cache the response if having-------------------
    if hashing_kv is not None:
        await hashing_kv.upsert({args_hash: {"return": result, "model": MODEL}})
    # -----------------------------------------------------
    return result

# We're using Ollama to generate embeddings for the BGE model
@wrap_embedding_func_with_attrs(
    embedding_dim=EMBEDDING_MODEL_DIM,
    max_token_size=EMBEDDING_MODEL_MAX_TOKENS,
)
async def ollama_embedding(texts: list[str]) -> np.ndarray:
    embed_text = []
    for text in texts:
        data = ollama.embeddings(model=EMBEDDING_MODEL, prompt=text)
        embed_text.append(data["embedding"])

    return embed_text


# Neo4j connection config
neo4j_config = {
    "neo4j_url": os.getenv("NEO4J_URL", "bolt://localhost:7687"),
    "neo4j_auth": (
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "testpass"),
    ),
}

# Initialize GraphRAG for legal depositions
graph_func = GraphRAG(
    graph_storage_cls=Neo4jStorage,
    addon_params=neo4j_config,
    working_dir=os.getenv("WORKING_DIR", "./deposition_info/graph_data"),
    best_model_func=ollama_model_if_cache,
        cheap_model_func=ollama_model_if_cache,
        embedding_func=ollama_embedding,
)


def extract_content(file_path: str) -> str:
    """
    Load content from .txt, .md, .pdf, .docx, or fallback: returns full text.
    """
    suffix = Path(file_path).suffix.lower()
    if suffix in (".txt", ".md"):
        return Path(file_path).read_text(encoding="utf-8")
    elif suffix == ".pdf":
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        from docx import Document

        doc = Document(file_path)
        return "\n".join(par.text for par in doc.paragraphs)
    else:
        return Path(file_path).read_bytes().decode("utf-8", errors="ignore")

def insert_and_visualize(file_path: str, vis_output: str):
    """
    Insert deposition transcript into GraphRAG and generate HTML visualization.
    """
    content = extract_content(file_path)
    graph_func.insert(content)
    visualize_neo4j_graph(output_file=vis_output)


def process_documents(input_dir: str, output_dir: str):
    """
    Ingest all deposition files in a directory into the graph and output visualizations,
    skipping INFO.md.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for file in Path(input_dir).iterdir():
        if not file.is_file():
            continue
        # skip INFO.md
        if file.name.lower() == "info.md":
            continue

        out_file = Path(output_dir) / f"{file.stem}_deposition_graph.html"
        try:
            insert_and_visualize(str(file), str(out_file))
            print(f"Processed deposition: {file.name}")
        except Exception as e:
            print(f"Error processing {file.name}: {e}")


def run_query(user_prompt: str) -> str:
    """
    Perform a local GraphRAG query tailored for legal depositions.
    """
    deposition_suffix = (
        "\nYou are analyzing a legal deposition transcript. "
        "Summarize key witness statements, extract facts and events, and list follow-up questions in 5-6 bullet points."
    )
    final_prompt = user_prompt + deposition_suffix
    return graph_func.query(final_prompt, param=QueryParam(mode="local"))


if __name__ == "__main__":
    # Ingest deposition transcripts and visualize
    input_directory = os.getenv("INPUT_DIR", "./deposition_info/depositions")
    output_directory = os.getenv("OUTPUT_DIR", "./deposition_info/deposition_graphs")
    process_documents(input_directory, output_directory)
    # Example deposition query
    example_prompt = "What part of Yancy's testimony don't add up?."
    print("\n\n\nDeposition Analysis:", run_query(example_prompt))
