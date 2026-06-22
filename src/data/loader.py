import os
import pytorch_lightning as pl
from torch.utils.data import DataLoader
from .dataset import GAIAImageDataset
from .transforms import get_transforms

class GAIADataModule(pl.LightningDataModule):
    def __init__(self, crop_name, processed_dir="data/processed", batch_size=32,
                 num_workers=2, image_size=224):
        super().__init__()
        self.crop_dir = os.path.join(processed_dir, crop_name)
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.image_size = image_size

    def setup(self, stage=None):
        self.train_dataset = GAIAImageDataset(
            os.path.join(self.crop_dir, "train.csv"),
            os.path.join(self.crop_dir, "images"),
            transform=get_transforms(augment=True, image_size=self.image_size)
        )
        self.val_dataset = GAIAImageDataset(
            os.path.join(self.crop_dir, "val.csv"),
            os.path.join(self.crop_dir, "images"),
            transform=get_transforms(augment=False, image_size=self.image_size)
        )

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size,
                          shuffle=True, num_workers=self.num_workers)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size,
                          shuffle=False, num_workers=self.num_workers)