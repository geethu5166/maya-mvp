"""
Vector Database Engine.
Semantic search and similarity detection using embeddings.

Features:
1. Event Embeddings (semantic understanding)
2. Semantic Similarity Search
3. Duplicate Detection
4. Threat Clustering
5. Recommendation Engine
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import json
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)


@dataclass
class Embedding:
    """Vector embedding for an event"""
    event_id: str
    vector: np.ndarray  # 768-dimensional embedding
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class SimilarityResult:
    """Result of similarity search"""
    query_event_id: str
    matched_event_id: str
    similarity_score: float  # 0-1
    matched_event_data: Dict[str, Any]


class EventEmbedder:
    """Create embeddings for events"""
    
    def __init__(self, embedding_dim: int = 768):
        """
        Initialize embedder.
        
        Args:
            embedding_dim: Embedding dimension
        """
        self.embedding_dim = embedding_dim
        # In production: use sentence-transformers.SentenceTransformer('all-MiniLM-L6-v2')
    
    async def embed_event(self, event: Dict[str, Any]) -> np.ndarray:
        """
        Create embedding for event.
        
        Args:
            event: Event to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Combine relevant event fields into text
            text_parts = [
                str(event.get('event_type', '')),
                str(event.get('description', '')),
                str(event.get('severity', '')),
                str(event.get('source_ip', '')),
                str(event.get('destination_ip', ''))
            ]
            
            combined_text = ' '.join(text_parts).lower()
            
            # Create simple embedding (hash-based representation)
            # In production: use actual transformer model
            embedding = await self._simple_hash_embedding(combined_text)
            
            return embedding
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            return np.zeros(self.embedding_dim)
    
    async def _simple_hash_embedding(self, text: str) -> np.ndarray:
        """
        Create simple hash-based embedding.
        
        In production: use sentence-transformers
        """
        # Use hash to create deterministic embedding
        words = text.split()
        embedding = np.zeros(self.embedding_dim)
        
        for i, word in enumerate(words):
            word_hash = hash(word) % self.embedding_dim
            embedding[word_hash] += 1.0
        
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    async def embed_batch(self, events: List[Dict[str, Any]]) -> List[Embedding]:
        """
        Embed multiple events.
        
        Args:
            events: List of events
            
        Returns:
            List of Embedding objects
        """
        embeddings = []
        
        for event in events:
            vector = await self.embed_event(event)
            embedding = Embedding(
                event_id=event.get('id', 'unknown'),
                vector=vector,
                timestamp=datetime.now(),
                metadata={
                    'event_type': event.get('event_type'),
                    'severity': event.get('severity')
                }
            )
            embeddings.append(embedding)
        
        return embeddings


class VectorDatabase:
    """In-memory vector database (production: use Milvus) """
    
    def __init__(self):
        """Initialize vector database"""
        self.embeddings: Dict[str, Embedding] = {}
        self.embedder = EventEmbedder()
    
    async def insert(self, embedding: Embedding) -> bool:
        """
        Insert embedding into database.
        
        Args:
            embedding: Embedding to insert
            
        Returns:
            Success status
        """
        try:
            self.embeddings[embedding.event_id] = embedding
            logger.debug(f"Inserted embedding: {embedding.event_id}")
            return True
        except Exception as e:
            logger.warning(f"Insertion failed: {e}")
            return False
    
    async def insert_batch(self, embeddings: List[Embedding]) -> int:
        """
        Insert multiple embeddings.
        
        Args:
            embeddings: List of embeddings
            
        Returns:
            Number inserted
        """
        count = 0
        for embedding in embeddings:
            if await self.insert(embedding):
                count += 1
        
        logger.info(f"Inserted {count}/{len(embeddings)} embeddings")
        return count
    
    async def search(self, query_vector: np.ndarray, 
                    top_k: int = 5,
                    threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Search for similar embeddings.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (event_id, similarity_score) tuples
        """
        if not self.embeddings:
            return []
        
        try:
            results = []
            
            # Calculate similarities
            for event_id, embedding in self.embeddings.items():
                similarity = cosine_similarity(
                    [query_vector],
                    [embedding.vector]
                )[0, 0]
                
                if similarity >= threshold:
                    results.append((event_id, float(similarity)))
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:top_k]
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []
    
    async def find_similar_events(self, event: Dict[str, Any],
                                 top_k: int = 5) -> List[SimilarityResult]:
        """
        Find events similar to query event.
        
        Args:
            event: Query event
            top_k: Number of results
            
        Returns:
            List of SimilarityResult objects
        """
        try:
            # Embed query event
            query_vector = await self.embedder.embed_event(event)
            
            # Search database
            matches = await self.search(query_vector, top_k=top_k)
            
            # Convert to SimilarityResult objects
            results = []
            for event_id, similarity in matches:
                embedding = self.embeddings.get(event_id)
                if embedding:
                    results.append(SimilarityResult(
                        query_event_id=event.get('id', 'unknown'),
                        matched_event_id=event_id,
                        similarity_score=similarity,
                        matched_event_data=embedding.metadata
                    ))
            
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []


class DuplicateDetector:
    """Detect duplicate or very similar events"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize duplicate detector.
        
        Args:
            similarity_threshold: Threshold for duplicate (0-1)
        """
        self.similarity_threshold = similarity_threshold
        self.vector_db = VectorDatabase()
    
    async def check_duplicate(self, event: Dict[str, Any]) -> Tuple[bool, Optional[str], float]:
        """
        Check if event is duplicate.
        
        Args:
            event: Event to check
            
        Returns:
            (is_duplicate, duplicate_event_id, similarity_score)
        """
        try:
            # Find similar events
            similar = await self.vector_db.find_similar_events(event, top_k=1)
            
            if similar and similar[0].similarity_score >= self.similarity_threshold:
                return True, similar[0].matched_event_id, similar[0].similarity_score
            
            return False, None, 0.0
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False, None, 0.0


class ThreatClusterer:
    """Cluster similar threats together"""
    
    def __init__(self, n_clusters: int = 10):
        """
        Initialize threat clusterer.
        
        Args:
            n_clusters: Number of clusters
        """
        self.n_clusters = n_clusters
        self.vector_db = VectorDatabase()
        self.kmeans = None
    
    async def cluster_threats(self, events: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        """
        Cluster events by threat similarity.
        
        Args:
            events: Events to cluster
            
        Returns:
            Dictionary mapping cluster_id to list of event_ids
        """
        try:
            if len(events) < self.n_clusters:
                # Not enough events, return single cluster
                return {0: [e.get('id', f"event_{i}") for i, e in enumerate(events)]}
            
            # Embed all events
            embeddings = await self.vector_db.embedder.embed_batch(events)
            
            # Extract vectors
            vectors = np.array([e.vector for e in embeddings])
            
            # Cluster
            self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
            labels = self.kmeans.fit_predict(vectors)
            
            # Group by cluster
            clusters = {}
            for event_id, label in zip([e.get('id') for e in events], labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(event_id)
            
            logger.info(f"✓ Clustered {len(events)} events into {len(clusters)} clusters")
            return clusters
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return {0: [e.get('id') for e in events]}


class RecommendationEngine:
    """Recommend responses based on similar incidents"""
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.vector_db = VectorDatabase()
        self.response_map = {
            'SSH_BRUTE_FORCE': 'BLOCK_IP_AND_REVIEW_LOGS',
            'WEB_SCAN': 'ISOLATE_WEB_SERVER',
            'DB_PROBE': 'BLOCK_DB_ACCESS',
            'ANOMALY': 'INVESTIGATE_MANUALLY',
            'HONEYPOT_INTERACTION': 'TRACE_ATTACKER',
            'CANARY_TRIGGER': 'ACTIVATE_INCIDENT_RESPONSE'
        }
    
    async def recommend_response(self, event: Dict[str, Any]) -> str:
        """
        Recommend incident response based on similar incidents.
        
        Args:
            event: Current event
            
        Returns:
            Recommended response action
        """
        try:
            # Find similar events
            similar = await self.vector_db.find_similar_events(event, top_k=5)
            
            if similar:
                # Check responses for similar incidents
                event_type = event.get('event_type', 'UNKNOWN')
                return self.response_map.get(event_type, 'INVESTIGATE_MANUALLY')
            
            return 'INVESTIGATE_MANUALLY'
        except Exception as e:
            logger.warning(f"Recommendation failed: {e}")
            return 'INVESTIGATE_MANUALLY'


class VectorSearchEngine:
    """Complete vector search engine"""
    
    def __init__(self):
        """Initialize vector search engine"""
        self.vector_db = VectorDatabase()
        self.duplicate_detector = DuplicateDetector()
        self.threat_clusterer = ThreatClusterer()
        self.recommendation_engine = RecommendationEngine()
    
    async def index_events(self, events: List[Dict[str, Any]]) -> bool:
        """
        Index events in vector database.
        
        Args:
            events: Events to index
            
        Returns:
            Success status
        """
        try:
            embeddings = await self.vector_db.embedder.embed_batch(events)
            count = await self.vector_db.insert_batch(embeddings)
            logger.info(f"✓ Indexed {count} events")
            return count > 0
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            return False


# Global vector search engine instance
vector_search_engine = VectorSearchEngine()
