# CS313 - Predict Research Paper Popularity (Citations)

This project aims to predict the popularity of research papers by collecting and analyzing metadata from various sources, including arXiv, Google Scholar, Hugging Face, and Semantic Scholar. The pipeline automates the process of scraping, enriching, and saving paper metadata for further analysis.

Dataset is available at: [Link](https://drive.google.com/drive/folders/1ZCR9uN_JuNhNj3KJ7bV3jaIl5R5-rDOt?usp=drive_link)

---
## I. Crawl data
### Features

- **arXiv Scraper**: Fetches paper metadata such as title, authors, abstract, categories, and submission history.
- **Google Scholar Scraper**: Retrieves citation counts, citations over years, and author statistics (e.g., citations, h-index, i10-index).
- **Hugging Face Scraper**: Extracts GitHub stars, upvotes, and other metrics for papers hosted on Hugging Face.
- **Semantic Scholar Scraper**: Enriches paper metadata with citation and reference details.
- **Pipeline Execution**: Combines all scrapers into a unified pipeline for seamless data collection.

---

### Prerequisites

Before running the pipeline, ensure you have the following installed:

1. **Python**: Version 3.10 or higher.
2. **Google Chrome**: Required for Selenium-based scraping.
3. **ChromeDriver**: Ensure the version matches your installed Chrome browser.
4. **Dependencies**: Install the required Python libraries using the `requirements.txt` file.

---

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NT-Loi/CS313-UIT.git
   cd CS313-UIT
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure `ChromeDriver` is in your system's PATH or specify its location in the scraper code.

---

### Usage

Run the scraper (please set the appropriate **year**). This scraper will automatically scrape papers in **category** = `'cs'` and **year** = `<year>`:

```bash
python pipeline.py
```

If the pipeline is interrupted, it will automatically resume from the last saved state in **`data/progressing.json`**. Duplicates are ensured not to be processed again.

---

### Output

- **Processed Papers**: Saved in the **`data/`** directory as individual JSON files (e.g., `1801.00005.json`).
- **Logs**: Detailed logs are saved in `arxiv.log`, `google_scholar.log`, and other log files for debugging.
- **Metadata Files**:
  - **`data/processed.json`**: Tracks all processed paper IDs.
  - **`data/progressing.json`**: Tracks papers currently being processed.

---

### Troubleshooting

#### 1. CAPTCHA Issues
- If Google Scholar prompts for CAPTCHA, solve it manually in the browser window and press Enter to continue.

#### 2. ChromeDriver Version Mismatch
- Ensure the installed ChromeDriver version matches your Chrome browser version.

## II. Exploratory Data Analysis & Preprocessing
After collecting and cleaning the paper metadata, the next step is to perform Exploratory Data Analysis (EDA) to understand key patterns, insights, and data distributions.

**Notebook**: ```eda.ipynb```

This notebook analyzes the collected dataset and visualizes important insights.

## III. Model Training & Evaluation
The goal of the model is to predict the future popularity (citation count) in next years of research papers based on their metadata and early metrics.

**Notebook:** ```predictmodel.ipynb```

### Data Preparation
- Split the dataset into training and test sets with ratio 8:2
- Scale numerical features with ```StandardScaler```

### Model Selection
- Linear Regression
- Random Forest Regressor
- XGBoost

The model currently uses default parameters.

### Evaluation
- Evaluate model predictions on the test set using standard regression metrics:
+ R² Score
+ RMSE (Root Mean Squared Error)
+ MAE (Mean Absolute Error)

Among all baseline models, the Random Forest Regressor achieved the highest performance across all metrics, demonstrating strong capability in capturing non-linear relationships and feature interactions within the dataset.

### Next Phase
- Continue collecting more data
- Use sequence models (RNN, LSTM, etc.)
- Create embeddings for text-related features (title, abstract, keywords, category)
- Predict for multiple future years, not limited to a single year
- Analyze and interpret the model (feature importance analysis)