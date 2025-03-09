"""
Setup script for the Lambda Creator package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lambda-creator",
    version="0.1.0",
    author="Devin AI",
    author_email="devin-ai-integration[bot]@users.noreply.github.com",
    description="A tool for creating AWS Lambda functions from ECR images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jianhuanggo/aws_create_lambda",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "boto3>=1.20.0",
        "botocore>=1.23.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lambda-creator=lambda_creator.cli:main",
        ],
    },
)
