import json
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from config import settings, BRAND_CONFIGS

_client: chromadb.ClientAPI | None = None
_embedder: SentenceTransformer | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def initialize() -> None:
    """Load FAQ JSON files into brand-specific ChromaDB collections."""
    client = _get_client()
    embedder = _get_embedder()

    for brand_key, brand_config in BRAND_CONFIGS.items():
        collection_name = brand_config["collection"]
        faq_path = Path(brand_config["faq_file"])

        if not faq_path.exists():
            print(f"  [WARN] FAQ file not found: {faq_path}")
            continue

        # Delete existing collection and recreate
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        with open(faq_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for i, faq in enumerate(faqs):
            # Combine question and answer for richer embeddings
            doc_text = f"Q: {faq['question']}\nA: {faq['answer']}"
            documents.append(doc_text)
            metadatas.append({
                "question": faq["question"],
                "answer": faq["answer"],
                "category": faq.get("category", "general"),
                "brand": brand_key,
            })
            ids.append(f"{brand_key}_{i}")

        # Also load any PDF/text docs from the docs directory
        docs_dir = Path(brand_config["docs_dir"])
        if docs_dir.exists():
            doc_idx = len(faqs)
            for doc_file in docs_dir.glob("*.txt"):
                content = doc_file.read_text(encoding="utf-8")
                # Split into chunks of ~500 chars
                chunks = _chunk_text(content, chunk_size=500, overlap=50)
                for j, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "question": "",
                        "answer": chunk,
                        "category": "document",
                        "brand": brand_key,
                        "source": doc_file.name,
                    })
                    ids.append(f"{brand_key}_doc_{doc_idx}_{j}")
                doc_idx += 1

        if documents:
            # Embed and add in batches
            batch_size = 64
            for start in range(0, len(documents), batch_size):
                end = min(start + batch_size, len(documents))
                batch_docs = documents[start:end]
                batch_embeds = embedder.encode(batch_docs).tolist()
                collection.add(
                    documents=batch_docs[: end - start],
                    embeddings=batch_embeds,
                    metadatas=metadatas[start:end],
                    ids=ids[start:end],
                )

            print(f"  [OK] {brand_config['name']}: {len(documents)} chunks indexed into '{collection_name}'")


def search(brand: str, query: str, top_k: int = 3) -> list[dict]:
    """Search brand-specific collection for relevant chunks.

    Returns list of dicts with keys: answer, question, category, distance.
    Filters out results with cosine distance > 1.5.
    """
    brand_config = BRAND_CONFIGS.get(brand)
    if not brand_config:
        return []

    client = _get_client()
    embedder = _get_embedder()

    try:
        collection = client.get_collection(brand_config["collection"])
    except Exception:
        return []

    query_embedding = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["metadatas", "distances"],
    )

    chunks = []
    if results and results["metadatas"] and results["distances"]:
        for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
            if distance <= 1.5:
                chunks.append({
                    "answer": metadata.get("answer", ""),
                    "question": metadata.get("question", ""),
                    "category": metadata.get("category", ""),
                    "distance": distance,
                })

    return chunks


def rebuild_collection(brand: str) -> None:
    """Rebuild a single brand's collection."""
    client = _get_client()
    brand_config = BRAND_CONFIGS.get(brand)
    if not brand_config:
        print(f"  [ERROR] Unknown brand: {brand}")
        return

    try:
        client.delete_collection(brand_config["collection"])
    except Exception:
        pass

    initialize()


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


if __name__ == "__main__":
    print("Initializing vector store...")
    initialize()
    print("\nTesting search...")
    for brand in ["ticket99", "eventitans"]:
        results = search(brand, "how much does it cost?")
        print(f"\n{brand} results for 'how much does it cost?':")
        for r in results:
            print(f"  [{r['distance']:.3f}] {r['question'][:80]}")
