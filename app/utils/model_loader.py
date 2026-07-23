
import torch
from timm.models.vision_transformer import VisionTransformer

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Rebuild the exact architecture from a saved state dict."""
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    # ── Separate backbone and head keys ──
    backbone_state = {}
    head_state = {}

    for k, v in state_dict.items():
        if k.startswith("head."):
            head_state[k.replace("head.", "", 1)] = v
        else:
            # Strip optional "backbone." prefix
            clean = k.replace("backbone.", "", 1)
            backbone_state[clean] = v

    # ── Detect backbone architecture from shapes ──
    cls_shape = backbone_state["cls_token"].shape       # [1, 1, D]
    embed_dim = cls_shape[2]
    pos_shape = backbone_state["pos_embed"].shape       # [1, N+1, D]
    num_patches = pos_shape[1] - 1
    grid_size = int(num_patches ** 0.5)
    img_size = grid_size * 16                          # patch_size=16
    depth = len([k for k in backbone_state if k.endswith(".norm1.weight")])
    num_heads = 6 if embed_dim == 384 else 3

    backbone = VisionTransformer(
        img_size=img_size, patch_size=16,
        embed_dim=embed_dim, depth=depth, num_heads=num_heads,
        num_classes=0, global_pool='token'
    )
    backbone.load_state_dict(backbone_state, strict=False)

    # ── Rebuild head ──
    # Count linear layers in head_state
    weight_keys = sorted([k for k in head_state if k.endswith(".weight")])

    if len(weight_keys) == 1:
        # Simple linear head
        head = torch.nn.Linear(embed_dim, num_classes)
        head.load_state_dict({
            "weight": head_state["weight"],
            "bias": head_state.get("bias", torch.zeros(num_classes))
        }, strict=False)
    else:
        # Deep head – rebuild from the saved structure
        layers = []
        in_features = embed_dim
        for w_key in weight_keys:
            b_key = w_key.replace(".weight", ".bias")
            w = head_state[w_key]
            out_features = w.shape[0]
            layer = torch.nn.Linear(in_features, out_features)
            layer.weight.data = w
            if b_key in head_state:
                layer.bias.data = head_state[b_key]
            layers.append(layer)
            layers.append(torch.nn.GELU())
            layers.append(torch.nn.Dropout(0.2))
            in_features = out_features
        # Remove trailing activation+dropout
        layers = layers[:-2]
        head = torch.nn.Sequential(*layers)

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
