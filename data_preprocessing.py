import json
import pandas as pd
from pathlib import Path
import re
import numpy as np
from sklearn.preprocessing import LabelEncoder
from scipy.stats import linregress

def normalize_category(cat):
    match = re.search(r'\((.*?)\)', cat)
    return match.group(1) if match else cat.strip()

def normalize_ranking(value):
    if value in ['A*', 'A', 'B', 'C']:
        return value  # CORE ranking
    elif value in ['Q1', 'Q2', 'Q3', 'Q4']:
        return value  # Scimago quartile
    else:
        return 'Other'

def extract_author_stats(authors_list):
    if not authors_list:
        return pd.Series({
            "mean_citations": np.nan,
            "max_citations": np.nan,
            "mean_h_index": np.nan,
            "max_h_index": np.nan,
            "mean_i10_index": np.nan,
            "max_i10_index": np.nan,
        })
    citations = [(a.get("citations_all") or 0) for a in authors_list]
    h = [(a.get("h_index_all") or 0) for a in authors_list]
    i10 = [(a.get("i10_index_all") or 0) for a in authors_list]
    return pd.Series({
        "mean_citations": np.mean(citations),
        "max_citations": np.max(citations),
        "mean_h_index": np.mean(h),
        "max_h_index": np.max(h),
        "mean_i10_index": np.mean(i10),
        "max_i10_index": np.max(i10),
    })

def safe_slope(g, year_col, value_col, x0):
    g = g[g[year_col] > x0]
    if len(g) < 2:
        return 0
    return linregress(g[year_col], g[value_col]).slope

def pipeline(df, year):
    # Create dataset for predicting {year} citation

    venue_df = pd.json_normalize(df['venue'], sep='.')
    venue_df.index = df.index
    df = pd.concat([df, venue_df], axis=1)
    df.drop(columns=['venue'], inplace=True)
    df.rename(columns={'name': 'venue_name',
                    'type': 'venue_type',
                    'ranking': 'venue_ranking'},
            inplace=True)
    
    df.drop(columns=['pdf_url', 'embedding', 'venue_name'], inplace=True)
    df['categories'] = df['categories'].apply(lambda lst: [normalize_category(c) for c in lst])
    df['primary_category'] = df['primary_category'].apply(normalize_category)

    # Remove paper with num_pages = null
    df = df[df['num_pages'].notna()]

    # Drop keywords
    df.drop(columns='keywords', inplace=True)

    # Remove paper with citations_by_year and citationCount = null
    df = df[df['citations_by_year'].notna()]
    df = df[df['citationCount'].notna()]

    # Fill missing values in github_stars = 0
    df.loc[df['github_stars'].isna(), 'github_stars'] = 0

    # Fill missing (venue.type, venue.ranking) = (preprint, 0)
    df.loc[df['venue_type'].isna(), 'venue_type'] = 'preprint'
    df.loc[df['venue_ranking'].isna(), 'venue_ranking'] = 0
    
    df['published_date'] = pd.to_datetime(df['published_date'])
    df['published_year'] = df['published_date'].dt.year
    
    def fill_citations_by_year(row):
        citations_by_year = row['citations_by_year']
        published_year = row['published_year']
        result = {}
        for y in range(published_year, year+1):
            citation = citations_by_year.get(f'{y}', 0)
            result[f'{y}'] = citation
        return result

    df['citations_by_year'] = df.apply(fill_citations_by_year, axis=1)

    # Assign outliers' venue ranking by their nearest median
    df['venue_ranking'] = df['venue_ranking'].apply(normalize_ranking)

    # Remove citations_by_years after {year-1} to avoid data leakage
    def adjust_citation_count(row):
        citations = row.get("citations_by_year", {})
        total = row.get("citationCount", 0)

        if not isinstance(citations, dict):
            return total

        future_citations = sum(
            v for k, v in citations.items()
            if isinstance(k, (int, str)) and str(k).isdigit() and int(k) > year-1
        )

        return max(total - future_citations, 0)

    df["citationCount"] = df.apply(adjust_citation_count, axis=1)
    df[f"citations"] = df["citations_by_year"].apply(
        lambda x: x.get(f"{year}", 0) if isinstance(x, dict) else 0
    )    
    df["citationCount_log"] = np.log1p(df["citationCount"])
    df[f"citations_log"] = np.log1p(df[f"citations"])
    
    venue_medians = (
        df[df['venue_ranking'] != 'Other']
        .groupby('venue_ranking')['citationCount']
        .median()
        .to_dict()
    )

    other_group = df[df['venue_ranking'] == 'Other']
    Q1 = np.percentile(other_group['citationCount'], 25)
    Q3 = np.percentile(other_group['citationCount'], 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers_other = other_group[
        (other_group['citationCount'] < lower_bound) |
        (other_group['citationCount'] > upper_bound)
    ]

    def nearest_venue(citation, medians):
        return min(medians.keys(), key=lambda k: abs(medians[k] - citation))

    for idx, row in outliers_other.iterrows():
        nearest = nearest_venue(row['citationCount'], venue_medians)
        df.at[idx, 'venue_ranking'] = nearest

    # Number of authors
    def count_authors(authors):
        return len(authors)
    
    df['num_authors'] = df['authors'].apply(count_authors)
    
    # Add authors' statistics
    author_features = df["authors"].apply(extract_author_stats)
    df = pd.concat([df, author_features], axis=1)

    # Encoding
    df['venue_type'] = df['venue_type'].map({'preprint':0, 'conference':1, 'journal':2})
    df['venue_ranking'] = df['venue_ranking'].map({'Q4':1, 'Q3':2, 'Q2':3, 'Q1':4, 'C': 1, 'B':2, 'A':3, 'A*':4, 'Other':0})
    
    le = LabelEncoder()
    df['primary_category'] = le.fit_transform(df['primary_category'])
    
    # Add slope of trend for each category (based on number of papers and citations in each category over time)
    # Exclude anomaly years for papers
    papers_trend = (
        df[~df['published_year'].isin([2020])]
        .groupby(['primary_category', 'published_year'])
        .size()
        .reset_index(name='num_papers')
    )

    # Exclude anomaly years for citations
    records = []

    for _, row in df.iterrows():
        cat = row['primary_category']
        cby = row['citations_by_year']

        if not isinstance(cby, dict):
            continue

        for y, c in cby.items():
            try:
                y = int(y)
            except ValueError:
                continue

            records.append({
                'primary_category': cat,
                'published_year': y,
                'citations': c
            })

    citations_long = pd.DataFrame(records)
    citations_trend = (
    citations_long[~citations_long['published_year'].isin([2023, 2024, 2025])]
    .groupby(['primary_category', 'published_year'])['citations']
    .sum()
    .reset_index(name='total_citations')
    )

    # Compute slopes
    slope_papers = (
        papers_trend
        .groupby('primary_category')
        .apply(
            lambda g: safe_slope(
                g,
                'published_year',   # ✅ column name
                'num_papers',       # ✅ column name
                year
            ),
            include_groups=False
        )
        .reset_index(name='slope_papers')
    )

    slope_citations = (
        citations_trend
        .groupby('primary_category')
        .apply(
            lambda g: safe_slope(
                g,
                'published_year',   # ✅ column name
                'total_citations',  # ✅ column name
                year
            ),
            include_groups=False
        )
        .reset_index(name='slope_citations')
    )

    # Combine
    trend_df = slope_papers.merge(slope_citations, on='primary_category', how='outer')
    df = df.merge(trend_df, on="primary_category", how="left")

    df['num_years_after_publication'] = df['published_year'].apply(lambda x: year - x)
    
    # Add statistics about citations over years (mean, std)

    def get_mean_before(citations_by_year, year):
        if not isinstance(citations_by_year, dict):
            return 0.0

        values = [
            v for k, v in citations_by_year.items()
            if str(k).isdigit() and int(k) <= year
        ]

        return float(np.mean(values)) if values else 0.0


    def get_std_before(citations_by_year, year):
        if not isinstance(citations_by_year, dict):
            return 0.0

        values = [
            v for k, v in citations_by_year.items()
            if str(k).isdigit() and int(k) <= year
        ]

        return float(np.std(values)) if values else 0.0

    df['mean_citations_over_years'] = df['citations_by_year'].apply(lambda x: get_mean_before(x, year))
    df['std_citations_over_years'] = df['citations_by_year'].apply(lambda x: get_std_before(x, year))
    # df.drop(columns = "citationCount", inplace=True)
    # df.drop(columns = f"citations", inplace=True)

    numeric_df = df.select_dtypes(include=["number"])
    numeric_df.drop(columns=['published_year'], inplace=True)
    numeric_df = numeric_df.fillna(0)
    
    df.to_csv(f"features_{year}.csv", index=False)
    numeric_df.to_csv(f"numeric_features_{year}.csv", index=False)
    return df, numeric_df

if __name__ == '__main__':
    root_dir = Path("data (Copy)")

    target_folders = []
    for year in range(2012, 2025):
        target_folders.append(f'{year}')

        records = []

        for folder in target_folders:
            folder_path = root_dir / folder

            print(f"📂 Scanning: {folder_path}")

            # Loop through all json files in the folder
            for json_file in folder_path.glob("*.json"):

                # Read JSON
                try:
                    with open(json_file, "r") as f:
                        data = json.load(f)
                except Exception as e:
                    print(f"⚠️ Failed to read {json_file}: {e}")
                    continue


                records.append(data)

        # Create dataframe
        df = pd.DataFrame(records)
        duplicates = df.duplicated(subset='arxiv_id').sum()
        if duplicates:
            df = df.drop_duplicates(subset="arxiv_id")
        pipeline(df, year)
        print(f"\tFinish extract features for {year}!\n")
        # print(dataset.columns)