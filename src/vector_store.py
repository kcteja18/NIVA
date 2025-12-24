"""
ChromaDB Vector Store for semantic scheme search.
Uses persistent storage and sentence-transformers embeddings.
"""
import os
import json
import chromadb
from chromadb.utils import embedding_functions


class SchemeVectorStore:
    """ChromaDB-based vector store for government schemes."""
    
    def __init__(self, persist_path: str = "./chroma_db"):
        self.persist_path = persist_path
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self._get_or_create_collection()
        print(f"✅ ChromaDB initialized at {persist_path}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create and populate it."""
        collection = self.client.get_or_create_collection(
            name="schemes",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Only populate if empty
        if collection.count() == 0:
            self._populate_collection(collection)
        
        return collection
    
    def _populate_collection(self, collection):
        """Load schemes from JSON and add to collection."""
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "schemes.json")
        
        if not os.path.exists(data_path):
            print(f"⚠️ Schemes data not found at {data_path}")
            return
        
        with open(data_path, "r", encoding="utf-8") as f:
            schemes = json.load(f)
        
        documents, metadatas, ids = [], [], []
        
        for scheme in schemes:
            # Create rich document text for embedding
            doc_text = f"""
            {scheme['name_en']} {scheme['name_te']}
            {scheme['description_en']} {scheme['description_te']}
            {scheme['benefits_en']} {scheme['benefits_te']}
            Sector: {scheme['sector']}
            """
            
            documents.append(doc_text)
            metadatas.append({
                "id": scheme["id"],
                "name_en": scheme["name_en"],
                "name_te": scheme["name_te"],
                "sector": scheme["sector"],
                "benefits_en": scheme["benefits_en"],
                "benefits_te": scheme["benefits_te"]
            })
            ids.append(scheme["id"])
        
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"✅ Added {len(schemes)} schemes to vector store")
    
    def search(self, query: str, language: str = "te", n_results: int = 3) -> str:
        """Search for relevant schemes."""
        results = self.collection.query(query_texts=[query], n_results=n_results)
        
        if not results["metadatas"] or not results["metadatas"][0]:
            return "కోరిన యోజనలు కనబడలేదు." if language == "te" else "No schemes found."
        
        response = ""
        for i, meta in enumerate(results["metadatas"][0], 1):
            name = meta.get(f"name_{language}", meta.get("name_en", "Unknown"))
            benefits = meta.get(f"benefits_{language}", meta.get("benefits_en", ""))
            sector = meta.get("sector", "")
            
            if language == "te":
                response += f"{i}. **{name}** ({sector})\n   లాభాలు: {benefits}\n\n"
            else:
                response += f"{i}. **{name}** ({sector})\n   Benefits: {benefits}\n\n"
        
        return response


# Singleton instance
_vector_store = None

def get_vector_store() -> SchemeVectorStore:
    """Get or create the vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = SchemeVectorStore()
    return _vector_store
