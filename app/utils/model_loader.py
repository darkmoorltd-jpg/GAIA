
import torch
import timm

def create_model_from_checkpoint(checkpoint_path, num_classes):
    """Load a model architecture that matches the checkpoint."""
    state_dict = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    
    # Detect architecture from the state dict
    if "backbone.cls_token" in state_dict:
        embed_dim = state_dict["backbone.cls_token"].shape[-1]
    else:
        embed_dim = 192  # default to tiny

    # Determine which backbone to use
    if embed_dim == 384:
        # ViT-Small-384 with deep head
        backbone = timm.create_model("vit_small_patch16_384", pretrained=False, num_classes=0)
        # Reconstruct the head: 3 linear layers as used during training
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
        # ViT-Tiny-224 with simple head
        backbone = timm.create_model("vit_tiny_patch16_224", pretrained=False, num_classes=0)
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
