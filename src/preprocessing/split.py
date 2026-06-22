import pandas as pd
from sklearn.model_selection import train_test_split

def train_val_split(processed_dir, test_size=0.2, random_state=42):
    all_csv = f"{processed_dir}/all.csv"
    df = pd.read_csv(all_csv)
    train_df, val_df = train_test_split(df, test_size=test_size,
                                        stratify=df['label'],
                                        random_state=random_state)
    train_df.to_csv(f"{processed_dir}/train.csv", index=False)
    val_df.to_csv(f"{processed_dir}/val.csv", index=False)
    print(f"Train: {len(train_df)}, Val: {len(val_df)}")