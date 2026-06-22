import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import torch
from src.models.gaia_model import GAIAModel

def test_forward():
    model = GAIAModel(num_classes=5)
    x = torch.randn(2, 1, 224, 224)
    out = model(x)
    assert out.shape == (2, 5)

def test_training_step():
    model = GAIAModel(num_classes=5)
    x = torch.randn(2, 1, 224, 224)
    y = torch.randint(0, 5, (2,))
    loss = model.training_step((x, y), 0)
    assert loss is not None