# AWS Lambda Creator

A production-grade Python tool for creating and managing AWS Lambda functions from ECR images using the boto3 SDK.

## Overview

This tool provides a simple and efficient way to create AWS Lambda functions from ECR (Elastic Container Registry) images. It takes an ECR repository name and a Lambda function name as inputs, and creates a Lambda function with the appropriate execution role and permissions.

Key features:
- Create Lambda functions from ECR images
- Automatically create IAM roles with appropriate permissions
- Grant Lambda functions access to all S3 buckets
- Update existing Lambda functions
- Invoke Lambda functions
- Delete Lambda functions
- List Lambda functions

## Installation

### From Source

```bash
git clone https://github.com/jianhuanggo/aws_create_lambda.git
cd aws_create_lambda
pip install -e .
```

### Using pip

```bash
pip install git+https://github.com/jianhuanggo/aws_create_lambda.git
```

## Prerequisites

- Python 3.8 or higher
- AWS credentials configured (via `aws configure` or environment variables)
- An ECR repository with a Docker image for your Lambda function

## Usage

### Command Line Interface

The package provides a command-line interface for creating and managing Lambda functions:

```bash
# Create a Lambda function
lambda-creator --create --ecr-repo my-ecr-repo --lambda-name my-lambda-function

# Update a Lambda function
lambda-creator --update --ecr-repo my-ecr-repo --lambda-name my-lambda-function --memory 512 --timeout 60

# Invoke a Lambda function
lambda-creator --invoke --lambda-name my-lambda-function --payload '{"key": "value"}'

# Get information about a Lambda function
lambda-creator --get --lambda-name my-lambda-function

# Delete a Lambda function
lambda-creator --delete --lambda-name my-lambda-function

# List Lambda functions
lambda-creator --list
```

For more options, run:

```bash
lambda-creator --help
```

### Python API

You can also use the package as a Python library:

```python
from lambda_creator.lambda_creator import create_lambda_function

# Create a Lambda function
response = create_lambda_function(
    function_name='my-lambda-function',
    ecr_repository_name='my-ecr-repo',
    memory_size=256,
    timeout=60,
    description='My Lambda function'
)

print(f"Lambda function created: {response['FunctionName']}")
```

For more advanced usage, see the examples directory.

## Lambda Execution Role

By default, the tool creates a Lambda execution role with the following permissions:

- Basic Lambda execution permissions (CloudWatch Logs access)
- Full access to all S3 buckets

This ensures that your Lambda function can read from and write to any S3 bucket in your AWS account.

## Examples

The `examples` directory contains sample scripts that demonstrate how to use the package:

- `sample_usage.py`: A comprehensive example that demonstrates creating, updating, invoking, and deleting a Lambda function

To run the example:

```bash
python examples/sample_usage.py --ecr-repo my-ecr-repo --lambda-name my-lambda-function
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/jianhuanggo/aws_create_lambda.git
cd aws_create_lambda
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run unit tests
pytest tests/unit

# Run integration tests (requires AWS credentials)
pytest tests/integration

# Run all tests with coverage
pytest --cov=src
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
