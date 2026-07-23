
import torch
import re
from timm.models.vision_transformer import VisionTransformer

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Rebuild the exact architecture from a saved state dict, manually assigning head weights."""
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    # Split keys into backbone and head
    backbone_keys = {}
    head_keys = {}

    for k, v in state_dict.items():
        if k.startswith("head."):
            head_keys[k] = v
        else:
            clean = k.replace("backbone.", "", 1)
            backbone_keys[clean] = v

    # ── Rebuild backbone (unchanged) ──
    embed_dim = backbone_keys["cls_token"].shape[-1]
    pos_shape = backbone_keys["pos_embed"].shape
    num_patches = pos_shape[1] - 1
    grid_size = int(num_patches ** 0.5)
    img_size = grid_size * 16
    depth = len([k for k in backbone_keys if k.endswith(".norm1.weight")])
    qkv_w = backbone_keys["blocks.0.attn.qkv.weight"]
    num_heads = 6 if embed_dim == 384 else 3

    backbone = VisionTransformer(
        img_size=img_size, patch_size=16,
        embed_dim=embed_dim, depth=depth, num_heads=num_heads,
        num_classes=0, global_pool='token'
    )
    backbone.load_state_dict(backbone_keys, strict=False)

    # ── Rebuild head by reading saved shapes and manually assigning weights ──
    # Extract head layer indices and their weight shapes
    head_layers = []   # list of (index, weight, bias)
    for k, v in head_keys.items():
        if k.endswith(".weight"):
            idx = int(re.search(r'head\.(\d+)', k).group(1))
            bias_key = k.replace(".weight", ".bias")
            bias = head_keys.get(bias_key, torch.zeros(v.shape[0]))
            head_layers.append((idx, v, bias))

    # Sort by index (they should be consecutive in the Sequential)
    head_layers.sort(key=lambda x: x[0])

    # Build a Sequential with the exact same architecture
    sequential_layers = []
    linear_positions = []  # keep track of which positions are Linear layers
    for i, (orig_idx, weight, bias) in enumerate(head_layers):
        out_features, in_features = weight.shape
        linear = torch.nn.Linear(in_features, out_features)
        # Manually assign the saved weights
        linear.weight.data = weight.clone()
        linear.bias.data = bias.clone()
        sequential_layers.append(linear)
        linear_positions.append(len(sequential_layers) - 1)

        # Add GELU and Dropout after each Linear except the last one
        if i < len(head_layers) - 1:
            sequential_layers.append(torch.nn.GELU())
            sequential_layers.append(torch.nn.Dropout(0.2))

    head = torch.nn.Sequential(*sequential_layers)

    # ── Combine into FlexibleViT ──
    class FlexibleViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__()
            self.backbone = backbone
            self.head = head
        def forward(self, x):
            return self.head(self.backbone(x))

    model = FlexibleViT(backbone, head)
    model.eval()
    return model
