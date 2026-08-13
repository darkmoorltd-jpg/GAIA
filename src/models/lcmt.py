
import torch
import torch.nn as nn
import torch.nn.functional as F
import timm

class MultiScaleFeaturePyramid(nn.Module):
    def __init__(self, embed_dim=384):
        super().__init__()
        self.scale1 = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.scale2 = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)
        self.scale3 = timm.create_model('vit_small_patch16_224', pretrained=False, num_classes=0)

    def forward(self, x):
        B, C, H, W = x.shape
        f1 = self.scale1.forward_features(x)[:, 0, :]
        crop112 = x[:, :, H//4:3*H//4, W//4:3*W//4]
        x112 = F.interpolate(crop112, size=(224, 224), mode='bilinear', align_corners=False)
        f2 = self.scale2.forward_features(x112)[:, 0, :]
        crop56 = x[:, :, 3*H//8:5*H//8, 3*W//8:5*W//8]
        x56 = F.interpolate(crop56, size=(224, 224), mode='bilinear', align_corners=False)
        f3 = self.scale3.forward_features(x56)[:, 0, :]
        return torch.cat([f1, f2, f3], dim=1)

class LesionDetector(nn.Module):
    def __init__(self, embed_dim=384):
        super().__init__()
        self.lesion_detector = nn.Sequential(nn.Linear(embed_dim, 256), nn.GELU(), nn.Linear(256, 1))
        self.lesion_counter = nn.Sequential(nn.Linear(embed_dim, 128), nn.GELU(), nn.Linear(128, 1))
    def forward(self, patch_tokens):
        lesion_probs = torch.sigmoid(self.lesion_detector(patch_tokens))
        lesion_features = patch_tokens * lesion_probs
        lesion_global = lesion_features.mean(dim=1)
        lesion_count = self.lesion_counter(lesion_global)
        return lesion_global, lesion_probs.squeeze(-1), lesion_count.squeeze(-1)

class LesionCentricAttention(nn.Module):
    def __init__(self, embed_dim=384):
        super().__init__()
        self.query = nn.Linear(embed_dim, 128)
        self.key = nn.Linear(embed_dim, 128)
        self.value = nn.Linear(embed_dim, 128)
    def forward(self, lesion_features, healthy_features):
        q = self.query(lesion_features)
        k = self.key(healthy_features)
        v = self.value(healthy_features)
        scores = torch.bmm(q.unsqueeze(1), k.transpose(1, 2)) / (128 ** 0.5)
        attn_weights = F.softmax(scores, dim=-1)
        attended = torch.bmm(attn_weights, v).squeeze(1)
        return attended

class LCMT(nn.Module):
    def __init__(self, num_classes=7):
        super().__init__()
        self.pyramid = MultiScaleFeaturePyramid()
        self.lesion_detector = LesionDetector()
        self.attention = LesionCentricAttention()
        self.classifier = nn.Sequential(
            nn.Linear(1152 + 384 + 128, 1024),
            nn.GELU(), nn.Dropout(0.3),
            nn.Linear(1024, 512),
            nn.GELU(), nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
        self.severity_predictor = nn.Sequential(
            nn.Linear(1152 + 384 + 128, 256),
            nn.GELU(),
            nn.Linear(256, 1)
        )
    def forward(self, x):
        multi_scale = self.pyramid(x)
        patch_tokens = self.pyramid.scale1.forward_features(x)[:, 1:, :]
        lesion_global, lesion_probs, lesion_count = self.lesion_detector(patch_tokens)
        attended = self.attention(lesion_global, patch_tokens)
        combined = torch.cat([multi_scale, lesion_global, attended], dim=1)
        logits = self.classifier(combined)
        severity = self.severity_predictor(combined)
        return {
            'logits': logits,
            'lesion_probs': lesion_probs,
            'lesion_count': lesion_count,
            'severity': severity
        }
