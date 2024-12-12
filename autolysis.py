# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pandas", "scikit-learn", "chardet", "requests", "seaborn", "matplotlib", "python-dotenv"]
# ///


import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import time

# Set your AI Proxy API key and base URL
openai.api_key = os.getenv("AIPROXY_TOKEN")
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

def read_csv(filename, encoding='utf-8'):
    return pd.read_csv(filename, encoding=encoding)

def perform_analysis(df):
    analysis = {}
    analysis['summary'] = df.describe(include='all').to_dict()
    analysis['missing_values'] = df.isnull().sum().to_dict()
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.shape[1] > 1:
        analysis['correlation_matrix'] = numeric_df.corr().to_dict()
    return analysis

def generate_insights(analysis):
    prompt = f"Analyze the following data summary and provide insights:\n{analysis}"
    max_retries = 5
    retry_delay = 1  # Start with a 1 second delay

    for attempt in range(max_retries):
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
            if attempt < max_retries - 1:
                print(f"Rate limit exceeded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise
        except openai.error.OpenAIError as e:
            print(f"Error: {e}")
            break

def create_visualizations(df, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    numeric_df = df.select_dtypes(include=['number'])
    
    # Correlation heatmap
    if numeric_df.shape[1] > 1:
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

def generate_readme(analysis, insights, output_dir):
    prompt = f"""
    Write a story about the following data analysis:

    1. The data received: {analysis['summary']}
    2. The analysis carried out: Summary statistics, missing values, and correlation matrix.
    3. The insights discovered: {insights}
    4. The implications of the findings: What actions should be taken based on the insights?

    Include the following images:
    - Correlation Matrix: correlation_matrix.png
    - Missing Values: missing_values.png
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a data analyst."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )

    story = response['choices'][0]['message']['content'].strip()

    readme_content = f"# Automated Data Analysis\n\n{story}\n\n"
    readme_content += "## Correlation Matrix\n\n![Correlation Matrix](correlation_matrix.png)\n\n"
    readme_content += "## Missing Values\n\n![Missing Values](missing_values.png)\n\n"

    with open(os.path.join(output_dir, 'README.md'), 'w') as f:
        f.write(readme_content)

def main(filename):
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            df = read_csv(filename, encoding=encoding)
            break
        except UnicodeDecodeError:
            print(f"Failed to read file with encoding {encoding}, trying next encoding...")
    else:
        print("Failed to read the file with all attempted encodings.")
        return

    analysis = perform_analysis(df)
    insights = generate_insights(analysis)
    output_dir = os.path.splitext(filename)[0]
    create_visualizations(df, output_dir)
    generate_readme(analysis, insights, output_dir)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py dataset.csv")
        sys.exit(1)
    main(sys.argv[1])