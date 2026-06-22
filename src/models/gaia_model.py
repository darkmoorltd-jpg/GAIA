import torch
import torch.nn as nn
import pytorch_lightning as pl
import torchmetrics
from .tiny_vit import TinyViT


class GAIAModel(pl.LightningModule):
    """Multi‑crop disease classifier based on TinyViT."""

    def __init__(self, num_classes=5, lr=1e-3, weight_decay=0.01, in_chans=1):
        super().__init__()
        self.save_hyperparameters()
        self.encoder = TinyViT(
            in_chans=in_chans,
            embed_dim=128,
            depth=4,
            num_heads=4
        )
        self.head = nn.Linear(128, num_classes)
        self.criterion = nn.CrossEntropyLoss()

        self.train_acc = torchmetrics.Accuracy(
            task="multiclass", num_classes=num_classes
        )
        self.val_acc = torchmetrics.Accuracy(
            task="multiclass", num_classes=num_classes
        )

    def forward(self, x):
        features = self.encoder(x)[:, 0, :]
        return self.head(features)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        self.train_acc(logits, y)
        self.log("train_loss", loss, prog_bar=True)
        self.log("train_acc", self.train_acc, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.criterion(logits, y)
        self.val_acc(logits, y)
        self.log("val_loss", loss, prog_bar=True)
        self.log("val_acc", self.val_acc, prog_bar=True)

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hparams.lr,
            weight_decay=self.hparams.weight_decay,
        )
        return optimizer