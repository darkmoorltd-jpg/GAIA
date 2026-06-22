import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.utils.inference import load_model
import pytest

def test_load_model_missing():
    with pytest.raises(FileNotFoundError):
        load_model("nonexistent_crop")