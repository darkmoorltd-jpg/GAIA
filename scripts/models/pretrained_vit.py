import torch.nn as nn
import pytorch_lightning as pl
import torchmetrics
import timm

class PretrainedViTClassifier(pl.LightningModule):
    def __init__(self, num_classes, lr=5e-5):
        super().__init__()
        self.save_hyperparameters()
        self.backbone = timm.create_model('vit_tiny_patch16_224', pretrained=False, num_classes=0)
        self.head = nn.Linear(self.backbone.embed_dim, num_classes)
        self.criterion = nn.CrossEntropyLoss()
        self.train_acc = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)
        self.val_acc = torchmetrics.Accuracy(task="multiclass", num_classes=num_classes)

    def forward(self, x):
        return self.head(self.backbone(x))