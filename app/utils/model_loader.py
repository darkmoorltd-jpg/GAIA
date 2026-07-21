
import torch
import timm

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Load a model architecture that matches the checkpoint."""
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    # Detect embedding dimension and image size from the state dict
    if "backbone.cls_token" in state_dict:
        embed_dim = state_dict["backbone.cls_token"].shape[-1]
    elif "cls_token" in state_dict:
        embed_dim = state_dict["cls_token"].shape[-1]
    else:
        embed_dim = 192  # fallback

    # Detect image size from pos_embed
    if "backbone.pos_embed" in state_dict:
        num_patches = state_dict["backbone.pos_embed"].shape[1] - 1  # exclude CLS
    elif "pos_embed" in state_dict:
        num_patches = state_dict["pos_embed"].shape[1] - 1
    else:
        num_patches = 196  # fallback for 224×224

    # Determine patch size and image size
    # timm ViTs use 16×16 patches by default
    grid_size = int(num_patches ** 0.5)
    img_size = grid_size * 16  # 14 → 224, 24 → 384

    # Choose backbone based on image size and embedding dimension
    if img_size == 384 and embed_dim == 384:
        backbone = timm.create_model("vit_small_patch16_384", pretrained=False, num_classes=0)
    elif img_size == 224 and embed_dim == 384:
        backbone = timm.create_model("vit_small_patch16_224", pretrained=False, num_classes=0)
    elif img_size == 224 and embed_dim == 192:
        backbone = timm.create_model("vit_tiny_patch16_224", pretrained=False, num_classes=0)
    else:
        # Generic fallback: try to create a ViT with the detected parameters
        backbone = timm.create_model(
            f"vit_patch16_{img_size}",
            pretrained=False,
            num_classes=0,
            embed_dim=embed_dim
        )

    # Determine head structure from state dict keys
    # If there are keys like "head.0.weight", "head.3.weight", etc., it's a deep head
    head_keys = [k for k in state_dict.keys() if k.startswith("head.")]
    has_deep_head = any(".0.weight" in k for k in head_keys)

    if has_deep_head:
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
        # Simple linear head
        head = torch.nn.Linear(embed_dim, num_classes)

    class FlexibleViT(torch.nn.Module):
        def __init__(self, backbone, head):
            super().__init__()
            self.backbone = backbone
            self.head = head
        def forward(self, x):
            return self.head(self.backbone(x))

    model = FlexibleViT(backbone, head)
    model.load_state_dict(state_dict)
    model.eval()
    return model
