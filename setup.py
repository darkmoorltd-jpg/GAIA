from setuptools import setup, find_packages

setup(
    name="gaia",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "torch",
        "pytorch-lightning",
        "torchvision",
        "opencv-python-headless",
        "pandas",
        "numpy",
        "PyYAML",
        "streamlit",
        "scikit-learn",
        "Pillow",
    ],
)