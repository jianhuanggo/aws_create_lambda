"""
Sample Usage of Lambda Creator

This script demonstrates how to use the Lambda Creator module to create and manage
AWS Lambda functions from ECR images. It showcases various operations including:
1. Creating a Lambda function from an ECR image
2. Updating a Lambda function
3. Invoking a Lambda function
4. Listing Lambda functions
5. Deleting a Lambda function

Usage:
    python sample_usage.py --ecr-repo <ecr_repo_name> --lambda-name <lambda_function_name> [--region <aws_region>]
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import the lambda_creator module
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lambda_creator.lambda_creator import LambdaCreator
from src.lambda_creator.lambda_role import create_lambda_role_with_s3_access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Create and manage AWS Lambda functions from ECR images')
    parser.add_argument('--ecr-repo', required=True, help='Name of the ECR repository')
    parser.add_argument('--lambda-name', required=True, help='Name of the Lambda function')
    parser.add_argument('--region', default=None, help='AWS region (default: use AWS configuration)')
    parser.add_argument('--profile', default='latest', help='AWS profile name to use (default: latest)')
    parser.add_argument('--image-tag', default='latest', help='ECR image tag (default: latest)')
    parser.add_argument('--memory', type=int, default=128, help='Lambda memory size in MB (default: 128)')
    parser.add_argument('--timeout', type=int, default=30, help='Lambda timeout in seconds (default: 30)')
    parser.add_argument('--operation', choices=['create', 'update', 'invoke', 'list', 'delete', 'all'],
                        default='create', help='Operation to perform (default: create)')
    parser.add_argument('--no-force-delete', action='store_false', dest='force_delete_existing',
                       help='Do not delete existing Lambda function with the same name')
    parser.add_argument('--payload', type=str, help='JSON payload for Lambda invocation')
    
    return parser.parse_args()


def create_lambda(creator: LambdaCreator, args) -> Dict[str, Any]:
    """Create a Lambda function from an ECR image."""
    logger.info(f"Creating Lambda function {args.lambda_name} from ECR repository {args.ecr_repo}")
    
    # Create a role with S3 access
    role_info = create_lambda_role_with_s3_access(region_name=args.region)
    role_name = role_info['RoleName']
    
    # Define environment variables
    env_vars = {
        'ENVIRONMENT': 'production',
        'LOG_LEVEL': 'INFO',
        'SOURCE_ECR_REPO': args.ecr_repo
    }
    
    # Define tags
    tags = {
        'Environment': 'production',
        'CreatedBy': 'LambdaCreator',
        'Source': 'ECR',
        'ECRRepository': args.ecr_repo
    }
    
    # Create the Lambda function
    response = creator.create_lambda_from_ecr(
        function_name=args.lambda_name,
        ecr_repository_name=args.ecr_repo,
        role_name=role_name,
        image_tag=args.image_tag,
        memory_size=args.memory,
        timeout=args.timeout,
        environment_variables=env_vars,
        description=f"Lambda function created from ECR repository {args.ecr_repo}",
        tags=tags,
        force_delete_existing=args.force_delete_existing
    )
    
    logger.info(f"Lambda function {args.lambda_name} created successfully")
    return response


def update_lambda(creator: LambdaCreator, args) -> Dict[str, Any]:
    """Update an existing Lambda function."""
    logger.info(f"Updating Lambda function {args.lambda_name}")
    
    # Define updated environment variables
    env_vars = {
        'ENVIRONMENT': 'production',
        'LOG_LEVEL': 'DEBUG',  # Changed from INFO to DEBUG
        'SOURCE_ECR_REPO': args.ecr_repo,
        'LAST_UPDATED': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Update the Lambda function
    response = creator.update_lambda_function(
        function_name=args.lambda_name,
        ecr_repository_name=args.ecr_repo,
        image_tag=args.image_tag,
        memory_size=args.memory,
        timeout=args.timeout,
        environment_variables=env_vars,
        description=f"Updated Lambda function from ECR repository {args.ecr_repo}"
    )
    
    logger.info(f"Lambda function {args.lambda_name} updated successfully")
    return response


def invoke_lambda(creator: LambdaCreator, args) -> Dict[str, Any]:
    """Invoke a Lambda function."""
    logger.info(f"Invoking Lambda function {args.lambda_name}")
    
    # Parse payload if provided
    payload = None
    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            sys.exit(1)
    else:
        # Default test payload
        payload = {
            "test": True,
            "message": "Hello from Lambda Creator",
            "timestamp": time.time()
        }
    
    # Invoke the Lambda function
    response = creator.invoke_lambda_function(
        function_name=args.lambda_name,
        payload=payload
    )
    
    # Process and display the response
    if 'ResponsePayload' in response:
        logger.info(f"Lambda function response: {response['ResponsePayload']}")
    else:
        logger.info(f"Lambda function invoked with status code: {response.get('StatusCode')}")
    
    return response


def list_lambdas(creator: LambdaCreator) -> Dict[str, Any]:
    """List Lambda functions."""
    logger.info("Listing Lambda functions")
    
    functions = creator.list_lambda_functions()
    
    logger.info(f"Found {len(functions)} Lambda functions")
    for i, function in enumerate(functions, 1):
        logger.info(f"{i}. {function['FunctionName']} - Runtime: {function.get('PackageType')} - Last Modified: {function.get('LastModified')}")
    
    return {"Functions": functions}


def delete_lambda(creator: LambdaCreator, args) -> Dict[str, Any]:
    """Delete a Lambda function."""
    logger.info(f"Deleting Lambda function {args.lambda_name}")
    
    response = creator.delete_lambda_function(args.lambda_name)
    
    logger.info(f"Lambda function {args.lambda_name} deleted successfully")
    return response


def run_all_operations(creator: LambdaCreator, args) -> None:
    """Run all Lambda operations in sequence."""
    try:
        # 1. Create Lambda function
        logger.info("=== Step 1: Creating Lambda function ===")
        create_response = create_lambda(creator, args)
        print_json_response(create_response)
        
        # Wait for Lambda to be fully created
        logger.info("Waiting for Lambda function to be fully created...")
        time.sleep(10)
        
        # 2. Get Lambda function details
        logger.info("\n=== Step 2: Getting Lambda function details ===")
        get_response = creator.get_lambda_function(args.lambda_name)
        print_json_response(get_response)
        
        # 3. Update Lambda function
        logger.info("\n=== Step 3: Updating Lambda function ===")
        update_response = update_lambda(creator, args)
        print_json_response(update_response)
        
        # Wait for Lambda to be fully updated
        logger.info("Waiting for Lambda function to be fully updated...")
        time.sleep(10)
        
        # 4. Invoke Lambda function
        logger.info("\n=== Step 4: Invoking Lambda function ===")
        invoke_response = invoke_lambda(creator, args)
        print_json_response(invoke_response)
        
        # 5. List Lambda functions
        logger.info("\n=== Step 5: Listing Lambda functions ===")
        list_response = list_lambdas(creator)
        # Don't print full response as it could be very large
        logger.info(f"Found {len(list_response['Functions'])} Lambda functions")
        
        # 6. Delete Lambda function
        logger.info("\n=== Step 6: Deleting Lambda function ===")
        delete_response = delete_lambda(creator, args)
        print_json_response(delete_response)
        
        logger.info("\n=== All operations completed successfully ===")
        
    except Exception as e:
        logger.error(f"Error during operations: {e}")
        sys.exit(1)


def print_json_response(response: Dict[str, Any]) -> None:
    """Print a JSON response in a readable format."""
    # Remove the Payload key if it's a StreamingBody object
    if 'Payload' in response and hasattr(response['Payload'], 'read'):
        del response['Payload']
    
    print(json.dumps(response, indent=2, default=str))


def main():
    """Main function to run the sample."""
    args = parse_arguments()
    
    try:
        # Create Lambda Creator instance
        creator = LambdaCreator(region_name=args.region, profile_name=args.profile)
        
        # Perform the requested operation
        if args.operation == 'create':
            response = create_lambda(creator, args)
            print_json_response(response)
        elif args.operation == 'update':
            response = update_lambda(creator, args)
            print_json_response(response)
        elif args.operation == 'invoke':
            response = invoke_lambda(creator, args)
            print_json_response(response)
        elif args.operation == 'list':
            response = list_lambdas(creator)
            # Don't print full response as it could be very large
            logger.info(f"Found {len(response['Functions'])} Lambda functions")
        elif args.operation == 'delete':
            response = delete_lambda(creator, args)
            print_json_response(response)
        elif args.operation == 'all':
            run_all_operations(creator, args)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
