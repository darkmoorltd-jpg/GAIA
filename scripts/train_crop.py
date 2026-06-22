import sys
import os
import argparse
import yaml
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytorch_lightning as pl
from src.models.gaia_model import GAIAModel
from src.data.loader import GAIADataModule

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str, required=True, help="crop name (cassava, maize, tomato)")
    parser.add_argument("--config", type=str, default=None, help="custom config file")
    args = parser.parse_args()

    # Load defaults
    with open("configs/defaults.yaml", "r") as f:
        defaults = yaml.safe_load(f)
    # Load crop specific config if exists
    crop_config_path = f"configs/{args.crop}.yaml"
    if os.path.exists(crop_config_path):
        with open(crop_config_path, "r") as f:
            crop_config = yaml.safe_load(f)
    else:
        raise FileNotFoundError(f"Config for {args.crop} not found at {crop_config_path}")

    num_classes = crop_config["num_classes"]
    class_names = crop_config.get("class_names", None)

    # Data module
    data_module = GAIADataModule(
        crop_name=args.crop,
        processed_dir=defaults["data"]["processed_dir"],
        batch_size=defaults["training"]["batch_size"],
        num_workers=defaults["training"]["num_workers"],
        image_size=defaults["model"]["image_size"]
    )

    # Model
    model = GAIAModel(
        num_classes=num_classes,
        lr=defaults["training"]["learning_rate"],
    )

    # Callbacks
    early_stop = pl.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=defaults["training"]["early_stop_patience"],
        mode="min"
    )
    checkpoint = pl.callbacks.ModelCheckpoint(
        dirpath=f"checkpoints/{args.crop}",
        filename="best-{epoch:02d}-{val_acc:.2f}",
        monitor="val_acc",
        mode="max",
        save_top_k=1
    )

    trainer = pl.Trainer(
        max_epochs=defaults["training"]["max_epochs"],
        accelerator="auto",
        devices=1,
        callbacks=[early_stop, checkpoint],
        log_every_n_steps=10,
    )

    trainer.fit(model, data_module)
    print(f"Training finished. Best model saved at: {checkpoint.best_model_path}")
    # Save the model state dict in standard format
    if checkpoint.best_model_path:
        best_model = GAIAModel.load_from_checkpoint(checkpoint.best_model_path)
        torch.save(best_model.state_dict(), f"checkpoints/{args.crop}/best_model.pt")
        print("Model state dict saved.")

if __name__ == "__main__":
    main()