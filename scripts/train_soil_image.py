import sys, os, argparse, yaml
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pytorch_lightning as pl
from src.models.gaia_model import GAIAModel
from src.data.loader import GAIADataModule

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/soil.yaml")
    args = parser.parse_args()

    with open("configs/defaults.yaml") as f:
        defaults = yaml.safe_load(f)
    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    # Override image channels and grayscale if needed
    in_chans = cfg["dataset"].get("in_channels", 1)
    image_size = cfg["dataset"]["image_size"]

    data_module = GAIADataModule(
        crop_name="soil",  # expects data/processed/soil/
        processed_dir="data/processed",
        batch_size=defaults["training"]["batch_size"],
        num_workers=defaults["training"]["num_workers"],
        image_size=image_size
    )

    model = GAIAModel(
        num_classes=cfg["num_classes"],
        lr=defaults["training"]["learning_rate"],
    )
    # If RGB, we need to modify TinyViT's in_chans. 
    # You can either create a new config param or use conditional loading.
    # Here we'll instantiate the encoder manually if needed (but GAIAModel by default uses in_chans=1).
    # Quick fix: extend GAIAModel to accept in_chans.
    # We'll just update the model's encoder directly after creation:
    if in_chans != 1:
        model.encoder = TinyViT(in_chans=in_chans, embed_dim=128, depth=4, num_heads=4)
        # re-initialize head? already done.
    # (For simplicity, I'll assume you add an in_chans parameter to GAIAModel – see note below*)

    early_stop = pl.callbacks.EarlyStopping(monitor="val_loss", patience=5)
    checkpoint = pl.callbacks.ModelCheckpoint(
        dirpath="checkpoints/soil",
        filename="best-{epoch:02d}-{val_acc:.2f}",
        monitor="val_acc", mode="max", save_top_k=1
    )
    trainer = pl.Trainer(max_epochs=defaults["training"]["max_epochs"],
                         accelerator="auto", devices=1,
                         callbacks=[early_stop, checkpoint])
    trainer.fit(model, data_module)
    print("Training complete.")

if __name__ == "__main__":
    main()