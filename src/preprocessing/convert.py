import os
import cv2
import pandas as pd
from tqdm import tqdm

def preprocess_crop(raw_dir, processed_dir, image_size=224):
    """
    Convert all images in raw_dir (subfolders 0,1,2... named by class index)
    to grayscale, resize, and save into processed_dir/images/.
    Creates a csv mapping image_name -> label.
    """
    img_dir = os.path.join(processed_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    records = []
    for class_idx in os.listdir(raw_dir):
        class_folder = os.path.join(raw_dir, class_idx)
        if not os.path.isdir(class_folder):
            continue
        try:
            label = int(class_idx)
        except ValueError:
            continue
        for fname in tqdm(os.listdir(class_folder), desc=f"Class {label}"):
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
            src_path = os.path.join(class_folder, fname)
            img = cv2.imread(src_path, cv2.IMREAD_COLOR)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (image_size, image_size))
            dst_name = f"{label}_{fname}"  # avoid name collisions
            dst_path = os.path.join(img_dir, dst_name)
            cv2.imwrite(dst_path, resized)
            records.append({"image_path": dst_name, "label": label})
    df = pd.DataFrame(records)
    df.to_csv(os.path.join(processed_dir, "all.csv"), index=False)
    print(f"Preprocessed {len(df)} images for {processed_dir}")
    return df