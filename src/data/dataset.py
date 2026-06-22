import os
import pandas as pd
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset

class GAIAImageDataset(Dataset):
    """Dataset for preprocessed grayscale images."""
    def __init__(self, csv_path, img_dir, transform=None):
        self.df = pd.read_csv(csv_path)
        self.img_dir = img_dir
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = row['image_path']
        label = int(row['label'])
        img_path = os.path.join(self.img_dir, img_name)
        # Load grayscale
        img = Image.open(img_path).convert('L')  # 'L' mode for 1 channel
        if self.transform:
            img = self.transform(img)
        else:
            # default to tensor
            img = torch.from_numpy(np.array(img)).unsqueeze(0).float() / 255.0
        return img, label