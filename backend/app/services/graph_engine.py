"""
Graph-Based Incident Correlation Engine.
Maps relationships between events, incidents, and attack patterns.

Features:
1. Attack Path Visualization
2. Relationship Mapping (attacker → target → impact)
3. Kill Chain Analysis (MITRE ATT&CK framework)
4. Lateral Movement Detection
5. Root Cause Analysis
6. Incident Correlation
7. Centrality Analysis (identify critical nodes)
"""

import logging
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class RelationType(str, Enum):
    """Types of relationships in attack graph"""
    EXPLOITS = "EXPLOITS"  # Attacker → Vulnerable system
    MOVES_LATERALLY_TO = "MOVES_LATERALLY_TO"  # System A → System B
    COMMUNICATES_WITH = "COMMUNICATES_WITH"  # IP → IP
    COMPROMISES = "COMPROMISES"  # Attacker → Account
    ESCALATES_TO = "ESCALATES_TO"  # User → Admin
    EXFILTRATES_FROM = "EXFILTRATES_FROM"  # System → External IP
    TRIGGERS = "TRIGGERS"  # Event → Incident
    CORRELATES_WITH = "CORRELATES_WITH"  # Incident → Incident


@dataclass
class GraphNode:
    """Node in attack graph"""
    node_id: str
    node_type: str  # ip, user, system, account, incident
    label: str
    properties: Dict[str, Any]
    timestamp: datetime
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    risk_score: int  # 0-100


@dataclass
class GraphEdge:
    """Edge (relationship) in attack graph"""
    edge_id: str
    source_id: str
    target_id: str
    relationship_type: RelationType
    weight: float  # 0-1, confidence
    properties: Dict[str, Any]
    timestamp: datetime
    event_count: int  # Number of events supporting this edge


@dataclass
class AttackPath:
    """Detected attack path or chain"""
    path_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    attack_type: str  # RECONNAISSANCE, EXPLOITATION, LATERAL_MOVEMENT, etc.
    confidence: float  # 0-1
    total_risk_score: int  # Sum of node risks
    mitre_techniques: List[str]  # MITRE ATT&CK techniques


@dataclass
class IncidentCorrelation:
    """Correlation between multiple incidents"""
    correlation_id: str
    incident_ids: List[str]
    common_attacker: Optional[str]
    common_target: Optional[str]
    common_timeframe: Tuple[datetime, datetime]
    correlation_strength: float  # 0-1
    likely_attack_type: str


class GraphNode:
    """Represents a node in the attack graph"""
    
    def __init__(self, node_id: str, node_type: str, label: str):
        self.node_id = node_id
        self.node_type = node_type  # ip, user, system, incident
        self.label = label
        self.properties = {}
        self.timestamp = datetime.now()
        self.edges_in = []  # Incoming edges
        self.edges_out = []  # Outgoing edges
        self.severity = 'LOW'
        self.risk_score = 0


class AttackGraph:
    """Attack graph representation and analysis"""
    
    def __init__(self):
        """Initialize attack graph"""
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[Dict[str, Any]] = []
        self.node_counter = 0
        self.edge_counter = 0
    
    def add_node(self, node_id: str, node_type: str, label: str,
                properties: Optional[Dict[str, Any]] = None) -> GraphNode:
        """
        Add node to graph.
        
        Args:
            node_id: Unique node identifier
            node_type: Type of node (ip, user, system, incident)
            label: Human-readable label
            properties: Optional properties dictionary
            
        Returns:
            GraphNode object
        """
        if node_id not in self.nodes:
            node = GraphNode(node_id, node_type, label)
            if properties:
                node.properties = properties
            self.nodes[node_id] = node
            logger.debug(f"Added node: {node_id}")
        
        return self.nodes[node_id]
    
    def add_edge(self, source_id: str, target_id: str, 
                relationship_type: RelationType,
                weight: float = 0.5,
                properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add edge (relationship) to graph.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship_type: Type of relationship
            weight: Confidence weight (0-1)
            properties: Optional properties
            
        Returns:
            Success status
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot add edge: nodes not found")
            return False
        
        edge = {
            'edge_id': f"edge_{self.edge_counter}",
            'source': source_id,
            'target': target_id,
            'type': relationship_type,
            'weight': weight,
            'properties': properties or {},
            'timestamp': datetime.now(),
            'event_count': 1
        }
        
        self.edges.append(edge)
        self.edge_counter += 1
        
        # Update node references
        self.nodes[source_id].edges_out.append(edge)
        self.nodes[target_id].edges_in.append(edge)
        
        logger.debug(f"Added edge: {source_id} → {target_id} ({relationship_type})")
        return True
    
    async def find_attack_paths(self, start_node_id: str, 
                               max_depth: int = 5) -> List[AttackPath]:
        """
        Find attack paths from a starting node (attacker).
        
        Args:
            start_node_id: Starting node (usually attacker IP)
            max_depth: Maximum path depth
            
        Returns:
            List of detected attack paths
        """
        paths = []
        
        def dfs(node_id: str, current_path: List[str], depth: int):
            """Depth-first search for paths"""
            if depth == 0:
                return
            
            node = self.nodes.get(node_id)
            if not node:
                return
            
            for edge in node.edges_out:
                next_node_id = edge['target']
                
                if next_node_id not in current_path:
                    new_path = current_path + [next_node_id]
                    
                    # Path found
                    path_nodes = [self.nodes[nid] for nid in new_path if nid in self.nodes]
                    path_edges = self._get_path_edges(new_path)
                    
                    if path_nodes and path_edges:
                        attack_path = AttackPath(
                            path_id=f"path_{len(paths)}",
                            nodes=path_nodes,
                            edges=path_edges,
                            attack_type=self._classify_attack(path_edges),
                            confidence=self._calculate_path_confidence(path_edges),
                            total_risk_score=sum(n.risk_score for n in path_nodes),
                            mitre_techniques=self._map_mitre_techniques(path_edges)
                        )
                        paths.append(attack_path)
                    
                    # Continue DFS
                    dfs(next_node_id, new_path, depth - 1)
        
        dfs(start_node_id, [start_node_id], max_depth)
        return paths
    
    async def find_lateral_movement(self) -> List[Dict[str, Any]]:
        """
        Detect lateral movement patterns (system-to-system).
        
        Returns:
            List of lateral movement patterns
        """
        lateral_movements = []
        
        for edge in self.edges:
            # Lateral movement: one system communicates with another
            if edge['type'] == RelationType.MOVES_LATERALLY_TO:
                source_node = self.nodes.get(edge['source'])
                target_node = self.nodes.get(edge['target'])
                
                if source_node and target_node:
                    lateral_movements.append({
                        'from_ip': source_node.label,
                        'to_ip': target_node.label,
                        'relationship': edge['type'],
                        'weight': edge['weight'],
                        'events': edge['event_count'],
                        'timestamp': edge['timestamp']
                    })
        
        return lateral_movements
    
    async def find_root_cause(self, incident_id: str) -> Optional[str]:
        """
        Trace back to root cause of incident.
        
        Args:
            incident_id: Incident node ID
            
        Returns:
            Root cause node ID or None
        """
        incident_node = self.nodes.get(incident_id)
        if not incident_node:
            return None
        
        # Trace backward using incoming edges
        current = incident_id
        visited = set()
        
        while current and current not in visited:
            visited.add(current)
            current_node = self.nodes.get(current)
            
            if not current_node or not current_node.edges_in:
                break
            
            # Follow the edge with highest weight (most confident)
            incoming = current_node.edges_in
            best_edge = max(incoming, key=lambda e: e['weight'])
            current = best_edge['source']
        
        return current if current and current != incident_id else None
    
    def _get_path_edges(self, path_nodes: List[str]) -> List[Dict[str, Any]]:
        """Get edges connecting path nodes"""
        path_edges = []
        for i in range(len(path_nodes) - 1):
            for edge in self.edges:
                if edge['source'] == path_nodes[i] and edge['target'] == path_nodes[i + 1]:
                    path_edges.append(edge)
                    break
        return path_edges
    
    def _classify_attack(self, edges: List[Dict[str, Any]]) -> str:
        """Classify attack type from edge sequence"""
        if not edges:
            return 'UNKNOWN'
        
        edge_types = [e['type'] for e in edges]
        
        if RelationType.EXPLOITS in edge_types:
            return 'EXPLOITATION'
        elif RelationType.MOVES_LATERALLY_TO in edge_types:
            return 'LATERAL_MOVEMENT'
        elif RelationType.EXFILTRATES_FROM in edge_types:
            return 'EXFILTRATION'
        elif RelationType.ESCALATES_TO in edge_types:
            return 'PRIVILEGE_ESCALATION'
        
        return 'MULTI_STAGE'
    
    def _calculate_path_confidence(self, edges: List[Dict[str, Any]]) -> float:
        """Calculate confidence of attack path"""
        if not edges:
            return 0.0
        return sum(e['weight'] for e in edges) / len(edges)
    
    def _map_mitre_techniques(self, edges: List[Dict[str, Any]]) -> List[str]:
        """Map attack path to MITRE ATT&CK techniques"""
        techniques = []
        
        for edge in edges:
            rel_type = edge['type']
            
            if rel_type == RelationType.EXPLOITS:
                techniques.append('T1190: Exploit Public-Facing Application')
            elif rel_type == RelationType.MOVES_LATERALLY_TO:
                techniques.append('T1210: Exploitation of Remote Services')
            elif rel_type == RelationType.ESCALATES_TO:
                techniques.append('T1548: Abuse Elevation Control Mechanism')
            elif rel_type == RelationType.EXFILTRATES_FROM:
                techniques.append('T1041: Exfiltration Over C2 Channel')
        
        return list(set(techniques))
    
    async def calculate_node_importance(self) -> Dict[str, float]:
        """
        Calculate importance of each node (centrality).
        
        Returns:
            Dictionary mapping node_id to importance score (0-1)
        """
        importance = {}
        
        for node_id in self.nodes:
            # In-degree + out-degree normalized
            in_degree = len(self.nodes[node_id].edges_in)
            out_degree = len(self.nodes[node_id].edges_out)
            total_degree = in_degree + out_degree
            
            max_degree = len(self.nodes)
            normalized_importance = total_degree / max_degree if max_degree > 0 else 0
            
            importance[node_id] = min(1.0, normalized_importance)
        
        return importance


class IncidentCorrelationEngine:
    """Correlate multiple incidents into attack campaigns"""
    
    def __init__(self):
        """Initialize correlation engine"""
        self.attack_graph = AttackGraph()
    
    async def build_graph_from_events(self, events: List[Dict[str, Any]]) -> AttackGraph:
        """
        Build attack graph from events.
        
        Args:
            events: List of events
            
        Returns:
            Populated AttackGraph
        """
        try:
            # Add nodes
            seen_ips = set()
            seen_users = set()
            
            for event in events:
                source_ip = event.get('source_ip')
                dest_ip = event.get('destination_ip')
                user = event.get('user')
                event_type = event.get('event_type')
                
                # Source IP node
                if source_ip and source_ip not in seen_ips:
                    self.attack_graph.add_node(f"ip_{source_ip}", "ip", source_ip,
                                              {'threat_level': event.get('severity', 'LOW')})
                    seen_ips.add(source_ip)
                
                # Destination IP node
                if dest_ip and dest_ip not in seen_ips:
                    self.attack_graph.add_node(f"ip_{dest_ip}", "ip", dest_ip,
                                              {'is_target': True})
                    seen_ips.add(dest_ip)
                
                # User node
                if user and user not in seen_users:
                    self.attack_graph.add_node(f"user_{user}", "user", user)
                    seen_users.add(user)
            
            # Add edges based on event patterns
            for event in events:
                source_ip = event.get('source_ip')
                dest_ip = event.get('destination_ip')
                event_type = event.get('event_type')
                
                if source_ip and dest_ip:
                    # Determine relationship type
                    if event_type == 'WEB_SCAN':
                        rel_type = RelationType.EXPLOITS
                    elif event_type == 'LATERAL_MOVEMENT':
                        rel_type = RelationType.MOVES_LATERALLY_TO
                    else:
                        rel_type = RelationType.COMMUNICATES_WITH
                    
                    self.attack_graph.add_edge(
                        f"ip_{source_ip}",
                        f"ip_{dest_ip}",
                        rel_type,
                        weight=0.7
                    )
            
            logger.info(f"✓ Attack graph built: {len(self.attack_graph.nodes)} nodes, {len(self.attack_graph.edges)} edges")
            return self.attack_graph
        except Exception as e:
            logger.error(f"Graph building failed: {e}")
            return self.attack_graph
    
    async def correlate_incidents(self, incidents: List[Dict[str, Any]]) -> List[IncidentCorrelation]:
        """
        Correlate multiple incidents.
        
        Args:
            incidents: List of incidents
            
        Returns:
            List of incident correlations
        """
        correlations = []
        
        try:
            for i, incident1 in enumerate(incidents):
                for incident2 in incidents[i + 1:]:
                    # Check if incidents share common attacker
                    attacker1 = incident1.get('source_ip')
                    attacker2 = incident2.get('source_ip')
                    
                    # Check if incidents share common target
                    target1 = incident1.get('destination_ip')
                    target2 = incident2.get('destination_ip')
                    
                    # Check if incidents are close in time
                    time1 = incident1.get('timestamp')
                    time2 = incident2.get('timestamp')
                    
                    common_attacker = attacker1 == attacker2
                    common_target = target1 == target2
                    close_time = abs((time1 - time2).total_seconds()) < 3600 if time1 and time2 else False
                    
                    correlation_strength = sum([common_attacker, common_target, close_time]) / 3
                    
                    if correlation_strength > 0.4:
                        correlations.append(IncidentCorrelation(
                            correlation_id=f"corr_{i}_{j}",
                            incident_ids=[incident1.get('id'), incident2.get('id')],
                            common_attacker=attacker1 if common_attacker else None,
                            common_target=target1 if common_target else None,
                            common_timeframe=(time1, time2) if time1 and time2 else (None, None),
                            correlation_strength=correlation_strength,
                            likely_attack_type='COORDINATED_CAMPAIGN' if correlation_strength > 0.7 else 'RELATED'
                        ))
        
        except Exception as e:
            logger.error(f"Incident correlation failed: {e}")
        
        return correlations


# Global correlation engine instance
correlation_engine = IncidentCorrelationEngine()
