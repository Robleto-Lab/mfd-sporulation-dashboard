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
                font-family: 'Roboto', Arial, sans-serif;
                background-color: #f4f6f9;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background-color: #fff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #1a3c6d;
                font-size: 32px;
                margin-bottom: 10px;
                font-weight: 700;
                text-align: center;
            }
            h2 {
                color: #2a5d9b;
                font-size: 24px;
                margin-top: 30px;
                margin-bottom: 15px;
                font-weight: 600;
                text-align: center;
            }
            .search-container {
                margin: 20px 0;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 10px;
            }
            input[type="text"] {
                padding: 10px;
                font-size: 16px;
                width: 350px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                outline: none;
                transition: border-color 0.2s;
            }
            input[type="text"]:focus {
                border-color: #1a3c6d;
            }
            label {
                font-size: 16px;
                color: #4b5e7e;
            }
            .button-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 12px;
                margin: 20px 0;
            }
            .btn {
                display: block;
                width: 350px;
                padding: 12px;
                font-size: 16px;
                cursor: pointer;
                border: none;
                background-color: #1a3c6d;
                color: white;
                border-radius: 6px;
                text-decoration: none;
                text-align: center;
                transition: background-color 0.2s;
            }
            .btn:hover {
                background-color: #153057;
            }
            .citation-container {
                margin-top: 30px;
                background-color: #e5e7eb;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                border: 1px solid #d1d5db;
                text-align: left;
                max-width: 700px;
                margin-left: auto;
                margin-right: auto;
            }
            .citation-container p {
                font-size: 14px;
                line-height: 1.7;
                color: #374151;
            }
            .citation-container a {
                color: #1a3c6d;
                text-decoration: none;
            }
            .citation-container a:hover {
                text-decoration: underline;
            }
            @media (max-width: 600px) {
                .container {
                    padding: 15px;
                }
                input[type="text"], .btn {
                    width: 100%;
                    max-width: 300px;
                }
            }
        </style>
    """, dangerously_allow_html=True),
html.Div([
    html.H1("Sporulation Dashboard"),
    html.H2(f"n = {gene_count} genes"),
    html.Div([
        html.Label("Search Genes (comma-separated):"),
        dcc.Input(id="gene-search", type="text", placeholder="e.g., cotC, spo0A"),
    ], className="search-container"),
    dcc.Graph(id="scatter-plot", figure=go.Figure(fig_dict)),
    html.H2("Data Files"),
    html.Div([
        html.Div(
#            html.A(file, href=f"/data/{file}", target="_blank", className="btn")
            html.A(file["display_name"], href=f"/data/{file['filename']}", target="_blank", className="btn")
        ) for file in files
    ], className="button-container"),
    html.H2("Citation"),
    html.Div([
        dcc.Markdown("""
            If you use this dashboard, please cite the following papers:

            - Perez RK, Chavez Rios JS, Grifaldo J, Regner K, Pedraza-Reyes M, Robleto EA. 2024. "Draft genome of Bacillus subtilis strain YB955, prophage-cured derivative of strain 168." *Microbiol Resour Announc* 13:e00263-24. [https://doi.org/10.1128/mra.00263-24](https://doi.org/10.1128/mra.00263-24)

            - Martin HA, Sundararajan A, Ermi TS, Heron R, Gonzales J, Lee K, Anguiano-Mendez D, Schilkey F, Pedraza-Reyes M, Robleto EA. 2021. "Mfd Affects Global Transcription and the Physiology of Stressed Bacillus subtilis Cells." *Front Microbiol* 12:625705. doi: [10.3389/fmicb.2021.625705](https://doi.org/10.3389/fmicb.2021.625705). PMID: 33603726; PMCID: PMC7885715.
        """, className="citation-container")
    ])
  ], className="container")
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
