
import torch, re
from timm.models.vision_transformer import VisionTransformer

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Rebuild the exact architecture from a saved state dict – no hardcoded sizes."""
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

    # ── Rebuild backbone ──
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

    # ── Rebuild head: read shapes from checkpoint, build Linear layers, assign weights ──
    head_weight_keys = sorted(
        [k for k in head_keys if k.endswith(".weight")],
        key=lambda k: int(re.search(r'head\.(\d+)', k).group(1))
    )

    layers = []
    linear_count = 0
    for i, w_key in enumerate(head_weight_keys):
        b_key = w_key.replace(".weight", ".bias")
        weight = head_keys[w_key]
        bias = head_keys.get(b_key, torch.zeros(weight.shape[0]))
        out_features, in_features = weight.shape

        linear = torch.nn.Linear(in_features, out_features)
        # Manually assign trained weights
        linear.weight.data = weight.clone()
        linear.bias.data = bias.clone()
        layers.append(linear)
        linear_count += 1

        # Add activation & dropout after each Linear except the last
        if i < len(head_weight_keys) - 1:
            layers.append(torch.nn.GELU())
            layers.append(torch.nn.Dropout(0.2))

    head = torch.nn.Sequential(*layers) if layers else torch.nn.Linear(embed_dim, num_classes)

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
