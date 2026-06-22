import pandas as pd
import torch
from torch.utils.data import Dataset

class TabularDataset(Dataset):
    """CSV dataset for regression. Assumes first columns are features, last ones are targets."""
    def __init__(self, csv_path, feature_cols, target_cols, transform=None):
        self.df = pd.read_csv(csv_path)
        self.features = self.df[feature_cols].values.astype('float32')
        self.targets = self.df[target_cols].values.astype('float32')
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        x = torch.tensor(self.features[idx])
        y = torch.tensor(self.targets[idx])
        if self.transform:
            x = self.transform(x)
        return x, y