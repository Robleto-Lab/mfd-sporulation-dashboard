#!/usr/bin/env python3
"""
create_searchable_plot.py
Creates a searchable HTML version of the plot that works in an iframe
"""

import json
import os

def create_searchable_html_plot(json_path, output_path, gene_list_path):
    """
    Create a self-contained HTML file with search functionality
    that can be loaded in an iframe
    """
    
    # Load the plot JSON
    with open(json_path, 'r') as f:
        plot_data = json.load(f)
    
    # Load the gene list
    with open(gene_list_path, 'r') as f:
        gene_data = json.load(f)
    
    # Create the HTML content with embedded search functionality
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Sporulation Plot</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 10px;
            font-family: Arial, sans-serif;
            background: white;
        }}
        .search-container {{
            margin-bottom: 10px;
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        #gene-search {{
            padding: 8px;
            font-size: 14px;
            width: 300px;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-left: 10px;
        }}
        #search-status {{
            margin-top: 5px;
            font-size: 12px;
            color: #666;
            font-style: italic;
        }}
        #plot {{
            width: 100%;
            height: 500px;
        }}
    </style>
</head>
<body>
    <div class="search-container">
        <label for="gene-search">Search Genes (comma-separated):</label>
        <input type="text" id="gene-search" placeholder="e.g., cotC, spo0A">
        <div id="search-status"></div>
    </div>
    <div id="plot"></div>
    
    <script>
        // Embed the plot data
        const originalFigure = {json.dumps(plot_data)};
        
        // Embed the valid genes list
        const validGenes = new Set({json.dumps([g.lower() for g in gene_data['genes']])});
        const geneCount = {gene_data['count']};
        
        // Initialize the plot
        Plotly.newPlot('plot', originalFigure.data, originalFigure.layout);
        
        // Search functionality
        function updatePlot(searchInput) {{
            // Deep clone the original figure data
            const figureData = JSON.parse(JSON.stringify(originalFigure.data));
            const figureLayout = JSON.parse(JSON.stringify(originalFigure.layout));
            
            if (searchInput && searchInput.trim()) {{
                // Parse search input
                const searchGenes = searchInput.split(',')
                    .map(gene => gene.trim().toLowerCase())
                    .filter(gene => gene.length > 0);
                
                if (searchGenes.length > 0) {{
                    console.log('Searching for genes:', searchGenes);
                    const matchedGenes = new Set();
                    let totalMatches = 0;
                    
                    // Process each trace
                    figureData.forEach(trace => {{
                        if (!trace.customdata) return;
                        
                        // Get original properties
                        const originalOpacity = trace.marker.opacity || 1.0;
                        const originalSize = trace.marker.size || 6;
                        const originalHovertemplate = trace.hovertemplate || '';
                        
                        // Create arrays for all points
                        const opacities = [];
                        const sizes = [];
                        const hovertemplates = [];
                        
                        trace.customdata.forEach((data, i) => {{
                            const gene = (data[0] || '').toLowerCase();
                            
                            // Check if gene matches search
                            const isMatch = searchGenes.some(searchGene => gene.includes(searchGene));
                            const isValid = validGenes.has(gene);
                            
                            if (isMatch && isValid) {{
                                opacities.push(originalOpacity);
                                sizes.push(originalSize * 1.5); // Make matching points bigger
                                hovertemplates.push(originalHovertemplate);
                                matchedGenes.add(gene);
                                totalMatches++;
                            }} else {{
                                opacities.push(0); // Hide non-matching points
                                sizes.push(originalSize);
                                hovertemplates.push(''); // Disable hover
                            }}
                        }});
                        
                        // Apply the arrays
                        trace.marker.opacity = opacities;
                        trace.marker.size = sizes;
                        trace.hovertemplate = hovertemplates;
                    }});
                    
                    // Update status
                    const uniqueMatches = matchedGenes.size;
                    document.getElementById('search-status').textContent = 
                        uniqueMatches > 0 
                            ? `Found ${{uniqueMatches}} unique genes (${{totalMatches}} total points)`
                            : 'No matching genes found';
                    
                    // Update title
                    if (uniqueMatches > 0) {{
                        figureLayout.title = `All Sporulation-Affected Genes - Showing ${{uniqueMatches}} matching genes`;
                    }} else {{
                        figureLayout.title = 'All Sporulation-Affected Genes - No matching genes found';
                    }}
                }}
            }} else {{
                // Reset when no search
                document.getElementById('search-status').textContent = '';
                figureLayout.title = 'All Sporulation-Affected Genes';
            }}
            
            // Update the plot
            Plotly.react('plot', figureData, figureLayout);
        }}
        
        // Setup search input with debouncing
        let debounceTimer;
        document.getElementById('gene-search').addEventListener('input', function() {{
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {{
                updatePlot(this.value);
            }}, 300);
        }});
    </script>
</body>
</html>"""
    
    # Write the HTML file
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Created searchable plot: {output_path}")

if __name__ == "__main__":
    # Configure paths
    json_path = "assets/all_sporulation_genes_scatter_plot.json"
    gene_list_path = "data/gene_list.json"
    output_path = "assets/all_sporulation_genes_scatter_plot_searchable.html"
    
    # Check if files exist
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        print("Make sure you've run your script.py to generate the JSON file")
        exit(1)
    
    if not os.path.exists(gene_list_path):
        print(f"Error: {gene_list_path} not found")
        print("Run generate_gene_list_JSON.py first")
        exit(1)
    
    # Create the searchable HTML
    create_searchable_html_plot(json_path, output_path, gene_list_path)
    print("\nYou can now use this file in your iframe:")
    print('  <iframe src="assets/all_sporulation_genes_scatter_plot_searchable.html"></iframe>')
