# Network Path Analysis Tool

A Python tool for analyzing paths and computing distances between links in water distribution networks using OWA-EPANET.

## Features

- Finds all possible paths between network links
- Computes shortest distances between links
- Generates distance matrices (index-based and ID-based)
- Supports multiple network files
- Automatic file naming and organization

## Installation

```bash
# Clone repository
git clone https://github.com/UrbanLinks/network-path-analysis.git
cd network-path-analysis

# Install requirements
pip install -r requirements.txt
```

## Usage

```python
# Single network analysis
from network_analyzer import analyze_network
analyze_network("net2.inp")

# Multiple networks
input_files = ["net2.inp"]
for input_file in input_files:
    analyze_network(input_file)
```

## Output Files

For each network (e.g., "net2.inp"):
- `paths_net2.json`: All possible paths
- `distance_matrix_index_net2.csv`: Index-based distances
- `distance_matrix_id_net2.csv`: ID-based distances
- `index_to_id_mapping_net2.json`: Index-ID mapping

## Requirements

- Python 3.7+
- OWA-EPANET Toolkit
- numpy
- pandas

## Citation ⚠️

If you use this tool in your work, please cite it as:

```bibtex
@software{nosratihabibi2024network,
  author = {Nosrati Habibi, Morad and Dziedzic, Rebecca},
  title = {Network Path Analysis Tool},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  organization = {Urban Links},
  url = {https://github.com/UrbanLinks/network-path-analysis}
}
```

## License

MIT License - See [LICENSE](LICENSE) file. 
You are free to use and modify this code, just remember to cite!

Copyright (c) 2024 Urban Links
Authors: Morad Nosrati Habibi and Rebecca Dziedzic

## Contact

Urban Links - https://github.com/UrbanLinks
