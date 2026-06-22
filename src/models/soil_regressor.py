import torch
import torch.nn as nn
import pytorch_lightning as pl
from torchmetrics import MeanSquaredError, R2Score

class SoilRegressor(pl.LightningModule):
    """MLP that predicts multiple soil nutrient levels from tabular inputs."""
    def __init__(self, input_dim, output_dim, hidden_dims=[64,32], dropout=0.2, lr=1e-3):
        super().__init__()
        self.save_hyperparameters()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, output_dim))
        self.net = nn.Sequential(*layers)
        self.criterion = nn.MSELoss()
        self.train_rmse = MeanSquaredError(squared=False)
        self.val_rmse = MeanSquaredError(squared=False)
        self.train_r2 = R2Score(num_outputs=output_dim)
        self.val_r2 = R2Score(num_outputs=output_dim)

    def forward(self, x):
        return self.net(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        pred = self(x)
        loss = self.criterion(pred, y)
        self.train_rmse(pred, y)
        self.train_r2(pred, y)
        self.log('train_loss', loss, prog_bar=True)
        self.log('train_rmse', self.train_rmse, prog_bar=True)
        self.log('train_r2', self.train_r2, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        pred = self(x)
        loss = self.criterion(pred, y)
        self.val_rmse(pred, y)
        self.val_r2(pred, y)
        self.log('val_loss', loss, prog_bar=True)
        self.log('val_rmse', self.val_rmse, prog_bar=True)
        self.log('val_r2', self.val_r2, prog_bar=True)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)