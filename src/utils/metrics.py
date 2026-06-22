from sklearn.metrics import classification_report, confusion_matrix
import torch
import numpy as np

def compute_metrics(y_true, y_pred, class_names=None):
    """Return classification report and confusion matrix."""
    if isinstance(y_true, torch.Tensor):
        y_true = y_true.cpu().numpy()
    if isinstance(y_pred, torch.Tensor):
        y_pred = y_pred.cpu().numpy()
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    cm = confusion_matrix(y_true, y_pred)
    return report, cm