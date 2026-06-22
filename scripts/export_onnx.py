import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import torch
import argparse
from src.models.gaia_model import GAIAModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--crop", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True, help="path to .ckpt or .pt")
    args = parser.parse_args()

    # Load model
    if args.checkpoint.endswith(".ckpt"):
        model = GAIAModel.load_from_checkpoint(args.checkpoint)
    else:
        # Load state dict from .pt
        with open(f"configs/{args.crop}.yaml", "r") as f:
            crop_config = yaml.safe_load(f)
        model = GAIAModel(num_classes=crop_config["num_classes"])
        model.load_state_dict(torch.load(args.checkpoint, map_location="cpu"))
    model.eval()
    dummy_input = torch.randn(1, 1, 224, 224)
    onnx_path = f"checkpoints/{args.crop}/gaia_{args.crop}.onnx"
    torch.onnx.export(model, dummy_input, onnx_path,
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch_size"},
                                    "output": {0: "batch_size"}})
    print(f"Exported ONNX model to {onnx_path}")

if __name__ == "__main__":
    main()