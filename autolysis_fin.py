import os
import argparse
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import time
from pandas.plotting import scatter_matrix

# Configuration: API key for OpenAI (set as environment variable)
openai.api_key = os.getenv("AIPROXY_TOKEN")
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

# ----------------------------- Utility Functions -----------------------------

def read_csv(filename):
    """Read CSV file with multiple encodings dynamically."""
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            return pd.read_csv(filename, encoding=encoding)
        except UnicodeDecodeError:
            pass
    print("Error: Unable to decode file with supported encodings.")
    return None

def analyze_data(df):
    """Perform a comprehensive analysis of the data."""
    summary = df.describe(include='all').to_dict()
    missing_values = df.isnull().sum().to_dict()
    correlation_matrix = df.select_dtypes(include=[np.number]).corr().to_dict()
    return summary, missing_values, correlation_matrix

def detect_outliers(df):
    """Identify outliers using the IQR method."""
    numeric_df = df.select_dtypes(include=[np.number])
    Q1 = numeric_df.quantile(0.25)
    Q3 = numeric_df.quantile(0.75)
    IQR = Q3 - Q1
    return ((numeric_df < (Q1 - 1.5 * IQR)) | (numeric_df > (Q3 + 1.5 * IQR))).sum().to_dict()

def generate_insights(summary, missing_values, correlation_matrix, outliers):
    """Generate insights using OpenAI GPT."""
    prompt = f"""
    Analyze the following data:
    Summary Statistics: {summary}
    Missing Values: {missing_values}
    Correlation Matrix: {correlation_matrix}
    Outliers: {outliers}

    Provide actionable insights and recommendations for data cleaning, analysis, and visualization.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a data analysis expert."},
                      {"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"OpenAI Error: {e}"

# ----------------------------- Visualization Functions -----------------------------

def create_visualizations(df, output_dir):
    """Create a suite of visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    numeric_df = df.select_dtypes(include=[np.number])

    # Correlation Heatmap
    if not numeric_df.empty:
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
        plt.title("Correlation Heatmap")
        plt.savefig(os.path.join(output_dir, "correlation_heatmap.png"))
        plt.close()

    # Pair Plot
    if len(numeric_df.columns) > 1:
        sns.pairplot(numeric_df)
        plt.savefig(os.path.join(output_dir, "pairplot.png"))
        plt.close()

    # Histograms
    for column in numeric_df.columns:
        plt.figure()
        sns.histplot(numeric_df[column], kde=True)
        plt.title(f"Histogram of {column}")
        plt.savefig(os.path.join(output_dir, f"histogram_{column}.png"))
        plt.close()

    # Scatter Matrix
    if not numeric_df.empty:
        scatter_matrix(numeric_df, figsize=(12, 12))
        plt.savefig(os.path.join(output_dir, "scatter_matrix.png"))
        plt.close()

# ----------------------------- Report Generation -----------------------------

def generate_readme(output_dir, summary, missing_values, correlation_matrix, outliers, insights):
    """Generate a detailed README.md file."""
    with open(os.path.join(output_dir, "README.md"), 'w') as f:
        f.write("# Data Analysis Report\n\n")
        f.write("## Summary Statistics\n")
        f.write(f"{pd.DataFrame(summary).to_markdown()}\n\n")
        f.write("## Missing Values\n")
        f.write(f"{missing_values}\n\n")
        f.write("## Correlation Matrix\n")
        f.write(f"{correlation_matrix}\n\n")
        f.write("## Outliers\n")
        f.write(f"{outliers}\n\n")
        f.write("## Generated Insights\n")
        f.write(insights + "\n\n")
        f.write("## Visualizations\n")
        f.write("Refer to generated images in the output directory.\n")

# ----------------------------- Main Function -----------------------------

def main():
    """Main function to orchestrate the analysis workflow."""
    parser = argparse.ArgumentParser(description="Automated Data Analysis Tool")
    parser.add_argument("filename", help="Path to the input CSV file")
    parser.add_argument("--output", default="output", help="Directory to save results")
    args = parser.parse_args()

    # Load data
    df = read_csv(args.filename)
    if df is None:
        print("Error: Failed to load data.")
        return

    # Perform analysis
    summary, missing_values, correlation_matrix = analyze_data(df)
    outliers = detect_outliers(df)
    insights = generate_insights(summary, missing_values, correlation_matrix, outliers)

    # Generate outputs
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    create_visualizations(df, output_dir)
    generate_readme(output_dir, summary, missing_values, correlation_matrix, outliers, insights)

    print(f"Analysis complete! Results saved to: {output_dir}")

# ----------------------------- Script Execution -----------------------------

if __name__ == "__main__":
    main()