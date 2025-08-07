import os
import pandas as pd 

root_directory = "/workspaces/ner_news_malay/scraper"

# Initialize list to store DataFrames
df_list = []

for dirpath, _, filenames in os.walk(root_directory):
    for filename in filenames:
        if filename.endswith(".csv"):
            file_path = os.path.join(dirpath, filename)
            try:
                # Read CSV into temporary DataFrame
                temp_df = pd.read_csv(file_path)
                # Append to our list of DataFrames
                df_list.append(temp_df)
                print(f"Successfully read: {file_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

if df_list:
    # Concatenate all DataFrames in the list
    merged_df = pd.concat(df_list, ignore_index=True)
    # Save to NEW file (original files remain untouched)
    merged_df.to_csv(os.path.join(root_directory, "/workspaces/ner_news_malay/scraper/news_merged/malay_news.csv"), index=False)
    print(f"Merged {len(df_list)} files successfully! Output: merged_output.csv")
else:
    print("No CSV files found to merge.")