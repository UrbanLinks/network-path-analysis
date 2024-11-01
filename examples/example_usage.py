from src.network_path_analysis import analyze_network

def main():
    """Example usage of the Network Path Analysis tool."""
    
    # Analyze a single network
    analyze_network("sample_networks/net2.inp")
    
    # Analyze multiple networks
    networks = ["sample_networks/net2.inp", "sample_networks/net3.inp"]
    for network in networks:
        analyze_network(network)

if __name__ == "__main__":
    main()
