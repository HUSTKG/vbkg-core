import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import norm

logger = logging.getLogger(__name__)


class PersonRankCalculator:
    """
    Optimized PersonRank calculator with multiple algorithms and performance optimizations
    """
    
    def __init__(self):
        self.convergence_history = []
    
    def calculate_personrank(
        self,
        graph_structure: Dict[str, List[str]],
        node_degrees: Dict[str, int],
        personalization_vector: Dict[str, float],
        damping_factor: float = 0.85,
        max_iterations: int = 100,
        convergence_threshold: float = 1e-6,
        algorithm: str = "power_iteration"
    ) -> Dict[str, float]:
        """
        Calculate PersonRank scores using specified algorithm
        
        Args:
            graph_structure: Adjacency list representation of graph
            node_degrees: Out-degree of each node
            personalization_vector: Personalization weights for each node
            damping_factor: Random walk vs personalization balance
            max_iterations: Maximum iterations
            convergence_threshold: Convergence tolerance
            algorithm: Algorithm to use ('power_iteration', 'sparse_matrix', 'iterative')
        
        Returns:
            Dictionary mapping node IDs to PersonRank scores
        """
        if not graph_structure:
            return {}
        
        if algorithm == "sparse_matrix":
            return self._sparse_matrix_personrank(
                graph_structure, node_degrees, personalization_vector,
                damping_factor, max_iterations, convergence_threshold
            )
        elif algorithm == "iterative":
            return self._iterative_personrank(
                graph_structure, node_degrees, personalization_vector,
                damping_factor, max_iterations, convergence_threshold
            )
        else:  # default: power_iteration
            return self._power_iteration_personrank(
                graph_structure, node_degrees, personalization_vector,
                damping_factor, max_iterations, convergence_threshold
            )
    
    def _power_iteration_personrank(
        self,
        graph_structure: Dict[str, List[str]],
        node_degrees: Dict[str, int],
        personalization_vector: Dict[str, float],
        damping_factor: float,
        max_iterations: int,
        convergence_threshold: float
    ) -> Dict[str, float]:
        """Power iteration method for PersonRank"""
        
        nodes = list(graph_structure.keys())
        n = len(nodes)
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        
        # Initialize vectors
        scores = np.ones(n) / n
        personalization = np.array([personalization_vector.get(node, 0.0) for node in nodes])
        
        # Normalize personalization vector
        if personalization.sum() > 0:
            personalization = personalization / personalization.sum()
        else:
            personalization = np.ones(n) / n
        
        self.convergence_history = []
        
        for iteration in range(max_iterations):
            new_scores = np.zeros(n)
            
            # Random walk component
            for i, node_id in enumerate(nodes):
                neighbors = graph_structure.get(node_id, [])
                for neighbor_id in neighbors:
                    if neighbor_id in node_to_idx:
                        j = node_to_idx[neighbor_id]
                        neighbor_degree = max(node_degrees.get(neighbor_id, 1), 1)
                        new_scores[i] += damping_factor * scores[j] / neighbor_degree
            
            # Personalization component
            new_scores += (1 - damping_factor) * personalization
            
            # Check convergence
            diff = np.linalg.norm(new_scores - scores, ord=1)
            self.convergence_history.append(diff)
            
            if diff < convergence_threshold:
                logger.info(f"PersonRank converged after {iteration + 1} iterations")
                break
                
            scores = new_scores
        
        return {nodes[i]: float(scores[i]) for i in range(n)}
    
    def _sparse_matrix_personrank(
        self,
        graph_structure: Dict[str, List[str]],
        node_degrees: Dict[str, int],
        personalization_vector: Dict[str, float],
        damping_factor: float,
        max_iterations: int,
        convergence_threshold: float
    ) -> Dict[str, float]:
        """Sparse matrix method for PersonRank (more efficient for large graphs)"""
        
        nodes = list(graph_structure.keys())
        n = len(nodes)
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        
        # Build sparse transition matrix
        row_indices = []
        col_indices = []
        data = []
        
        for node_id, neighbors in graph_structure.items():
            if node_id not in node_to_idx:
                continue
                
            i = node_to_idx[node_id]
            degree = max(node_degrees.get(node_id, 1), 1)
            
            for neighbor_id in neighbors:
                if neighbor_id in node_to_idx:
                    j = node_to_idx[neighbor_id]
                    row_indices.append(j)  # Target node
                    col_indices.append(i)  # Source node
                    data.append(damping_factor / degree)
        
        # Create sparse transition matrix
        transition_matrix = csr_matrix(
            (data, (row_indices, col_indices)), 
            shape=(n, n)
        )
        
        # Personalization vector
        personalization = np.array([personalization_vector.get(node, 0.0) for node in nodes])
        if personalization.sum() > 0:
            personalization = personalization / personalization.sum()
        else:
            personalization = np.ones(n) / n
        
        personalization_term = (1 - damping_factor) * personalization
        
        # Power iteration with sparse matrix
        scores = np.ones(n) / n
        self.convergence_history = []
        
        for iteration in range(max_iterations):
            new_scores = transition_matrix.dot(scores) + personalization_term
            
            # Check convergence
            diff = norm(new_scores - scores, ord=1)
            self.convergence_history.append(diff)
            
            if diff < convergence_threshold:
                logger.info(f"Sparse PersonRank converged after {iteration + 1} iterations")
                break
                
            scores = new_scores
        
        return {nodes[i]: float(scores[i]) for i in range(n)}
    
    def _iterative_personrank(
        self,
        graph_structure: Dict[str, List[str]],
        node_degrees: Dict[str, int],
        personalization_vector: Dict[str, float],
        damping_factor: float,
        max_iterations: int,
        convergence_threshold: float
    ) -> Dict[str, float]:
        """Iterative method with optimized memory usage"""
        
        nodes = list(graph_structure.keys())
        n = len(nodes)
        
        # Use dictionaries for better memory efficiency with sparse graphs
        scores = {node: 1.0 / n for node in nodes}
        personalization = {}
        
        # Normalize personalization
        total_personalization = sum(personalization_vector.values())
        if total_personalization > 0:
            for node in nodes:
                personalization[node] = personalization_vector.get(node, 0.0) / total_personalization
        else:
            for node in nodes:
                personalization[node] = 1.0 / n
        
        self.convergence_history = []
        
        for iteration in range(max_iterations):
            new_scores = {}
            
            # Initialize with personalization component
            for node in nodes:
                new_scores[node] = (1 - damping_factor) * personalization[node]
            
            # Add random walk component
            for node_id, neighbors in graph_structure.items():
                if not neighbors:
                    continue
                    
                degree = max(node_degrees.get(node_id, 1), 1)
                contribution = damping_factor * scores[node_id] / degree
                
                for neighbor_id in neighbors:
                    if neighbor_id in new_scores:
                        new_scores[neighbor_id] += contribution
            
            # Check convergence
            diff = sum(abs(new_scores[node] - scores[node]) for node in nodes)
            self.convergence_history.append(diff)
            
            if diff < convergence_threshold:
                logger.info(f"Iterative PersonRank converged after {iteration + 1} iterations")
                break
                
            scores = new_scores
        
        return scores
    
    def get_convergence_info(self) -> Dict[str, Any]:
        """Get information about the last convergence"""
        if not self.convergence_history:
            return {"status": "No convergence data available"}
        
        return {
            "iterations": len(self.convergence_history),
            "final_difference": self.convergence_history[-1],
            "converged": self.convergence_history[-1] < 1e-6,
            "convergence_rate": self._calculate_convergence_rate(),
            "convergence_history": self.convergence_history[-10:]  # Last 10 iterations
        }
    
    def _calculate_convergence_rate(self) -> float:
        """Calculate the convergence rate"""
        if len(self.convergence_history) < 2:
            return 0.0
        
        # Calculate average rate of convergence
        rates = []
        for i in range(1, len(self.convergence_history)):
            if self.convergence_history[i-1] > 0:
                rate = self.convergence_history[i] / self.convergence_history[i-1]
                rates.append(rate)
        
        return np.mean(rates) if rates else 0.0


class PersonRankAnalyzer:
    """
    Analyzer for PersonRank results and graph properties
    """
    
    @staticmethod
    def analyze_scores(
        scores: Dict[str, float],
        entities_dict: Dict[str, Dict[str, Any]],
        top_k: int = 10
    ) -> Dict[str, Any]:
        """Analyze PersonRank scores and provide insights"""
        
        if not scores:
            return {"error": "No scores to analyze"}
        
        # Sort scores
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Basic statistics
        score_values = list(scores.values())
        stats = {
            "total_nodes": len(scores),
            "mean_score": np.mean(score_values),
            "std_score": np.std(score_values),
            "min_score": min(score_values),
            "max_score": max(score_values),
            "score_range": max(score_values) - min(score_values)
        }
        
        # Top entities
        top_entities = []
        for i, (entity_id, score) in enumerate(sorted_scores[:top_k]):
            entity_info = entities_dict.get(entity_id, {})
            top_entities.append({
                "rank": i + 1,
                "entity_id": entity_id,
                "entity_text": entity_info.get("entity_text", "Unknown"),
                "entity_type": entity_info.get("entity_type", "Unknown"),
                "score": score,
                "score_normalized": score / max(score_values) if max(score_values) > 0 else 0
            })
        
        # Score distribution analysis
        distribution = PersonRankAnalyzer._analyze_score_distribution(score_values)
        
        # Entity type analysis
        type_analysis = PersonRankAnalyzer._analyze_by_entity_type(
            sorted_scores, entities_dict
        )
        
        return {
            "statistics": stats,
            "top_entities": top_entities,
            "score_distribution": distribution,
            "entity_type_analysis": type_analysis,
            "insights": PersonRankAnalyzer._generate_insights(stats, top_entities, type_analysis)
        }
    
    @staticmethod
    def _analyze_score_distribution(scores: List[float]) -> Dict[str, Any]:
        """Analyze the distribution of PersonRank scores"""
        
        # Percentiles
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        percentile_values = {
            f"p{p}": np.percentile(scores, p) for p in percentiles
        }
        
        # Distribution characteristics
        return {
            "percentiles": percentile_values,
            "skewness": float(np.mean([(x - np.mean(scores))**3 for x in scores]) / (np.std(scores)**3)) if np.std(scores) > 0 else 0,
            "concentration": percentile_values["p90"] / percentile_values["p10"] if percentile_values["p10"] > 0 else float('inf'),
            "gini_coefficient": PersonRankAnalyzer._calculate_gini(scores)
        }
    
    @staticmethod
    def _analyze_by_entity_type(
        sorted_scores: List[Tuple[str, float]], 
        entities_dict: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze PersonRank scores by entity type"""
        
        type_scores = {}
        type_counts = {}
        
        for entity_id, score in sorted_scores:
            entity_info = entities_dict.get(entity_id, {})
            entity_type = entity_info.get("entity_type", "Unknown")
            
            if entity_type not in type_scores:
                type_scores[entity_type] = []
                type_counts[entity_type] = 0
            
            type_scores[entity_type].append(score)
            type_counts[entity_type] += 1
        
        type_analysis = {}
        for entity_type, scores in type_scores.items():
            type_analysis[entity_type] = {
                "count": type_counts[entity_type],
                "mean_score": np.mean(scores),
                "max_score": max(scores),
                "std_score": np.std(scores),
                "top_entities_percentage": len([s for s in scores if s > np.percentile(list(dict(sorted_scores).values()), 90)]) / len(scores) * 100
            }
        
        return type_analysis
    
    @staticmethod
    def _calculate_gini(scores: List[float]) -> float:
        """Calculate Gini coefficient for score inequality"""
        if len(scores) == 0:
            return 0.0
        
        # Sort scores
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        
        # Calculate Gini coefficient
        cumsum = np.cumsum(sorted_scores)
        return (2 * np.sum(np.arange(1, n + 1) * sorted_scores)) / (n * cumsum[-1]) - (n + 1) / n if cumsum[-1] > 0 else 0.0
    
    @staticmethod
    def _generate_insights(
        stats: Dict[str, Any], 
        top_entities: List[Dict[str, Any]], 
        type_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate human-readable insights from PersonRank analysis"""
        
        insights = []
        
        # Score concentration insight
        if stats["score_range"] > stats["mean_score"] * 2:
            insights.append("High score variance indicates some entities are significantly more important than others")
        else:
            insights.append("Scores are relatively evenly distributed across entities")
        
        # Top entity insight
        if len(top_entities) > 0:
            top_entity = top_entities[0]
            if top_entity["score_normalized"] > 0.5:
                insights.append(f"'{top_entity['entity_text']}' is a dominant entity with very high importance")
            else:
                insights.append(f"'{top_entity['entity_text']}' is the most important entity but importance is distributed")
        
        # Entity type insights
        if type_analysis:
            # Find entity type with highest average score
            best_type = max(type_analysis.items(), key=lambda x: x[1]["mean_score"])
            insights.append(f"'{best_type[0]}' entities have the highest average importance scores")
            
            # Find most represented type in top entities
            type_top_representation = {t: info["top_entities_percentage"] for t, info in type_analysis.items()}
            most_represented = max(type_top_representation.items(), key=lambda x: x[1])
            if most_represented[1] > 20:
                insights.append(f"'{most_represented[0]}' entities are over-represented in top-ranking entities")
        
        return insights


# Utility functions for graph analysis
def calculate_graph_metrics(graph_structure: Dict[str, List[str]]) -> Dict[str, Any]:
    """Calculate basic graph metrics"""
    
    nodes = set(graph_structure.keys())
    edges = 0
    in_degrees = {}
    out_degrees = {}
    
    # Calculate degrees
    for node, neighbors in graph_structure.items():
        out_degrees[node] = len(neighbors)
        edges += len(neighbors)
        
        for neighbor in neighbors:
            nodes.add(neighbor)
            in_degrees[neighbor] = in_degrees.get(neighbor, 0) + 1
    
    # Ensure all nodes have degree entries
    for node in nodes:
        if node not in in_degrees:
            in_degrees[node] = 0
        if node not in out_degrees:
            out_degrees[node] = 0
    
    # Calculate metrics
    degree_values = list(out_degrees.values())
    
    return {
        "node_count": len(nodes),
        "edge_count": edges,
        "average_degree": np.mean(degree_values) if degree_values else 0,
        "max_degree": max(degree_values) if degree_values else 0,
        "min_degree": min(degree_values) if degree_values else 0,
        "density": edges / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0,
        "degree_distribution": {
            "mean": np.mean(degree_values) if degree_values else 0,
            "std": np.std(degree_values) if degree_values else 0,
            "p90": np.percentile(degree_values, 90) if degree_values else 0
        }
    }


def optimize_personalization_vector(
    query_embedding: List[float],
    entities_dict: Dict[str, Dict[str, Any]],
    similarity_weight: float = 0.7,
    confidence_weight: float = 0.3
) -> Dict[str, float]:
    """
    Create optimized personalization vector combining similarity and entity confidence
    """
    personalization = {}
    
    for entity_id, entity_info in entities_dict.items():
        # Get similarity score
        similarity = entity_info.get("similarity_score", 0.0)
        
        # Get entity confidence
        confidence = entity_info.get("confidence", 0.5)
        
        # Combine scores
        personalization[entity_id] = (similarity_weight * similarity + 
                                    confidence_weight * confidence)
    
    # Normalize
    total = sum(personalization.values())
    if total > 0:
        personalization = {k: v / total for k, v in personalization.items()}
    
    return personalization
