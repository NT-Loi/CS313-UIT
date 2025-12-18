import pandas as pd
import glob

# Find all feature files
feature_files = glob.glob("features_*.csv")
numeric_feature_files = glob.glob("numeric_features_*.csv")

# Create a list to hold the dataframes
dfs = []

# Load and append feature files
for filename in feature_files:
    df = pd.read_csv(filename)
    dfs.append(df)

# Load and append numeric feature files
for filename in numeric_feature_files:
    df = pd.read_csv(filename)
    # Add a prefix to numeric feature columns to avoid conflicts
    df = df.rename(columns={col: f"num_{col}" for col in df.columns if col != 'id'})
    dfs.append(df)

# Concatenate all dataframes
if dfs:
    merged_df = pd.concat(dfs, ignore_index=True)
    # Drop duplicate rows if any, keeping the first occurrence
    merged_df = merged_df.drop_duplicates(subset=['id'])
    merged_df.to_csv("features.csv", index=False)
    print("Successfully merged all feature files into features.csv")
else:
    print("No feature files found.")
