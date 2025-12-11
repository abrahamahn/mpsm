"""Setup configuration for MPSM - Music Production Software Manager."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

# Separate dev dependencies
dev_requirements = [
    req for req in requirements
    if any(pkg in req for pkg in ['pytest', 'black', 'mypy', 'pylint'])
]
install_requirements = [
    req for req in requirements
    if req not in dev_requirements
]

setup(
    name="mpsm",
    version="1.0.0",
    author="Abraham Ahn",
    author_email="your.email@example.com",
    description="Music Production Software Manager - Automate VST plugin management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abrahamahn/mpsm",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.9",
    install_requires=install_requirements,
    extras_require={
        "dev": dev_requirements,
    },
    entry_points={
        "console_scripts": [
            "mpsm=mpsm:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "src": [
            "config/defaults.yaml",
            "data/vendors.yaml",
        ],
    },
    zip_safe=False,
)
