import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import time
import requests
import json

# Set OpenAI API key and base URL
openai.api_key = os.getenv("AIPROXY_TOKEN")
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

# Function to read CSV with multiple encoding options
def read_csv(filename):
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            return pd.read_csv(filename, encoding=encoding)
        except UnicodeDecodeError:
            print(f"Failed with encoding {encoding}, trying next...")
    print("Failed to read file with all encodings.")
    return None

# Function to perform data analysis
def analyze_data(df):
    summary = df.describe(include='all').to_dict()
    missing_values = df.isnull().sum().to_dict()
    numeric_df = df.select_dtypes(include=[np.number])
    correlation_matrix = numeric_df.corr().to_dict() if not numeric_df.empty else {}
    return summary, missing_values, correlation_matrix

# Function to detect outliers using the IQR method
def detect_outliers(df):
    numeric_df = df.select_dtypes(include=[np.number])
    Q1 = numeric_df.quantile(0.25)
    Q3 = numeric_df.quantile(0.75)
    IQR = Q3 - Q1
    return ((numeric_df < (Q1 - 1.5 * IQR)) | (numeric_df > (Q3 + 1.5 * IQR))).sum().to_dict()

# Function to generate visualizations
def create_visualizations(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    numeric_df = df.select_dtypes(include=[np.number])
    
    # Correlation heatmap
    if not numeric_df.empty:
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
        plt.title('Correlation Matrix')
        plt.savefig(os.path.join(output_dir, 'correlation_matrix.png'))
        plt.close()

    # Missing values bar plot
    missing_values = df.isnull().sum()
    if missing_values.any():
        plt.figure(figsize=(10, 8))
        missing_values.plot(kind='bar')
        plt.title('Missing Values')
        plt.savefig(os.path.join(output_dir, 'missing_values.png'))
        plt.close()

    # Outliers bar plot
    outliers = detect_outliers(df)
    if any(outliers.values()):
        plt.figure(figsize=(10, 6))
        pd.Series(outliers).plot(kind='bar', color='red')
        plt.title('Outliers')
        plt.savefig(os.path.join(output_dir, 'outliers.png'))
        plt.close()

# Function to generate insights using OpenAI
def generate_insights(summary, missing_values, correlation_matrix, outliers):
    prompt = f"""
    Analyze the following data analysis:
    - Summary: {summary}
    - Missing Values: {missing_values}
    - Correlation Matrix: {correlation_matrix}
    - Outliers: {outliers}

    Provide detailed insights and implications.
    """
    for attempt in range(5):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.RateLimitError:
            time.sleep(2 ** attempt)  # Exponential backoff
        except openai.error.OpenAIError as e:
            print(f"Error: {e}")
            break
    return "Failed to generate insights."

# Function to create a README file
def generate_readme(summary, missing_values, correlation_matrix, outliers, insights, output_dir):
    readme_path = os.path.join(output_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write("# Automated Data Analysis Report\n\n")
        f.write("## Summary Statistics\n")
        f.write(str(summary) + "\n\n")
        f.write("## Missing Values\n")
        f.write(str(missing_values) + "\n\n")
        f.write("## Correlation Matrix\n")
        f.write(str(correlation_matrix) + "\n\n")
        f.write("## Outliers\n")
        f.write(str(outliers) + "\n\n")
        f.write("## Insights\n")
        f.write(insights + "\n\n")
        f.write("## Visualizations\n")
        f.write("![Correlation Matrix](correlation_matrix.png)\n")
        f.write("![Missing Values](missing_values.png)\n")
        f.write("![Outliers](outliers.png)\n")
    print(f"README generated at {readme_path}")

# Main function
def main(filename):
    df = read_csv(filename)
    if df is None:
        return
    
    summary, missing_values, correlation_matrix = analyze_data(df)
    outliers = detect_outliers(df)
    insights = generate_insights(summary, missing_values, correlation_matrix, outliers)
    
    output_dir = os.path.splitext(filename)[0]
    create_visualizations(df, output_dir)
    generate_readme(summary, missing_values, correlation_matrix, outliers, insights, output_dir)
    print(f"Analysis completed. Check {output_dir} for results.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python merged_autolysis.py dataset.csv")
        sys.exit(1)
    main(sys.argv[1])