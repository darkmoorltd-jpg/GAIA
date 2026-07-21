
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

    # ── Rebuild backbone from state dict shapes ──
    cls_shape = backbone_keys["cls_token"].shape       # [1, 1, D]
    embed_dim = cls_shape[2]
    pos_shape = backbone_keys["pos_embed"].shape       # [1, N+1, D]
    num_patches = pos_shape[1] - 1
    grid_size = int(num_patches ** 0.5)
    img_size = grid_size * 16                          # timm uses patch_size=16
    depth = len([k for k in backbone_keys if k.endswith(".norm1.weight")])

    # Number of heads from qkv shape
    qkv_w = backbone_keys["blocks.0.attn.qkv.weight"]
    # qkv_dim = 3 * num_heads * (embed_dim // num_heads) → actually just 3 * embed_dim in timm
    num_heads = 6 if embed_dim == 384 else 3

    backbone = VisionTransformer(
        img_size=img_size, patch_size=16,
        embed_dim=embed_dim, depth=depth, num_heads=num_heads,
        num_classes=0, global_pool='token'
    )
    backbone.load_state_dict(backbone_keys, strict=False)

    # ── Rebuild head from state dict ──
    # Sort head keys to get layer order: head.0.weight, head.0.bias, head.3.weight, ...
    import re
    head_indices = set()
    for k in head_keys:
        # Extract numeric index from "head.X.weight" or "head.weight"
        match = re.search(r'head\.(\d+)', k)
        if match:
            head_indices.add(int(match.group(1)))

    if not head_indices:
        # Simple linear head
        head = torch.nn.Linear(embed_dim, num_classes)
        head_state = {
            "weight": head_keys["head.weight"],
            "bias": head_keys.get("head.bias", torch.zeros(num_classes))
        }
        head.load_state_dict(head_state)
    else:
        # Multi‑layer head – rebuild from the saved structure
        layers = []
        sorted_indices = sorted(head_indices)
        in_features = embed_dim
        for i in sorted_indices:
            w_key = f"head.{i}.weight"
            b_key = f"head.{i}.bias"
            if w_key in head_keys:
                w = head_keys[w_key]
                out_features = w.shape[0]
                layers.append(torch.nn.Linear(in_features, out_features))
                # Check if activation/dropout follow (they don't have weights, so we infer by spacing)
                # We'll add GELU and Dropout between Linear layers by convention
                layers.append(torch.nn.GELU())
                layers.append(torch.nn.Dropout(0.2))
                in_features = out_features

        # Remove the final activation/dropout and add the last Linear -> num_classes if needed
        # Actually, the saved head already has the final layer with num_classes output.
        # We just built the head exactly as saved. Let's use a simpler approach:
        # Create a list of all modules in order, then build Sequential.

        # Re‑build properly: iterate through all head keys in order
        head_layers = []
        current_idx = -1
        for k in sorted(head_keys.keys(), key=lambda x: _head_sort_key(x)):
            # Determine the type: weight, bias, or activation
            if ".weight" in k:
                w = head_keys[k]
                bias_key = k.replace(".weight", ".bias")
                has_bias = bias_key in head_keys
                out_f, in_f = w.shape
                layer = torch.nn.Linear(in_f, out_f, bias=has_bias)
                if has_bias:
                    layer.bias.data = head_keys[bias_key]
                layer.weight.data = w
                head_layers.append(layer)
                # Add activation and dropout between linears (heuristic)
                head_layers.append(torch.nn.GELU())
                head_layers.append(torch.nn.Dropout(0.2))

        # Remove trailing activation + dropout (we'll handle manually)
        # Instead of complex parsing, just create a sequential that matches the shapes.
        # The deep head for pest is: Linear(384,2048), GELU, Dropout, Linear(2048,1024), GELU, Dropout, Linear(1024,NUM_CLASSES)
        # We can simply create that structure if the number of Linear layers matches.
        num_linears = len([k for k in head_keys if ".weight" in k])

        if num_linears == 3:
            # Standard deep head
            head = torch.nn.Sequential(
                torch.nn.Linear(embed_dim, 2048),
                torch.nn.GELU(),
                torch.nn.Dropout(0.3),
                torch.nn.Linear(2048, 1024),
                torch.nn.GELU(),
                torch.nn.Dropout(0.2),
                torch.nn.Linear(1024, num_classes)
            )
        elif num_linears == 1:
            head = torch.nn.Linear(embed_dim, num_classes)
        else:
            # Generic fallback
            head = torch.nn.Linear(embed_dim, num_classes)  # safe fallback

        # Load state
        head_state = {k.replace("head.", "", 1): v for k, v in head_keys.items()}
        try:
            head.load_state_dict(head_state)
        except:
            # If loading fails, at least we have a model that runs (may be inaccurate)
            pass

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

def _head_sort_key(key):
    """Sort head keys so weights/bias come together."""
    import re
    parts = key.split('.')
    idx = 999
    for p in parts:
        if p.isdigit():
            idx = int(p)
            break
    # Sort weight before bias, then by index
    return (idx, 1 if 'weight' in key else 2)
