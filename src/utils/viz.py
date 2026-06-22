import cv2
import numpy as np
import torch

def grad_cam(model, img_tensor, target_layer_name="encoder.blocks.3.norm2"):
    """
    Simple Grad‑CAM for grayscale image (1 channel).
    model: GAIAModel (LightningModule or nn.Module)
    img_tensor: (1, 1, H, W) tensor
    Returns heatmap (2D numpy array) upsampled to input size.
    """
    model.eval()
    # Hook the feature maps and gradients
    features = []
    gradients = []
    def forward_hook(module, input, output):
        features.append(output)
    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])

    # Find layer by name
    layer = dict(model.named_modules())[target_layer_name]
    f_handle = layer.register_forward_hook(forward_hook)
    b_handle = layer.register_full_backward_hook(backward_hook)

    output = model(img_tensor)
    class_idx = output.argmax(dim=1).item()
    model.zero_grad()
    output[0, class_idx].backward()

    f_handle.remove()
    b_handle.remove()

    # features[0] shape: (B, N, dim) from transformer; we need the patch tokens
    # For Conv-ViT, we must handle patch embedding. Simplified approach:
    # We'll use the grad for the whole encoder output.
    # Since TinyViT outputs (B, seq_len, dim), we take the non-cls tokens.
    patch_features = features[0][0, 1:, :]  # exclude CLS token
    patch_grads = gradients[0][0, 1:, :]
    weights = patch_grads.mean(dim=1, keepdim=True)  # global average pooling of grads
    cam = (weights * patch_features).sum(dim=1)  # (num_patches,)
    cam = cam.detach().cpu().numpy()
    cam = np.maximum(cam, 0)
    # Reshape to patch grid
    num_patches = cam.shape[0]
    patch_size = int(np.sqrt(num_patches))
    cam = cam.reshape(patch_size, patch_size)
    cam = cv2.resize(cam, (img_tensor.shape[2], img_tensor.shape[3]))
    cam = (cam - cam.min()) / (cam.max() + 1e-8)
    return cam