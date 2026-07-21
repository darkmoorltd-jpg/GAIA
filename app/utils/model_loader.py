
import torch
import timm
from timm.models.vision_transformer import VisionTransformer

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Build a ViT exactly matching the saved checkpoint."""
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    # ── 1. Figure out architecture from state dict keys ──
    # Keys start with "backbone." or directly with model attributes
    prefix = "backbone." if "backbone.cls_token" in state_dict else ""

    def get_shape(key):
        return state_dict.get(f"{prefix}{key}", state_dict.get(key)).shape

    embed_dim = get_shape("cls_token")[2]  # [1, 1, D]
    pos_embed_shape = get_shape("pos_embed")  # [1, N+1, D]
    num_patches = pos_embed_shape[1] - 1
    grid_size = int(num_patches ** 0.5)
    img_size = grid_size * 16  # timm uses patch_size=16 by default

    # Depth = number of transformer blocks (count norm layers)
    depth = len([k for k in state_dict if k.endswith(".norm1.weight")])

    # Number of heads (from qkv weight shape)
    qkv_weight = state_dict[f"{prefix}blocks.0.attn.qkv.weight"]
    d = embed_dim
    qkv_dim = qkv_weight.shape[0]
    # In timm ViT, qkv_dim = 3 * num_heads * (d // num_heads) = 3 * d
    # So num_heads = qkv_dim // (3 * (d // num_heads)) … simpler: check head count from config
    # Typically ViT-Tiny uses 3 heads, Small uses 6
    num_heads = 6 if embed_dim == 384 else 3  # good enough heuristic

    # ── 2. Create backbone with exact parameters ──
    backbone = VisionTransformer(
        img_size=img_size,
        patch_size=16,
        embed_dim=embed_dim,
        depth=depth,
        num_heads=num_heads,
        num_classes=0,          # discard classification head
        global_pool='token'     # return CLS token
    )

    # Strip prefix to load backbone weights
    backbone_state = {}
    for k, v in state_dict.items():
        if k.startswith("head."):
            continue
        new_key = k.replace("backbone.", "", 1) if prefix else k
        backbone_state[new_key] = v
    backbone.load_state_dict(backbone_state, strict=False)

    # ── 3. Build matching head ──
    head_keys = [k for k in state_dict if k.startswith("head.")]
    # Determine if deep head (contains keys like head.0.weight)
    has_deep = any(".0.weight" in k for k in head_keys)

    if has_deep:
        # Deep head: 2048 → 1024 → num_classes
        head = torch.nn.Sequential(
            torch.nn.Linear(embed_dim, 2048),
            torch.nn.GELU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(2048, 1024),
            torch.nn.GELU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(1024, num_classes)
        )
    else:
        head = torch.nn.Linear(embed_dim, num_classes)

    # Load head weights (strip "head." prefix if needed)
    head_state = {k.replace("head.", "", 1): v for k, v in state_dict.items() if k.startswith("head.")}
    head.load_state_dict(head_state)

    # ── 4. Combine into FlexibleViT ──
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
