"""
Lambda Creator Module

This module provides functionality to create AWS Lambda functions from ECR images.
It uses boto3 SDK to interact with AWS services.
"""

import logging
import time
from typing import Dict, Optional, Any, List, Union

import boto3
from botocore.exceptions import ClientError

from .lambda_role import create_lambda_role, attach_s3_policy

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class LambdaCreator:
    """
    A class to create and manage AWS Lambda functions from ECR images.
    """

    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize the LambdaCreator with AWS region.

        Args:
            region_name: AWS region name. If None, uses the default region from AWS configuration.
        """
        self.region_name = region_name
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.ecr_client = boto3.client('ecr', region_name=region_name)
        self.iam_client = boto3.client('iam', region_name=region_name)

    def create_lambda_from_ecr(
        self,
        function_name: str,
        ecr_repository_name: str,
        role_name: Optional[str] = None,
        image_tag: str = 'latest',
        memory_size: int = 128,
        timeout: int = 30,
        environment_variables: Optional[Dict[str, str]] = None,
        description: str = '',
        tags: Optional[Dict[str, str]] = None,
        vpc_config: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Create a Lambda function from an ECR image.

        Args:
            function_name: Name of the Lambda function
            ecr_repository_name: Name of the ECR repository
            role_name: Name of the IAM role to use. If None, creates a new role.
            image_tag: Tag of the ECR image to use
            memory_size: Memory size for the Lambda function in MB
            timeout: Timeout for the Lambda function in seconds
            environment_variables: Environment variables for the Lambda function
            description: Description of the Lambda function
            tags: Tags to attach to the Lambda function
            vpc_config: VPC configuration for the Lambda function

        Returns:
            Dict containing information about the created Lambda function
        """
        try:
            # Get ECR repository URI
            ecr_repo_uri = self._get_ecr_repository_uri(ecr_repository_name)
            if not ecr_repo_uri:
                raise ValueError(f"ECR repository {ecr_repository_name} not found")

            # Create or get IAM role
            if role_name:
                role_arn = self._get_role_arn(role_name)
                if not role_arn:
                    raise ValueError(f"IAM role {role_name} not found")
            else:
                # Create a new role with a name based on the function name
                generated_role_name = f"{function_name}-role-{int(time.time())}"
                role_arn = create_lambda_role(self.iam_client, generated_role_name)
                # Attach S3 full access policy
                attach_s3_policy(self.iam_client, generated_role_name)
                # Wait for role to propagate
                logger.info(f"Waiting for role {generated_role_name} to propagate...")
                time.sleep(10)

            # Prepare environment variables
            environment = {'Variables': environment_variables} if environment_variables else None

            # Prepare tags
            lambda_tags = tags or {}

            # Create Lambda function
            image_uri = f"{ecr_repo_uri}:{image_tag}"
            logger.info(f"Creating Lambda function {function_name} from image {image_uri}")
            
            create_params = {
                'FunctionName': function_name,
                'Role': role_arn,
                'PackageType': 'Image',
                'Code': {
                    'ImageUri': image_uri
                },
                'Description': description,
                'Timeout': timeout,
                'MemorySize': memory_size,
                'Tags': lambda_tags
            }
            
            if environment:
                create_params['Environment'] = environment
                
            if vpc_config:
                create_params['VpcConfig'] = vpc_config

            response = self.lambda_client.create_function(**create_params)
            
            logger.info(f"Lambda function {function_name} created successfully")
            return response
            
        except ClientError as e:
            logger.error(f"Error creating Lambda function: {e}")
            raise

    def update_lambda_function(
        self,
        function_name: str,
        ecr_repository_name: Optional[str] = None,
        image_tag: str = 'latest',
        role_arn: Optional[str] = None,
        memory_size: Optional[int] = None,
        timeout: Optional[int] = None,
        environment_variables: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
        vpc_config: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing Lambda function.

        Args:
            function_name: Name of the Lambda function to update
            ecr_repository_name: Name of the ECR repository (if updating the image)
            image_tag: Tag of the ECR image to use (if updating the image)
            role_arn: ARN of the IAM role to use (if updating the role)
            memory_size: Memory size for the Lambda function in MB
            timeout: Timeout for the Lambda function in seconds
            environment_variables: Environment variables for the Lambda function
            description: Description of the Lambda function
            vpc_config: VPC configuration for the Lambda function

        Returns:
            Dict containing information about the updated Lambda function
        """
        try:
            update_params = {
                'FunctionName': function_name
            }
            
            # Update image if ECR repository name is provided
            if ecr_repository_name:
                ecr_repo_uri = self._get_ecr_repository_uri(ecr_repository_name)
                if not ecr_repo_uri:
                    raise ValueError(f"ECR repository {ecr_repository_name} not found")
                
                image_uri = f"{ecr_repo_uri}:{image_tag}"
                update_params['ImageUri'] = image_uri
                
                # Use update_function_code for image updates
                logger.info(f"Updating Lambda function {function_name} image to {image_uri}")
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ImageUri=image_uri
                )
            
            # Prepare configuration update parameters
            config_update = {}
            
            if role_arn:
                config_update['Role'] = role_arn
                
            if memory_size:
                config_update['MemorySize'] = memory_size
                
            if timeout:
                config_update['Timeout'] = timeout
                
            if environment_variables:
                config_update['Environment'] = {'Variables': environment_variables}
                
            if description:
                config_update['Description'] = description
                
            if vpc_config:
                config_update['VpcConfig'] = vpc_config
                
            # Update function configuration if there are configuration changes
            if config_update:
                logger.info(f"Updating Lambda function {function_name} configuration")
                response = self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    **config_update
                )
                return response
            
            # If only the image was updated, get the function details
            return self.get_lambda_function(function_name)
            
        except ClientError as e:
            logger.error(f"Error updating Lambda function: {e}")
            raise

    def delete_lambda_function(self, function_name: str) -> Dict[str, Any]:
        """
        Delete a Lambda function.

        Args:
            function_name: Name of the Lambda function to delete

        Returns:
            Dict containing the response from the delete operation
        """
        try:
            logger.info(f"Deleting Lambda function {function_name}")
            response = self.lambda_client.delete_function(FunctionName=function_name)
            logger.info(f"Lambda function {function_name} deleted successfully")
            return response
        except ClientError as e:
            logger.error(f"Error deleting Lambda function: {e}")
            raise

    def get_lambda_function(self, function_name: str) -> Dict[str, Any]:
        """
        Get information about a Lambda function.

        Args:
            function_name: Name of the Lambda function

        Returns:
            Dict containing information about the Lambda function
        """
        try:
            logger.info(f"Getting information for Lambda function {function_name}")
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response
        except ClientError as e:
            logger.error(f"Error getting Lambda function information: {e}")
            raise

    def invoke_lambda_function(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        invocation_type: str = 'RequestResponse'
    ) -> Dict[str, Any]:
        """
        Invoke a Lambda function.

        Args:
            function_name: Name of the Lambda function to invoke
            payload: Payload to send to the Lambda function
            invocation_type: Type of invocation (RequestResponse, Event, DryRun)

        Returns:
            Dict containing the response from the invocation
        """
        import json
        
        try:
            logger.info(f"Invoking Lambda function {function_name}")
            
            invoke_params = {
                'FunctionName': function_name,
                'InvocationType': invocation_type
            }
            
            if payload:
                invoke_params['Payload'] = json.dumps(payload).encode()
                
            response = self.lambda_client.invoke(**invoke_params)
            
            # Parse the response payload if it exists
            if 'Payload' in response:
                response_payload = response['Payload'].read().decode('utf-8')
                if response_payload:
                    try:
                        response['ResponsePayload'] = json.loads(response_payload)
                    except json.JSONDecodeError:
                        response['ResponsePayload'] = response_payload
                        
            return response
            
        except ClientError as e:
            logger.error(f"Error invoking Lambda function: {e}")
            raise

    def list_lambda_functions(self, max_items: int = 50) -> List[Dict[str, Any]]:
        """
        List Lambda functions.

        Args:
            max_items: Maximum number of functions to list

        Returns:
            List of dictionaries containing information about Lambda functions
        """
        try:
            logger.info("Listing Lambda functions")
            paginator = self.lambda_client.get_paginator('list_functions')
            
            functions = []
            for page in paginator.paginate(MaxItems=max_items):
                functions.extend(page.get('Functions', []))
                
            return functions
            
        except ClientError as e:
            logger.error(f"Error listing Lambda functions: {e}")
            raise

    def _get_ecr_repository_uri(self, repository_name: str) -> Optional[str]:
        """
        Get the URI of an ECR repository.

        Args:
            repository_name: Name of the ECR repository

        Returns:
            URI of the ECR repository or None if not found
        """
        try:
            response = self.ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            repositories = response.get('repositories', [])
            
            if repositories:
                return repositories[0].get('repositoryUri')
            return None
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                logger.error(f"ECR repository {repository_name} not found")
                return None
            logger.error(f"Error getting ECR repository URI: {e}")
            raise

    def _get_role_arn(self, role_name: str) -> Optional[str]:
        """
        Get the ARN of an IAM role.

        Args:
            role_name: Name of the IAM role

        Returns:
            ARN of the IAM role or None if not found
        """
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            return response.get('Role', {}).get('Arn')
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                logger.error(f"IAM role {role_name} not found")
                return None
            logger.error(f"Error getting IAM role ARN: {e}")
            raise


def create_lambda_function(
    function_name: str,
    ecr_repository_name: str,
    region_name: Optional[str] = None,
    role_name: Optional[str] = None,
    image_tag: str = 'latest',
    memory_size: int = 128,
    timeout: int = 30,
    environment_variables: Optional[Dict[str, str]] = None,
    description: str = '',
    tags: Optional[Dict[str, str]] = None,
    vpc_config: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Any]:
    """
    Create a Lambda function from an ECR image (convenience function).

    Args:
        function_name: Name of the Lambda function
        ecr_repository_name: Name of the ECR repository
        region_name: AWS region name
        role_name: Name of the IAM role to use
        image_tag: Tag of the ECR image to use
        memory_size: Memory size for the Lambda function in MB
        timeout: Timeout for the Lambda function in seconds
        environment_variables: Environment variables for the Lambda function
        description: Description of the Lambda function
        tags: Tags to attach to the Lambda function
        vpc_config: VPC configuration for the Lambda function

    Returns:
        Dict containing information about the created Lambda function
    """
    creator = LambdaCreator(region_name=region_name)
    return creator.create_lambda_from_ecr(
        function_name=function_name,
        ecr_repository_name=ecr_repository_name,
        role_name=role_name,
        image_tag=image_tag,
        memory_size=memory_size,
        timeout=timeout,
        environment_variables=environment_variables,
        description=description,
        tags=tags,
        vpc_config=vpc_config
    )
