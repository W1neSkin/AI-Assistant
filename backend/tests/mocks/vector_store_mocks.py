from typing import List, Optional
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.core.vector_stores import VectorStoreQuery

class MockVectorStore:
    def __init__(self):
        self.nodes = {}  # doc_id -> list of nodes
        
    def add(self, nodes: List[TextNode]) -> List[str]:
        for node in nodes:
            doc_id = node.metadata.get("doc_id")
            if doc_id not in self.nodes:
                self.nodes[doc_id] = []
            self.nodes[doc_id].append(node)
        return [node.metadata.get("doc_id") for node in nodes]
    
    def delete(self, ref_doc_id: str, **kwargs) -> None:
        if ref_doc_id in self.nodes:
            del self.nodes[ref_doc_id]
            
    def query(self, query: VectorStoreQuery) -> List[NodeWithScore]:
        # Return some mock results
        results = []
        for doc_nodes in self.nodes.values():
            for node in doc_nodes:
                if node.metadata.get("active") == "true":
                    results.append(
                        NodeWithScore(
                            node=node,
                            score=0.95
                        )
                    )
        return results[:query.similarity_top_k] if query.similarity_top_k else results

    def clear(self) -> None:
        self.nodes = {} 