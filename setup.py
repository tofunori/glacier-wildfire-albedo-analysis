from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="glacier-wildfire-albedo",
    version="0.1.0",
    author="Votre Nom",
    author_email="votre.email@universite.ca",
    description="Analyse de l'impact des feux de forêt sur l'albédo des glaciers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tofunori/glacier-wildfire-albedo-analysis",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "xarray>=0.19.0",
        "geopandas>=0.10.0",
        "matplotlib>=3.4.0",
    ],
    entry_points={
        "console_scripts": [
            "process-raqdps=scripts.process_raqdps:main",
            "generate-reports=scripts.generate_reports:main",
        ],
    },
)