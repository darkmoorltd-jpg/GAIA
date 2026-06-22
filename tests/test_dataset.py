import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd
import tempfile
import numpy as np
from PIL import Image
from src.data.dataset import GAIAImageDataset

def test_dataset():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy data
        img_dir = os.path.join(tmpdir, "images")
        os.makedirs(img_dir)
        for i in range(10):
            img = Image.fromarray(np.random.randint(0, 255, (224, 224), dtype=np.uint8))
            img.save(os.path.join(img_dir, f"{i}.png"))
        df = pd.DataFrame({"image_path": [f"{i}.png" for i in range(10)], "label": np.random.randint(0, 2, 10)})
        csv_path = os.path.join(tmpdir, "test.csv")
        df.to_csv(csv_path, index=False)
        ds = GAIAImageDataset(csv_path, img_dir)
        assert len(ds) == 10
        img, label = ds[0]
        assert img.shape == (1, 224, 224)
        assert label in [0, 1]