import os
import pandas as pd

# set/create paths
root_directory = "ner_news_malay\scraper"
output_folder = "..\model_gliner\data"
os.makedirs(output_folder, exist_ok=True)

csv_dfs = []
parquet_dfs = []

# go through directory
for dirpath, _, filenames in os.walk(root_directory):
    for filename in filenames:
        file_path = os.path.join(dirpath, filename)
        
        # get csv files
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(file_path)
                csv_dfs.append(df)
                print(f"Successfully read CSV: {file_path}")
            except Exception as e:
                print(f"Error reading CSV {file_path}: {e}")
        
        # get parquet files
        elif filename.endswith(".parquet"):
            try:
                df = pd.read_parquet(file_path)
                parquet_dfs.append(df)
                print(f"Successfully read Parquet: {file_path}")
            except Exception as e:
                print(f"Error reading Parquet {file_path}: {e}")

# merge and save csv files
if csv_dfs:
    merged_csv = pd.concat(csv_dfs, ignore_index=True)
    csv_output_path = os.path.join(output_folder, "malay_news.csv")
    merged_csv.to_csv(csv_output_path, index=False)
    print(f"\nMerged {len(csv_dfs)} CSV files into {csv_output_path}")
    print(f"CSV dataset size: {len(merged_csv):,} rows")
else:
    print("\nNo CSV files found to merge.")

# merge and save parquet files
if parquet_dfs:
    merged_parquet = pd.concat(parquet_dfs, ignore_index=True)
    parquet_output_path = os.path.join(output_folder, "malay_news.parquet")
    merged_parquet.to_parquet(
        parquet_output_path,
        engine='pyarrow',
        compression='snappy',
        index=False
    )
    print(f"\nMerged {len(parquet_dfs)} parquet files into {parquet_output_path}")
    print(f"Parquet dataset size: {len(merged_parquet):,} rows")
else:
    print("\nNo Parquet files found to merge.")

print("\nMerging complete!")