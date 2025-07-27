import pandas as pd
import numpy as np
import glob
import os
import plotly.express as px
import sys
import json
from datetime import datetime

# Configuration
file_path = "/home/perezthedev/Documents/Robleto_Lab/YB955_Genomics/sporulation_analysis/spor_output_genes/*.csv"
base_output_dir = os.path.expanduser("~/Documents/Robleto_Lab/YB955_Genomics/sporulation_analysis/dash_board_search")
data_output_dir = os.path.join(base_output_dir, "data")
assets_output_dir = os.path.join(base_output_dir, "assets")

# Threshold constants
CV_THRESHOLD = 0.3
RANGE_THRESHOLD = 1000

# Create output directories if they don't exist
os.makedirs(data_output_dir, exist_ok=True)
os.makedirs(assets_output_dir, exist_ok=True)
print(f"Data output directory: {data_output_dir}")
print(f"Assets output directory: {assets_output_dir}")

def process_files_with_error_handling(file_path, data_output_dir):
    """Process CSV files with error handling and return combined statistics DataFrame"""
    files = sorted(glob.glob(file_path))
    all_data = []
    individual_summaries = []

    for file in files:
        print(f"Processing: {file}")
        gene_name = file.split('/')[-1].replace('.csv', '')

        try:
            # Read CSV file
            data = pd.read_csv(file, skiprows=1, header=None)

            # Extract count data columns
            count_columns = data.iloc[:, 2::3]
            count_columns.columns = ["M1", "M2", "M3", "Y1", "Y2", "Y3"]

            # Convert all values to numeric (force non-numeric to NaN)
            count_columns = count_columns.apply(pd.to_numeric, errors='coerce')

            # Check for NaN values (problematic entries)
            if count_columns.isna().sum().sum() > 0:
                print(f"WARNING: Missing or non-numeric values found in {file}")
                print(count_columns[count_columns.isna().any(axis=1)])

            # Compute statistics
            stats = pd.DataFrame({
                "Sample": count_columns.columns,
                "Mean": count_columns.mean().values,
                "SD": count_columns.std().values,
                "CV": (count_columns.std() / count_columns.mean()).values,
                "Range": (count_columns.max() - count_columns.min()).values
            })

            # Add Gene column
            stats.insert(0, "Gene", gene_name)
            all_data.append(stats)

            # Store individual summary for text file
            individual_summary = f"File: {gene_name}.csv\nSummary Statistics for {gene_name}.csv:\n"
            individual_summary += stats.set_index('Sample')[['Mean', 'SD', 'CV', 'Range']].to_string()
            individual_summary += "\n\n"
            individual_summaries.append(individual_summary)

        except Exception as e:
            print(f"ERROR in file: {file} - {e}")
            print(f"Problematic Data in {file}:")
            try:
                data = pd.read_csv(file, skiprows=1, header=None)
                print(data.head(10))
            except:
                print("Could not read file for error display")

    # Save individual gene summaries to text file
    if individual_summaries:
        with open(os.path.join(data_output_dir, "individual_gene_summaries.txt"), 'w') as f:
            f.writelines(individual_summaries)

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def process_dataframe_with_colors(df):
    """Apply color coding based on thresholds"""
    df["Color"] = "gray"  # Default color (Below threshold)

    i = 0
    while i < len(df):
        gene = df.iloc[i]["Gene"]
        m_samples = df.iloc[i:i+3]  # M1, M2, M3
        y_samples = df.iloc[i+3:i+6]  # Y1, Y2, Y3

        # Check thresholds for M-samples
        meets_range_m = m_samples["Range"] >= RANGE_THRESHOLD
        meets_cv_m = m_samples["CV"] >= CV_THRESHOLD
        meets_threshold_m = meets_range_m | meets_cv_m

        # Check thresholds for Y-samples
        meets_range_y = y_samples["Range"] >= RANGE_THRESHOLD
        meets_cv_y = y_samples["CV"] >= CV_THRESHOLD
        meets_threshold_y = meets_range_y | meets_cv_y

        # Apply coloring logic
        if len(m_samples) == 3 and set(m_samples["Sample"]) == {"M1", "M2", "M3"}:
            if meets_threshold_m.all():
                df.loc[(df["Gene"] == gene) & (df["Sample"].isin(["M1", "M2", "M3"])), "Color"] = "red"
            elif meets_threshold_m.any():
                df.loc[(df["Gene"] == gene) & (df["Sample"].isin(["M1", "M2", "M3"])), "Color"] = "black"

        if len(y_samples) == 3 and set(y_samples["Sample"]) == {"Y1", "Y2", "Y3"}:
            if meets_threshold_y.all():
                df.loc[(df["Gene"] == gene) & (df["Sample"].isin(["Y1", "Y2", "Y3"])), "Color"] = "blue"
            elif meets_threshold_y.any():
                df.loc[(df["Gene"] == gene) & (df["Sample"].isin(["Y1", "Y2", "Y3"])), "Color"] = "black"

        # Check for green (both M and Y meet threshold)
        if (len(m_samples) == 3 and meets_threshold_m.all() and 
            len(y_samples) == 3 and meets_threshold_y.all()):
            df.loc[df["Gene"] == gene, "Color"] = "green"

        i += 6

    return df

def create_gene_category_summary(df, data_output_dir):
    """Create gene category summary based on colors"""
    # Get unique genes and their predominant color
    gene_colors = []
    
    for gene in df["Gene"].unique():
        gene_data = df[df["Gene"] == gene]
        colors = gene_data["Color"].value_counts()
        
        # Determine category based on color priority
        if "green" in colors.index:
            category = "Common Genes"  # Green - both M and Y meet threshold
        elif "red" in colors.index:
            category = "Mfd-"  # Red - M samples meet threshold
        elif "blue" in colors.index:
            category = "YB955"  # Blue - Y samples meet threshold
        elif "black" in colors.index:
            category = "Partial Threshold"  # Black - partial threshold
        else:
            category = "Below Threshold"  # Gray - below threshold
            
        gene_colors.append({"Gene": gene, "Category": category})
    
    gene_colors_df = pd.DataFrame(gene_colors)
    
    # Create summary table
    summary_table = (
        gene_colors_df
        .groupby("Category")["Gene"]
        .agg([
            ("Count", "count"),
            ("Genes", lambda x: ", ".join(sorted(x)))
        ])
        .reset_index()
    )
    
    # Save summary table
    summary_table.to_csv(os.path.join(data_output_dir, "gene_category_summary_table.csv"), index=False)
    print(summary_table)
    
    return gene_colors_df

def create_summary_files_by_category(df, gene_colors, data_output_dir):
    """Create summary text files for each category"""
    categories = {
        "All Sporulation": df["Gene"].unique(),
        "Mfd-": gene_colors[gene_colors["Category"] == "Mfd-"]["Gene"].values,
        "YB955": gene_colors[gene_colors["Category"] == "YB955"]["Gene"].values,
        "Common Genes": gene_colors[gene_colors["Category"] == "Common Genes"]["Gene"].values,
        "Partial Threshold": gene_colors[gene_colors["Category"] == "Partial Threshold"]["Gene"].values,
        "Below Threshold": gene_colors[gene_colors["Category"] == "Below Threshold"]["Gene"].values
    }
    
    for category, genes in categories.items():
        if len(genes) == 0:
            continue
            
        filename = f"Summary_Stats_{category.replace(' ', '_')}_Genes.txt"
        filepath = os.path.join(data_output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(f"Summary Statistics for {category} Genes\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Genes: {len(genes)}\n")
            f.write(f"Gene List: {', '.join(sorted(genes))}\n\n")
            
            # Calculate overall statistics for this category
            category_data = df[df["Gene"].isin(genes)]
            if not category_data.empty:
                f.write("Overall Statistics:\n")
                f.write("-" * 20 + "\n")
                stats_summary = category_data.groupby("Sample")[["Mean", "SD", "CV", "Range"]].mean()
                f.write(stats_summary.to_string())
                f.write("\n\n")
                
                f.write("Individual Gene Details:\n")
                f.write("-" * 25 + "\n")
                for gene in sorted(genes):
                    gene_data = category_data[category_data["Gene"] == gene]
                    if not gene_data.empty:
                        f.write(f"\n{gene}:\n")
                        gene_stats = gene_data.set_index("Sample")[["Mean", "SD", "CV", "Range"]]
                        f.write(gene_stats.to_string())
                        f.write("\n")

def create_interactive_plot(df, title, filename, legend_x=0.95, legend_y=0.35, legend_font_size=20, gene_label="Gene"):
    """Create an interactive scatter plot and save as JSON."""
    # Mapping of internal color codes to display names
    color_labels = {
        "red"   : "Mfd<sup>−</sup>",
        "blue"  : "YB955",
        "green" : "Common Genes",
        "black" : "Partial Threshold",
        "gray" : "Below Threshold"
    }

    fig = px.scatter(
        df, x="CV", y="Range",
        color="Color",
        color_discrete_map={
            "red": "red",
            "blue": "blue",
            "green": "green", 
            "black": "black",
            "gray": "gray"
        },
        category_orders={  # Legend display order (initial)
            "Color": ["blue", "red", "green", "black", "gray"]
        },
        hover_name=None,
        hover_data=None
    )
    
    for trace in fig.data:
        trace_color = trace.name
        sub_df = df[df["Color"] == trace_color]
        # Convert NumPy arrays to lists for JSON serialization
        trace.customdata = sub_df[["Gene", "Sample", "Mean", "SD"]].values.tolist()

    # Custom hover template with configurable gene label
    fig.update_traces(
        hovertemplate=f"<b>{gene_label}:</b> %{{customdata[0]}}<br>" +
                      "<b>Sample:</b> %{customdata[1]}<br>" +
                      "<b>Mean:</b> %{customdata[2]:.2f}<br>" +
                      "<b>SD:</b> %{customdata[3]:.2f}<br>" +
                      "<b>CV:</b> %{x:.3f}<br>" +
                      "<b>Range:</b> %{y:.0f}<extra></extra>"
    )

    # Add threshold lines
    fig.add_vline(
        x=CV_THRESHOLD,
        line_dash="dash",
        line_color="black",
        annotation_text=f" CV ≥ {CV_THRESHOLD}",
        annotation_font=dict(size=15)
    )
    fig.add_hline(
        y=RANGE_THRESHOLD,
        line_dash="dash",
        line_color="black",
        annotation_text=f"Range ≥ {RANGE_THRESHOLD}",
        annotation_font=dict(size=15)
    )

    # Layout styling with configurable legend position
    fig.update_layout(
        xaxis=dict(
            title=dict(text="Coefficient of Variation (CV)", font=dict(size=22)),
            tickfont=dict(size=20),
            showgrid=True,
            gridcolor="whitesmoke",
            gridwidth=0.5
        ),
        yaxis=dict(
            title=dict(text="Number of Reads (Range)", font=dict(size=22)),
            tickfont=dict(size=20),
            showgrid=True,
            gridcolor="whitesmoke",
            gridwidth=0.5
        ),
        title=title,
        title_font=dict(size=24),
        legend_title=None,
        legend_traceorder="normal",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            x=legend_x,
            y=legend_y,
            xanchor='right',
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.8)',
            font=dict(size=legend_font_size)
        )
    )

    # Draw Order Priority (higher drawn on top)
    render_priority = {
        "red": 5,
        "blue": 5,
        "green": 4,
        "black": 3,
        "gray": 2
    }

    # Legend Display Order
    legend_rank = {
        "YB955": 0,
        "Mfd<sup>−</sup>": 1,
        "Common Genes": 2,
        "Partial Threshold": 3,
        "Below Threshold": 4
    }

    # Sort traces by internal color value for rendering
    sorted_traces = sorted(fig.data, key=lambda t: render_priority.get(t.name, 0))

    # Rename traces and assign legend rank
    for trace in sorted_traces:
        original_name = trace.name
        display_name = color_labels.get(original_name, original_name)
        trace.name = display_name
        trace.legendrank = legend_rank.get(display_name, 100)

    # Reassign reordered traces
    fig.data = tuple(sorted_traces)

    # Dot styling by display name
    for trace in fig.data:
        if trace.name == "Below Threshold":
            trace.marker.size = 5
            trace.marker.opacity = 0.7
        elif trace.name == "Mfd<sup>−</sup>":
            trace.marker.size = 10
            trace.marker.opacity = 1.0
        elif trace.name == "YB955":
            trace.marker.size = 10
            trace.marker.opacity = 1.0
        elif trace.name == "Common Genes":
            trace.marker.size = 7
            trace.marker.opacity = 1.0
            trace.marker.symbol = "square"
        else:
            trace.marker.size = 5
            trace.marker.opacity = 0.9

    # Save figure as JSON
    with open(filename.replace('.html', '.json'), 'w') as f:
        json.dump(fig.to_dict(), f)

# Main execution workflow
print("Starting Sporulation Analysis Pipeline...")
print("=" * 50)

# Step 1: Process all CSV files and create combined dataset
print("\nStep 1: Processing CSV files and calculating statistics...")
data_df = process_files_with_error_handling(file_path, data_output_dir)

if data_df.empty:
    print("No data processed. Exiting.")
    sys.exit()

# Save combined statistics
data_df.to_csv(os.path.join(data_output_dir, "sporulation_CV_statistics.csv"), index=False)
print(f"Combined statistics saved to: {os.path.join(data_output_dir, 'sporulation_CV_statistics.csv')}")

# Step 2: Apply color coding based on thresholds
print("\nStep 2: Applying color coding based on thresholds...")
data_df = process_dataframe_with_colors(data_df)

# Step 3: Create gene category summary
print("\nStep 3: Creating gene category summary...")
gene_colors = create_gene_category_summary(data_df, data_output_dir)

# Step 4: Create summary files by category
print("\nStep 4: Creating summary files by category...")
create_summary_files_by_category(data_df, gene_colors, data_output_dir)

# Step 5: Create interactive plot
print("\nStep 5: Creating interactive visualization...")
create_interactive_plot(
    data_df, 
    "All Sporulation-Affected Genes", 
    os.path.join(assets_output_dir, "all_sporulation_genes_scatter_plot.html")
)
print("All sporulation-affected genes plot saved")

# Final summary
print(f"\nAnalysis complete! Outputs saved to:")
print(f"Data: {data_output_dir}")
print(f"Assets: {assets_output_dir}")
print("\nGenerated files:")
print("CSV Files:")
print(f"  - {os.path.join(data_output_dir, 'sporulation_CV_statistics.csv')}")
print(f"  - {os.path.join(data_output_dir, 'gene_category_summary_table.csv')}")
print("Text Files:")
print(f"  - {os.path.join(data_output_dir, 'individual_gene_summaries.txt')}")
print(f"  - {os.path.join(data_output_dir, 'Summary_Stats_All_Sporulation_Genes.txt')}")
print(f"  - {os.path.join(data_output_dir, 'Summary_Stats_Mfd-_Genes.txt')}")
print(f"  - {os.path.join(data_output_dir, 'Summary_Stats_YB955_Genes.txt')}")
print(f"  - {os.path.join(data_output_dir, 'Summary_Stats_Common_Genes_Genes.txt')}")
print(f"  - {os.path.join(data_output_dir, 'Summary_Stats_Partial_Threshold_Genes.txt')}")
print(f"  - {os.path.join(data_output_dir, 'Summary_Stats_Below_Threshold_Genes.txt')}")
print("JSON Plot:")
print(f"  - {os.path.join(assets_output_dir, 'all_sporulation_genes_scatter_plot.json')}")
