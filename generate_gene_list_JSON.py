#!/usr/bin/env python3
"""
Generate gene_list.json from sporulation_CV_statistics.csv
This file is needed for the client-side search validation in the GitHub Pages version
"""

import pandas as pd
import json
import os

# Configuration - adjust path as needed
data_dir = "data"  # Path to your data directory
csv_file = os.path.join(data_dir, "sporulation_CV_statistics.csv")
output_file = os.path.join(data_dir, "gene_list.json")

try:
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Get unique genes
    unique_genes = df["Gene"].unique().tolist()
    gene_count = len(unique_genes)
    
    # Create the JSON structure
    gene_data = {
        "count": gene_count,
        "genes": sorted(unique_genes)  # Sort for consistency
    }
    
    # Save to JSON file
    with open(output_file, 'w') as f:
        json.dump(gene_data, f, indent=2)
    
    print(f"Successfully created {output_file}")
    print(f"Total genes: {gene_count}")
    print(f"First 10 genes: {sorted(unique_genes)[:10]}")
    
except FileNotFoundError:
    print(f"Error: Could not find {csv_file}")
    print("Make sure the CSV file exists in the data directory")
    
except Exception as e:
    print(f"Error: {e}")
    print("Creating a minimal gene_list.json file...")
    
    # Create a minimal file so the dashboard still works
    minimal_data = {
        "count": 0,
        "genes": []
    }
    
    os.makedirs(data_dir, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(minimal_data, f, indent=2)
    
    print(f"Created minimal {output_file} - search will work but without validation")
