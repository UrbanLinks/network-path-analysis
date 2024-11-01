import epanet.toolkit as en
import numpy as np
import pandas as pd
from itertools import permutations
import json
import re
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

@dataclass
class NetworkLink:
    """Represents a link in the network with its properties."""
    id: str
    start_node: str
    end_node: str
    length: float

class NetworkAnalyzer:
    """Class to analyze network topology and compute distances between links."""
    
    def __init__(self, input_file: str):
        """Initialize the network analyzer with an input file."""
        self.project = en.createproject()
        self.input_file = input_file
        self.network_name = os.path.splitext(os.path.basename(input_file))[0]
        self.links: Dict[str, NetworkLink] = {}
        self.paths: Dict[Tuple[str, str], List[List[str]]] = {}
        self.distances: Dict[Tuple[str, str], float] = {}
        self.link_indices: Dict[int, str] = {}  # Maps indices to link IDs
        
    def __enter__(self):
        """Context manager entry point."""
        en.open(self.project, self.input_file, "", "")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        en.deleteproject(self.project)
    
    def get_output_filename(self, prefix: str, extension: str) -> str:
        """Generate output filename based on input filename."""
        return f"{prefix}_{self.network_name}.{extension}"
    
    def load_network(self) -> None:
        """Load network data from the EPANET file."""
        num_links = en.getcount(self.project, en.LINKCOUNT)
        
        for link_index in range(1, num_links + 1):
            # Get link properties
            link_id = en.getlinkid(self.project, link_index)
            self.link_indices[link_index] = link_id  # Store index to ID mapping
            
            start_node, end_node = en.getlinknodes(self.project, link_index)
            start_node_id = en.getnodeid(self.project, start_node)
            end_node_id = en.getnodeid(self.project, end_node)
            length = en.getlinkvalue(self.project, link_index, en.LENGTH)
            
            # Create NetworkLink object
            self.links[link_id] = NetworkLink(
                id=link_id,
                start_node=start_node_id,
                end_node=end_node_id,
                length=length
            )
    
    def _build_graph(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build a bidirectional graph from the network links."""
        graph = {}
        for link in self.links.values():
            # Add forward direction
            if link.start_node not in graph:
                graph[link.start_node] = []
            graph[link.start_node].append((link.end_node, link.id))
            
            # Add reverse direction
            if link.end_node not in graph:
                graph[link.end_node] = []
            graph[link.end_node].append((link.start_node, link.id))
        return graph
    
    def find_all_paths(self) -> None:
        """Find all possible paths between each pair of links."""
        graph = self._build_graph()
        
        def bfs_paths(start_link: str, end_link: str) -> List[List[str]]:
            """Find all paths between two links using BFS."""
            start_link_data = self.links[start_link]
            queue = [(start_link_data.start_node, [start_link]),
                    (start_link_data.end_node, [start_link])]
            visited = set()
            paths = []
            
            while queue:
                current_node, path = queue.pop(0)
                if path[-1] == end_link:
                    paths.append(path)
                    continue
                    
                for neighbor, next_link in graph.get(current_node, []):
                    if next_link not in path and (current_node, neighbor) not in visited:
                        queue.append((neighbor, path + [next_link]))
                        visited.add((current_node, neighbor))
            
            return paths
        
        # Find paths for all link combinations
        for start_link, end_link in permutations(self.links.keys(), 2):
            self.paths[(start_link, end_link)] = bfs_paths(start_link, end_link)
    
    def compute_path_distance(self, path: List[str]) -> float:
        """Compute the distance of a path considering link lengths."""
        if not path:
            return 0.0
        
        total_length = sum(self.links[link].length for link in path)
        # Adjust for the midpoints of first and last links
        total_length -= (self.links[path[0]].length / 2 + 
                        self.links[path[-1]].length / 2)
        return total_length
    
    def compute_shortest_distances(self) -> None:
        """Compute the shortest distance between all pairs of links."""
        for link_pair, paths in self.paths.items():
            if paths:  # Only compute if paths exist
                distances = [self.compute_path_distance(path) for path in paths]
                self.distances[link_pair] = min(distances)
    
    def create_distance_matrices(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create two distance matrices:
        1. Index-based matrix (0-based indices)
        2. ID-based matrix (using link IDs)
        """
        # Create ID-based matrix
        unique_links = sorted(self.links.keys(), 
                            key=lambda x: [int(t) if t.isdigit() else t.lower() 
                                         for t in re.split('([0-9]+)', x)])
        id_matrix = pd.DataFrame(0.0, index=unique_links, columns=unique_links)
        
        # Fill the ID-based matrix
        for (link1, link2), distance in self.distances.items():
            id_matrix.at[link1, link2] = distance
            id_matrix.at[link2, link1] = distance
        
        # Create index-based matrix
        num_links = len(unique_links)
        index_matrix = pd.DataFrame(0.0, 
                                  index=range(num_links), 
                                  columns=range(num_links))
        
        # Map IDs to indices and fill the index-based matrix
        id_to_index = {link_id: idx for idx, link_id in enumerate(unique_links)}
        for (link1, link2), distance in self.distances.items():
            idx1, idx2 = id_to_index[link1], id_to_index[link2]
            index_matrix.at[idx1, idx2] = distance
            index_matrix.at[idx2, idx1] = distance
        
        return index_matrix, id_matrix
    
    def save_paths(self) -> None:
        """Save computed paths to a JSON file."""
        filename = self.get_output_filename("paths", "json")
        string_keys_paths = {f"{key[0]},{key[1]}": value 
                           for key, value in self.paths.items()}
        with open(filename, 'w') as file:
            json.dump(string_keys_paths, file, indent=4)
        print(f"Paths saved to {filename}")
    
    def load_paths(self) -> None:
        """Load paths from a JSON file."""
        filename = self.get_output_filename("paths", "json")
        with open(filename, 'r') as file:
            string_keys_paths = json.load(file)
        self.paths = {tuple(key.split(',')): value 
                     for key, value in string_keys_paths.items()}
        print(f"Paths loaded from {filename}")
    
    def save_distance_matrices(self, index_matrix: pd.DataFrame, id_matrix: pd.DataFrame) -> None:
        """Save both index-based and ID-based distance matrices."""
        # Save index-based matrix
        index_filename = self.get_output_filename("distance_matrix_index", "csv")
        index_matrix.to_csv(index_filename)
        print(f"Index-based distance matrix saved to {index_filename}")
        
        # Save ID-based matrix
        id_filename = self.get_output_filename("distance_matrix_id", "csv")
        id_matrix.to_csv(id_filename)
        print(f"ID-based distance matrix saved to {id_filename}")
        
        # Save index to ID mapping
        mapping_filename = self.get_output_filename("index_to_id_mapping", "json")
        index_to_id = {str(idx): id_matrix.index[idx] for idx in range(len(id_matrix))}
        with open(mapping_filename, 'w') as f:
            json.dump(index_to_id, f, indent=4)
        print(f"Index to ID mapping saved to {mapping_filename}")

def analyze_network(input_file: str) -> None:
    """Analyze a network file and save results."""
    print(f"\nAnalyzing network: {input_file}")
    
    with NetworkAnalyzer(input_file) as analyzer:
        # Load and analyze network
        analyzer.load_network()
        print("Network loaded successfully")
        
        analyzer.find_all_paths()
        print("All paths computed")
        
        # Save paths
        analyzer.save_paths()
        
        # Compute and save distances with both matrices
        analyzer.compute_shortest_distances()
        index_matrix, id_matrix = analyzer.create_distance_matrices()
        analyzer.save_distance_matrices(index_matrix, id_matrix)
        
        print("Analysis completed")

def main():
    """Main function to demonstrate usage."""
    # Example usage with multiple input files
    input_files = ["net2.inp"]  # Add your input files here
    
    for input_file in input_files:
        try:
            analyze_network(input_file)
            print(f"Successfully processed {input_file}\n")
        except Exception as e:
            print(f"Error processing {input_file}: {e}\n")

if __name__ == "__main__":
    main()
