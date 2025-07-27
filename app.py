import dash
from dash import dcc, html, Input, Output
from dash_auth import BasicAuth
import os
import json
import plotly.graph_objs as go
import pandas as pd
from flask import send_from_directory, abort

# Initialize Dash app
app = dash.Dash(__name__)

# Password protection
auth = BasicAuth(
    app,
    {"guest": "Support bacteria, we need more culture!"}  # Replace with a strong password
)

# List of files in data/
files = [
    {"filename":"Summary_Stats_All_Sporulation_Genes.txt", "display_name": "All Sporulation-Affected Genes"},
    {"filename":"Summary_Stats_Mfd-_Genes.txt", "display_name": "Mfd- Genes"},
    {"filename":"Summary_Stats_YB955_Genes.txt", "display_name": "YB955 Genes"},
    {"filename":"Summary_Stats_Common_Genes_Genes.txt", "display_name": "Common Genes"},
    {"filename":"Summary_Stats_Partial_Threshold_Genes.txt", "display_name": "Partial Threshold Genes"},
    {"filename":"Summary_Stats_Below_Threshold_Genes.txt", "display_name": "Below Threshold Genes"},
    {"filename":"sporulation_CV_statistics.csv", "display_name": "Sporulation CV Statistics"},
    {"filename":"gene_category_summary_table.csv", "display_name": "Summary Table"}
]

# Load Plotly figure from JSON
fig_dict = {}
try:
    with open(os.path.join("data", "all_sporulation_genes_scatter_plot.json"), 'r') as f:
        fig_dict = json.load(f)
except Exception as e:
    print(f"Error loading plot JSON: {e}")

# Read gene count and gene list from sporulation_CV_statistics.csv
gene_count = 0
valid_genes = set()
try:
    df = pd.read_csv(os.path.join("data", "sporulation_CV_statistics.csv"))
    gene_count = len(df["Gene"].unique())
    valid_genes = set(df["Gene"].str.lower())  # List of valid gene names for validation
except Exception as e:
    print(f"Error reading gene count: {e}")

# Define layout with inline CSS
app.layout = html.Div([
    dcc.Markdown("""
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #f8f9fa;
                margin: 20px;
            }
            h1 {
                color: #333;
            }
            h2 {
                color: #555;
                margin-top: 20px;
            }
            .button-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 10px;
            }
            .btn {
                display: block;
                width: 300px;
                margin-top: 10px;
                padding: 8px 12px;
                font-size: 14px;
                cursor: pointer;
                border: none;
                background-color: #007BFF;
                color: white;
                border-radius: 5px;
                text-decoration: none;
                text-align: center;
            }
            .btn:hover {
                background-color: #0056b3;
            }
            .search-container {
                margin-bottom: 20px;
            }
            input[type="text"] {
                padding: 8px;
                font-size: 14px;
                width: 300px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        </style>
    """, dangerously_allow_html=True),
    html.H1("Sporulation Dashboard"),
    html.H2(f"n = {gene_count} genes"),
    html.Div([
        html.Label("Search Genes (comma-separated):"),
        dcc.Input(id="gene-search", type="text", placeholder="e.g., cotC, spo0A", style={"marginLeft": "10px"}),
    ], className="search-container"),
    dcc.Graph(id="scatter-plot", figure=go.Figure(fig_dict)),
    html.H2("Data Files"),
    html.Div([
        html.Div(
#            html.A(file, href=f"/data/{file}", target="_blank", className="btn")
            html.A(file["display_name"], href=f"/data/{file['filename']}", target="_blank", className="btn")
        ) for file in files
    ], className="button-container")
])

# Callback to update plot based on gene search
@app.callback(
    Output("scatter-plot", "figure"),
    Input("gene-search", "value")
)
def update_plot(search_input):
    fig = go.Figure(fig_dict)
    
    if search_input:
        # Split input into list of genes (trim whitespace, convert to lowercase)
        search_genes = [gene.strip().lower() for gene in search_input.split(",") if gene.strip()]
        if search_genes:
            print("Search genes:", search_genes)  # Debug: Log search input
            matched_genes = set()
            for trace in fig.data:
                customdata = trace.customdata
                if customdata is None:
                    continue
                # Create a list of marker sizes, defaulting to original sizes
                sizes = [trace.marker.size] * len(customdata)
                # Highlight points where gene name contains the search term
                for i, data in enumerate(customdata):
                    gene = data[0].lower() if data[0] else ""
                    # Only highlight if the gene name contains the search term and is a valid gene
                    if any(search_gene in gene for search_gene in search_genes) and gene in valid_genes:
                        sizes[i] = trace.marker.size * 2  # Double size for highlight
                        matched_genes.add(gene)
                trace.marker.size = sizes
            print("Matched genes:", matched_genes)  # Debug: Log matched genes
    
    return fig

# Route to serve data files from data/
@app.server.route('/data/<filename>')
def serve_data_file(filename):
    file_path = os.path.join("data", filename)
    if not os.path.exists(file_path):
        abort(404, description=f"File {filename} not found in data/.")
    return send_from_directory("data", filename)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
