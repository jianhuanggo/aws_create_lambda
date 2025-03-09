"""
Integration tests for the Lambda Creator module.

These tests verify the end-to-end functionality of the Lambda Creator module
for creating and managing AWS Lambda functions from ECR images.

Note: These tests require AWS credentials and will create and delete real AWS resources.
"""

import json
import os
import time
import unittest
from unittest.mock import patch

import boto3
import pytest

from src.lambda_creator.lambda_creator import LambdaCreator
from src.lambda_creator.lambda_role import create_lambda_role_with_s3_access, delete_role_and_policies


@pytest.mark.integration
class TestLambdaCreatorIntegration(unittest.TestCase):
    """Integration tests for the LambdaCreator class."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for the entire test class."""
        # Skip tests if AWS credentials are not available
        try:
            boto3.client('sts').get_caller_identity()
        except Exception:
            pytest.skip("AWS credentials not available")
            
        # Set up test resources
        cls.region_name = os.environ.get('AWS_REGION', 'us-east-1')
        cls.ecr_repo_name = f"lambda-creator-test-{int(time.time())}"
        cls.function_name = f"lambda-creator-test-{int(time.time())}"
        
        # Create ECR repository
        cls.ecr_client = boto3.client('ecr', region_name=cls.region_name)
        try:
            cls.ecr_client.create_repository(repositoryName=cls.ecr_repo_name)
            print(f"Created ECR repository: {cls.ecr_repo_name}")
        except cls.ecr_client.exceptions.RepositoryAlreadyExistsException:
            print(f"ECR repository {cls.ecr_repo_name} already exists")
            
        # Create a role with S3 access
        cls.role_info = create_lambda_role_with_s3_access(region_name=cls.region_name)
        cls.role_name = cls.role_info['RoleName']
        cls.role_arn = cls.role_info['RoleArn']
        print(f"Created IAM role: {cls.role_name}")
        
        # Wait for role to propagate
        print("Waiting for role to propagate...")
        time.sleep(10)
        
        # Create Lambda Creator instance
        cls.creator = LambdaCreator(region_name=cls.region_name)

    @classmethod
    def tearDownClass(cls):
        """Tear down test fixtures for the entire test class."""
        # Delete Lambda function if it exists
        try:
            cls.creator.delete_lambda_function(cls.function_name)
            print(f"Deleted Lambda function: {cls.function_name}")
        except Exception as e:
            print(f"Error deleting Lambda function: {e}")
            
        # Delete IAM role and policies
        try:
            delete_role_and_policies(cls.role_name, region_name=cls.region_name)
            print(f"Deleted IAM role: {cls.role_name}")
        except Exception as e:
            print(f"Error deleting IAM role: {e}")
            
        # Delete ECR repository
        try:
            cls.ecr_client.delete_repository(
                repositoryName=cls.ecr_repo_name,
                force=True
            )
            print(f"Deleted ECR repository: {cls.ecr_repo_name}")
        except Exception as e:
            print(f"Error deleting ECR repository: {e}")

    @pytest.mark.skipif(not os.environ.get('AWS_ACCESS_KEY_ID'), reason="AWS credentials not available")
    def test_create_lambda_from_ecr_mock(self):
        """Test creating a Lambda function from an ECR image using mocks."""
        # This test uses mocks to avoid creating real AWS resources
        with patch.object(self.creator.lambda_client, 'create_function') as mock_create_function:
            mock_create_function.return_value = {
                'FunctionName': self.function_name,
                'FunctionArn': f'arn:aws:lambda:{self.region_name}:123456789012:function:{self.function_name}',
                'Role': self.role_arn,
                'PackageType': 'Image'
            }
            
            with patch.object(self.creator, '_get_ecr_repository_uri') as mock_get_ecr_uri:
                mock_get_ecr_uri.return_value = f"123456789012.dkr.ecr.{self.region_name}.amazonaws.com/{self.ecr_repo_name}"
                
                # Create the Lambda function
                response = self.creator.create_lambda_from_ecr(
                    function_name=self.function_name,
                    ecr_repository_name=self.ecr_repo_name,
                    role_name=self.role_name,
                    memory_size=256,
                    timeout=60,
                    description='Test Lambda function'
                )
                
                # Verify the response
                self.assertEqual(response['FunctionName'], self.function_name)
                self.assertEqual(response['Role'], self.role_arn)
                self.assertEqual(response['PackageType'], 'Image')
                
                # Verify that create_function was called with the correct parameters
                mock_create_function.assert_called_once()
                call_args = mock_create_function.call_args[1]
                self.assertEqual(call_args['FunctionName'], self.function_name)
                self.assertEqual(call_args['Role'], self.role_arn)
                self.assertEqual(call_args['PackageType'], 'Image')
                self.assertEqual(call_args['MemorySize'], 256)
                self.assertEqual(call_args['Timeout'], 60)
                self.assertEqual(call_args['Description'], 'Test Lambda function')

    @pytest.mark.skipif(not os.environ.get('AWS_ACCESS_KEY_ID'), reason="AWS credentials not available")
    def test_end_to_end_with_mocks(self):
        """Test the end-to-end workflow using mocks."""
        # This test simulates the entire workflow using mocks
        
        # 1. Create a Lambda function
        with patch.object(self.creator.lambda_client, 'create_function') as mock_create_function:
            mock_create_function.return_value = {
                'FunctionName': self.function_name,
                'FunctionArn': f'arn:aws:lambda:{self.region_name}:123456789012:function:{self.function_name}',
                'Role': self.role_arn,
                'PackageType': 'Image'
            }
            
            with patch.object(self.creator, '_get_ecr_repository_uri') as mock_get_ecr_uri:
                mock_get_ecr_uri.return_value = f"123456789012.dkr.ecr.{self.region_name}.amazonaws.com/{self.ecr_repo_name}"
                
                # Create the Lambda function
                create_response = self.creator.create_lambda_from_ecr(
                    function_name=self.function_name,
                    ecr_repository_name=self.ecr_repo_name,
                    role_name=self.role_name,
                    memory_size=256,
                    timeout=60,
                    description='Test Lambda function'
                )
                
                # Verify the response
                self.assertEqual(create_response['FunctionName'], self.function_name)
        
        # 2. Get Lambda function details
        with patch.object(self.creator.lambda_client, 'get_function') as mock_get_function:
            mock_get_function.return_value = {
                'Configuration': {
                    'FunctionName': self.function_name,
                    'FunctionArn': f'arn:aws:lambda:{self.region_name}:123456789012:function:{self.function_name}',
                    'Role': self.role_arn,
                    'PackageType': 'Image',
                    'MemorySize': 256,
                    'Timeout': 60
                }
            }
            
            # Get the Lambda function
            get_response = self.creator.get_lambda_function(self.function_name)
            
            # Verify the response
            self.assertEqual(get_response['Configuration']['FunctionName'], self.function_name)
            self.assertEqual(get_response['Configuration']['Role'], self.role_arn)
            self.assertEqual(get_response['Configuration']['PackageType'], 'Image')
            self.assertEqual(get_response['Configuration']['MemorySize'], 256)
            self.assertEqual(get_response['Configuration']['Timeout'], 60)
        
        # 3. Update Lambda function
        with patch.object(self.creator.lambda_client, 'update_function_configuration') as mock_update_config:
            mock_update_config.return_value = {
                'FunctionName': self.function_name,
                'FunctionArn': f'arn:aws:lambda:{self.region_name}:123456789012:function:{self.function_name}',
                'Role': self.role_arn,
                'PackageType': 'Image',
                'MemorySize': 512,  # Updated
                'Timeout': 120  # Updated
            }
            
            # Update the Lambda function
            update_response = self.creator.update_lambda_function(
                function_name=self.function_name,
                memory_size=512,
                timeout=120,
                description='Updated Lambda function'
            )
            
            # Verify the response
            self.assertEqual(update_response['FunctionName'], self.function_name)
            self.assertEqual(update_response['MemorySize'], 512)
            self.assertEqual(update_response['Timeout'], 120)
        
        # 4. Invoke Lambda function
        with patch.object(self.creator.lambda_client, 'invoke') as mock_invoke:
            # Create a mock response payload
            mock_payload = type('MockPayload', (), {})()
            mock_payload.read = lambda: json.dumps({'result': 'success'}).encode()
            
            mock_invoke.return_value = {
                'StatusCode': 200,
                'Payload': mock_payload
            }
            
            # Invoke the Lambda function
            invoke_response = self.creator.invoke_lambda_function(
                function_name=self.function_name,
                payload={'input': 'test'}
            )
            
            # Verify the response
            self.assertEqual(invoke_response['StatusCode'], 200)
            self.assertEqual(invoke_response['ResponsePayload']['result'], 'success')
        
        # 5. Delete Lambda function
        with patch.object(self.creator.lambda_client, 'delete_function') as mock_delete_function:
            mock_delete_function.return_value = {}
            
            # Delete the Lambda function
            delete_response = self.creator.delete_lambda_function(self.function_name)
            
            # Verify that delete_function was called with the correct parameters
            mock_delete_function.assert_called_once_with(FunctionName=self.function_name)


if __name__ == '__main__':
    unittest.main()
