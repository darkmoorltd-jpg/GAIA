import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.preprocessing.convert import preprocess_crop
from src.preprocessing.split import train_val_split

CROPS = ['cassava', 'maize', 'tomato']

def main():
    base_raw = "data/raw"
    base_proc = "data/processed"
    for crop in CROPS:
        raw_dir = os.path.join(base_raw, crop)
        proc_dir = os.path.join(base_proc, crop)
        if not os.path.exists(raw_dir):
            print(f"Raw directory {raw_dir} not found, skipping.")
            continue
        print(f"Processing {crop}...")
        preprocess_crop(raw_dir, proc_dir)
        train_val_split(proc_dir)
    print("All crops preprocessed.")

if __name__ == "__main__":
    main()