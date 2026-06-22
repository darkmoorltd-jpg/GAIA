# GAIA – Global Agricultural Intelligence Assistant

GAIA diagnoses crop diseases from a photo.  
It uses a TinyViT transformer trained on African crops (cassava, maize, tomato, …).  

**Quickstart**  
1. Install dependencies: `pip install -r requirements.txt`  
2. Download datasets into `data/raw/cassava/` etc.  
3. Preprocess: `python scripts/preprocess_all.py`  
4. Train: `python scripts/train_crop.py --crop cassava`  
5. Launch app: `streamlit run app/main.py`

## Project Structure
- `src/` – core library (model, data, utils)
- `scripts/` – training, preprocessing, export
- `app/` – Streamlit web app
- `configs/` – YAML configuration per crop
- `notebooks/` – Colab ready experiments