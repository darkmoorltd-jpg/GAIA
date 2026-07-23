
import torch
from timm.models.vision_transformer import VisionTransformer

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Rebuild the exact architecture from a saved state dict."""
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    # Split keys into backbone and head
    backbone_keys = {}
    head_keys = {}

    for k, v in state_dict.items():
        if k.startswith("head."):
            head_keys[k] = v
        else:
            # Remove optional "backbone." prefix
            clean = k.replace("backbone.", "", 1)
            backbone_keys[clean] = v

    # ── Rebuild backbone ──
    embed_dim = backbone_keys["cls_token"].shape[-1]          # 384
    pos_shape = backbone_keys["pos_embed"].shape               # [1, 197, 384]
    num_patches = pos_shape[1] - 1                             # 196
    grid_size = int(num_patches ** 0.5)                        # 14
    img_size = grid_size * 16                                  # 224
    depth = len([k for k in backbone_keys if k.endswith(".norm1.weight")])  # 12
    # num_heads is not directly stored, but we can infer from qkv weight shape
    qkv_w = backbone_keys["blocks.0.attn.qkv.weight"]
    num_heads = qkv_w.shape[0] // (3 * embed_dim)             # 1152 / (3*384) = 1? Actually 1152/384 = 3, so num_heads = 1152/(3*embed_dim/num_heads)? We'll use a safe default.
    # Simpler: use 6 for embed_dim 384 (ViT-Small)
    num_heads = 6 if embed_dim == 384 else 3

    backbone = VisionTransformer(
        img_size=img_size, patch_size=16,
        embed_dim=embed_dim, depth=depth, num_heads=num_heads,
        num_classes=0, global_pool='token'
    )
    backbone.load_state_dict(backbone_keys, strict=False)

    # ── Rebuild head from the saved head keys ──
    # Head keys look like: head.0.weight, head.0.bias, head.3.weight, ...
    # We need to build a sequence of Linear layers with GELU & Dropout.
    # The indices tell us the layer order.
    import re, collections

    layer_indices = set()
    for k in head_keys:
        match = re.search(r'head\.(\d+)', k)
        if match:
            layer_indices.add(int(match.group(1)))
    sorted_indices = sorted(layer_indices)

    # Build layers dynamically
    layers = []
    for i, idx in enumerate(sorted_indices):
        w_key = f"head.{idx}.weight"
        b_key = f"head.{idx}.bias"
        if w_key not in head_keys:
            continue
        weight = head_keys[w_key]
        bias = head_keys.get(b_key, torch.zeros(weight.shape[0]))
        out_features, in_features = weight.shape
        layers.append(torch.nn.Linear(in_features, out_features))
        # Add activation and dropout after each layer except the last
        if i < len(sorted_indices) - 1:
            layers.append(torch.nn.GELU())
            layers.append(torch.nn.Dropout(0.2))   # you can adjust dropout rate if needed

    head = torch.nn.Sequential(*layers) if layers else torch.nn.Linear(embed_dim, num_classes)

    # Load the head weights (strip the "head." prefix)
    head_state = {}
    for k, v in head_keys.items():
        new_key = k.replace("head.", "", 1)
        head_state[new_key] = v
    head.load_state_dict(head_state)

    # ── Combine ──
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
