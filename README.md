# TDSProj2LLM
TDS Project 2 based on LLMs IITM

# Automated Data Analysis

This project provides an automated data analysis tool that reads a CSV file, performs analysis, generates insights using the `gpt-4o-mini` model, creates visualizations, and writes a story about the analysis to `README.md`.

## Features

- Reads a CSV file and performs data analysis
- Generates insights using the `gpt-4o-mini` model
- Creates visualizations including a correlation matrix and missing values bar plot
- Writes a story about the analysis to `README.md`

## Requirements

- Python 3.x
- pandas
- seaborn
- matplotlib
- openai

## Setup

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. **Install the required libraries:**
    ```sh
    pip install pandas seaborn matplotlib openai
    ```

3. **Set the AI Proxy API key:**
    ```sh
    export AIPROXY_TOKEN=your_ai_proxy_key
    ```

## Usage

To run the script, use the following command:
```sh
python3 autolysis.py dataset.csv
