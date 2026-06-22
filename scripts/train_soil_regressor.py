import sys, os, yaml, argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytorch_lightning as pl
from torch.utils.data import DataLoader, random_split
from src.data.tabular_dataset import TabularDataset
from src.models.soil_regressor import SoilRegressor

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/soil_regression.yaml")
    parser.add_argument("--data_csv", type=str, required=True, help="path to CSV with features and targets")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    feature_cols = [f"feat_{i}" for i in range(cfg["input_features"])]  # adjust as needed
    target_cols = cfg["target_columns"]
    full_dataset = TabularDataset(args.data_csv, feature_cols, target_cols)
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_ds, val_ds = random_split(full_dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=16)

    model = SoilRegressor(
        input_dim=cfg["input_features"],
        output_dim=len(cfg["target_columns"]),
        hidden_dims=cfg["hidden_dims"],
        dropout=cfg["dropout"]
    )

    trainer = pl.Trainer(max_epochs=50, accelerator="auto", devices=1)
    trainer.fit(model, train_loader, val_loader)
    torch.save(model.state_dict(), "checkpoints/soil_regressor.pt")
    print("Model saved.")

if __name__ == "__main__":
    main()