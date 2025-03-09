"""
Command Line Interface for Lambda Creator

This module provides a command-line interface for creating and managing
AWS Lambda functions from ECR images.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any, Optional

from .lambda_creator import LambdaCreator, create_lambda_function
from .lambda_role import create_lambda_role_with_s3_access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Create and manage AWS Lambda functions from ECR images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--ecr-repo', required=True,
                        help='Name of the ECR repository containing the Docker image')
    parser.add_argument('--lambda-name', required=True,
                        help='Name of the Lambda function to create or manage')
    
    # Optional arguments
    parser.add_argument('--region', default=None,
                        help='AWS region (default: use AWS configuration)')
    parser.add_argument('--profile', default='latest',
                        help='AWS profile name to use')
    parser.add_argument('--role-name', default=None,
                        help='Name of an existing IAM role to use (default: create a new role)')
    parser.add_argument('--image-tag', default='latest',
                        help='ECR image tag to use')
    parser.add_argument('--memory', type=int, default=128,
                        help='Memory size for the Lambda function in MB')
    parser.add_argument('--timeout', type=int, default=30,
                        help='Timeout for the Lambda function in seconds')
    parser.add_argument('--description', default='',
                        help='Description of the Lambda function')
    parser.add_argument('--env-vars', default=None,
                        help='Environment variables for the Lambda function in JSON format')
    parser.add_argument('--tags', default=None,
                        help='Tags to attach to the Lambda function in JSON format')
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--create', action='store_true',
                             help='Create a new Lambda function')
    parser.add_argument('--no-force-delete', action='store_false', dest='force_delete_existing',
                       help='Do not delete existing Lambda function with the same name')
    action_group.add_argument('--update', action='store_true',
                             help='Update an existing Lambda function')
    action_group.add_argument('--delete', action='store_true',
                             help='Delete a Lambda function')
    action_group.add_argument('--invoke', action='store_true',
                             help='Invoke a Lambda function')
    action_group.add_argument('--get', action='store_true',
                             help='Get information about a Lambda function')
    action_group.add_argument('--list', action='store_true',
                             help='List Lambda functions')
    
    # Invoke arguments
    parser.add_argument('--payload', default=None,
                        help='JSON payload for Lambda invocation')
    parser.add_argument('--invocation-type', default='RequestResponse',
                        choices=['RequestResponse', 'Event', 'DryRun'],
                        help='Type of Lambda invocation')
    
    # Output format
    parser.add_argument('--output', default='json',
                        choices=['json', 'text'],
                        help='Output format')
    
    return parser.parse_args()


def parse_json_arg(json_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """Parse a JSON string argument."""
    if not json_str:
        return None
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        sys.exit(1)


def format_output(data: Dict[str, Any], output_format: str) -> None:
    """Format and print the output data."""
    if output_format == 'json':
        # Remove StreamingBody objects which can't be serialized
        if 'Payload' in data and hasattr(data['Payload'], 'read'):
            del data['Payload']
        
        print(json.dumps(data, indent=2, default=str))
    else:  # text format
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            elif isinstance(value, list):
                print(f"{key}:")
                for i, item in enumerate(value, 1):
                    if isinstance(item, dict):
                        print(f"  {i}.")
                        for k, v in item.items():
                            print(f"    {k}: {v}")
                    else:
                        print(f"  {i}. {item}")
            else:
                print(f"{key}: {value}")


def create_lambda(args) -> Dict[str, Any]:
    """Create a Lambda function from an ECR image."""
    logger.info(f"Creating Lambda function {args.lambda_name} from ECR repository {args.ecr_repo}")
    
    # Parse environment variables and tags
    env_vars = parse_json_arg(args.env_vars)
    tags = parse_json_arg(args.tags)
    
    # Create the Lambda function
    response = create_lambda_function(
        function_name=args.lambda_name,
        ecr_repository_name=args.ecr_repo,
        region_name=args.region,
        profile_name=args.profile,
        role_name=args.role_name,
        image_tag=args.image_tag,
        memory_size=args.memory,
        timeout=args.timeout,
        environment_variables=env_vars,
        description=args.description,
        tags=tags,
        force_delete_existing=args.force_delete_existing
    )
    
    logger.info(f"Lambda function {args.lambda_name} created successfully")
    return response


def update_lambda(args) -> Dict[str, Any]:
    """Update an existing Lambda function."""
    logger.info(f"Updating Lambda function {args.lambda_name}")
    
    # Parse environment variables
    env_vars = parse_json_arg(args.env_vars)
    
    # Create Lambda Creator instance
    creator = LambdaCreator(region_name=args.region, profile_name=args.profile)
    
    # Update the Lambda function
    response = creator.update_lambda_function(
        function_name=args.lambda_name,
        ecr_repository_name=args.ecr_repo,
        image_tag=args.image_tag,
        memory_size=args.memory,
        timeout=args.timeout,
        environment_variables=env_vars,
        description=args.description
    )
    
    logger.info(f"Lambda function {args.lambda_name} updated successfully")
    return response


def delete_lambda(args) -> Dict[str, Any]:
    """Delete a Lambda function."""
    logger.info(f"Deleting Lambda function {args.lambda_name}")
    
    # Create Lambda Creator instance
    creator = LambdaCreator(region_name=args.region, profile_name=args.profile)
    
    # Delete the Lambda function
    response = creator.delete_lambda_function(args.lambda_name)
    
    logger.info(f"Lambda function {args.lambda_name} deleted successfully")
    return response


def invoke_lambda(args) -> Dict[str, Any]:
    """Invoke a Lambda function."""
    logger.info(f"Invoking Lambda function {args.lambda_name}")
    
    # Parse payload
    payload = parse_json_arg(args.payload)
    
    # Create Lambda Creator instance
    creator = LambdaCreator(region_name=args.region, profile_name=args.profile)
    
    # Invoke the Lambda function
    response = creator.invoke_lambda_function(
        function_name=args.lambda_name,
        payload=payload,
        invocation_type=args.invocation_type
    )
    
    logger.info(f"Lambda function {args.lambda_name} invoked successfully")
    return response


def get_lambda(args) -> Dict[str, Any]:
    """Get information about a Lambda function."""
    logger.info(f"Getting information for Lambda function {args.lambda_name}")
    
    # Create Lambda Creator instance
    creator = LambdaCreator(region_name=args.region, profile_name=args.profile)
    
    # Get the Lambda function
    response = creator.get_lambda_function(args.lambda_name)
    
    return response


def list_lambdas(args) -> Dict[str, Any]:
    """List Lambda functions."""
    logger.info("Listing Lambda functions")
    
    # Create Lambda Creator instance
    creator = LambdaCreator(region_name=args.region, profile_name=args.profile)
    
    # List Lambda functions
    functions = creator.list_lambda_functions()
    
    return {"Functions": functions}


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    try:
        # Perform the requested action
        if args.create:
            response = create_lambda(args)
        elif args.update:
            response = update_lambda(args)
        elif args.delete:
            response = delete_lambda(args)
        elif args.invoke:
            response = invoke_lambda(args)
        elif args.get:
            response = get_lambda(args)
        elif args.list:
            response = list_lambdas(args)
        else:
            logger.error("No action specified")
            sys.exit(1)
        
        # Format and print the output
        format_output(response, args.output)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
