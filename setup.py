from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rctx",
    version="0.8.0",
    author="Volod Isai",
    author_email="volod.isai@gmail.com",
    description="A tool to stringify code using rsync and manage presets, forked from rstring.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/noreff/rctx",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "rctx=rctx.cli:main",
        ],
    },
    install_requires=[
        "colorama>=0.4.6",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        'dev': ['pytest>=8.3.2'],
    },
    package_data={
        "rctx": ["default_presets.yaml"],
    },
    include_package_data=True,
)