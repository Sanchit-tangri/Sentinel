import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

from schemas.models import RemediationMemory, VulnerabilityFinding

class MemoryStore:
    """
    Self-learning RAG Memory Store.
    Stores and indexes vulnerability remediation patterns, diffs, and security post-mortems.
    Falls back to a JSON-backed memory if chromadb is not yet installed.
    """
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or os.path.join(os.path.dirname(__file__), "storage")
        os.makedirs(self.persist_dir, exist_ok=True)
        self.fallback_file = os.path.join(self.persist_dir, "remediation_memories.json")

        if HAS_CHROMADB:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name="remediation_memories",
                metadata={"description": "Sentinel self-learning remediation memory"}
            )
        else:
            self.client = None
            self.collection = None
            if not os.path.exists(self.fallback_file):
                with open(self.fallback_file, "w") as f:
                    json.dump([], f)

    def record_success(
        self,
        vulnerability: VulnerabilityFinding,
        vulnerable_code: str,
        patched_diff: str,
        explanation: str
    ) -> RemediationMemory:
        """
        Ingest verified remediation fix into the RAG vector store.
        """
        memory_id = f"mem-{uuid.uuid4().hex[:8]}"
        memory = RemediationMemory(
            memory_id=memory_id,
            cwe_id=vulnerability.cwe_id or "UNKNOWN",
            vulnerability_title=vulnerability.title,
            vulnerable_pattern=vulnerability.snippet or vulnerable_code[:200],
            patched_diff=patched_diff,
            explanation=explanation,
            timestamp=datetime.utcnow().isoformat()
        )

        doc_text = f"CWE: {memory.cwe_id} | Vulnerability: {memory.vulnerability_title}\nPattern:\n{memory.vulnerable_pattern}\nFix:\n{memory.patched_diff}\nRationale: {memory.explanation}"

        if HAS_CHROMADB and self.collection:
            self.collection.add(
                ids=[memory.memory_id],
                documents=[doc_text],
                metadatas=[{
                    "cwe_id": memory.cwe_id or "",
                    "title": memory.vulnerability_title,
                    "timestamp": memory.timestamp
                }]
            )
        else:
            data = []
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, "r") as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        data = []
            data.append(memory.model_dump())
            with open(self.fallback_file, "w") as f:
                json.dump(data, f, indent=2)

        return memory

    def search_similar_remediations(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve nearest verified remediation memories to guide Patcher and Auditor.
        """
        if HAS_CHROMADB and self.collection:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, max(1, self.collection.count()))
            )
            hits = []
            if results and results.get("documents"):
                for idx, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][idx] if results.get("metadatas") else {}
                    hits.append({
                        "id": results["ids"][0][idx],
                        "document": doc,
                        "metadata": metadata
                    })
            return hits
        else:
            # Fallback simple keyword match
            hits = []
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, "r") as f:
                    try:
                        memories = json.load(f)
                        for item in memories:
                            if any(q.lower() in item.get("vulnerability_title", "").lower() or 
                                   q.lower() in item.get("vulnerable_pattern", "").lower()
                                   for q in query.split()):
                                hits.append({
                                    "id": item["memory_id"],
                                    "document": item["explanation"],
                                    "metadata": {"cwe_id": item["cwe_id"], "title": item["vulnerability_title"]}
                                })
                                if len(hits) >= top_k:
                                    break
                    except Exception:
                        pass
            return hits
