from setuptools import setup, find_packages

setup(
    name="bpm-detector",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "soundfile>=0.12.1",
        "numpy>=1.24.3",
        "scipy>=1.11.3",
        "PyQt6>=6.7.0",
    ],
    entry_points={
        "console_scripts": [
            "bpm-detector=bpm_detector.cli:main",
            "bpm-detector-gui=bpm_detector.gui:main",
        ],
    },
    python_requires=">=3.7",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python package for detecting BPM in audio files using autocorrelation and energy flux methods",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="audio, music, bpm, beat detection, tempo detection",
    url="https://github.com/yourusername/bpm-detector",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 