"""
Unit tests for the Lambda Creator module.

These tests verify the functionality of the LambdaCreator class and its methods
for creating and managing AWS Lambda functions from ECR images.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

import boto3
import pytest
from botocore.exceptions import ClientError

from src.lambda_creator.lambda_creator import LambdaCreator, create_lambda_function


class TestLambdaCreator(unittest.TestCase):
    """Test cases for the LambdaCreator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for the boto3 clients
        self.lambda_mock = MagicMock()
        self.ecr_mock = MagicMock()
        self.iam_mock = MagicMock()
        
        # Create a patcher for boto3.client
        self.boto3_client_patcher = patch('boto3.client')
        self.boto3_client_mock = self.boto3_client_patcher.start()
        
        # Configure the mock to return our mocks for different services
        def side_effect(service, region_name=None):
            if service == 'lambda':
                return self.lambda_mock
            elif service == 'ecr':
                return self.ecr_mock
            elif service == 'iam':
                return self.iam_mock
            else:
                return MagicMock()
        
        self.boto3_client_mock.side_effect = side_effect
        
        # Create an instance of LambdaCreator with the mocked clients
        self.creator = LambdaCreator(region_name='us-west-2')
        
        # Common test data
        self.function_name = 'test-lambda-function'
        self.ecr_repo_name = 'test-ecr-repo'
        self.role_name = 'test-lambda-role'
        self.role_arn = 'arn:aws:iam::123456789012:role/test-lambda-role'
        self.ecr_repo_uri = '123456789012.dkr.ecr.us-west-2.amazonaws.com/test-ecr-repo'
        self.image_tag = 'latest'
        self.image_uri = f"{self.ecr_repo_uri}:{self.image_tag}"

    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the patcher
        self.boto3_client_patcher.stop()

    def test_init(self):
        """Test the initialization of LambdaCreator."""
        # Verify that the boto3 clients were created with the correct region
        self.boto3_client_mock.assert_any_call('lambda', region_name='us-west-2')
        self.boto3_client_mock.assert_any_call('ecr', region_name='us-west-2')
        self.boto3_client_mock.assert_any_call('iam', region_name='us-west-2')
        
        # Verify that the clients were assigned correctly
        self.assertEqual(self.creator.lambda_client, self.lambda_mock)
        self.assertEqual(self.creator.ecr_client, self.ecr_mock)
        self.assertEqual(self.creator.iam_client, self.iam_mock)

    def test_get_ecr_repository_uri_success(self):
        """Test getting an ECR repository URI successfully."""
        # Configure the mock to return a successful response
        self.ecr_mock.describe_repositories.return_value = {
            'repositories': [
                {
                    'repositoryArn': f'arn:aws:ecr:us-west-2:123456789012:repository/{self.ecr_repo_name}',
                    'registryId': '123456789012',
                    'repositoryName': self.ecr_repo_name,
                    'repositoryUri': self.ecr_repo_uri,
                    'createdAt': '2023-01-01T00:00:00+00:00'
                }
            ]
        }
        
        # Call the method
        result = self.creator._get_ecr_repository_uri(self.ecr_repo_name)
        
        # Verify the result
        self.assertEqual(result, self.ecr_repo_uri)
        
        # Verify that the mock was called with the correct parameters
        self.ecr_mock.describe_repositories.assert_called_once_with(
            repositoryNames=[self.ecr_repo_name]
        )

    def test_get_ecr_repository_uri_not_found(self):
        """Test getting an ECR repository URI when the repository doesn't exist."""
        # Configure the mock to raise a RepositoryNotFoundException
        error_response = {
            'Error': {
                'Code': 'RepositoryNotFoundException',
                'Message': f'Repository {self.ecr_repo_name} not found'
            }
        }
        self.ecr_mock.describe_repositories.side_effect = ClientError(
            error_response, 'DescribeRepositories'
        )
        
        # Call the method
        result = self.creator._get_ecr_repository_uri(self.ecr_repo_name)
        
        # Verify the result
        self.assertIsNone(result)
        
        # Verify that the mock was called with the correct parameters
        self.ecr_mock.describe_repositories.assert_called_once_with(
            repositoryNames=[self.ecr_repo_name]
        )

    def test_get_role_arn_success(self):
        """Test getting an IAM role ARN successfully."""
        # Configure the mock to return a successful response
        self.iam_mock.get_role.return_value = {
            'Role': {
                'Path': '/',
                'RoleName': self.role_name,
                'RoleId': 'AROAEXAMPLEID',
                'Arn': self.role_arn,
                'CreateDate': '2023-01-01T00:00:00+00:00'
            }
        }
        
        # Call the method
        result = self.creator._get_role_arn(self.role_name)
        
        # Verify the result
        self.assertEqual(result, self.role_arn)
        
        # Verify that the mock was called with the correct parameters
        self.iam_mock.get_role.assert_called_once_with(RoleName=self.role_name)

    def test_get_role_arn_not_found(self):
        """Test getting an IAM role ARN when the role doesn't exist."""
        # Configure the mock to raise a NoSuchEntity error
        error_response = {
            'Error': {
                'Code': 'NoSuchEntity',
                'Message': f'The role with name {self.role_name} cannot be found'
            }
        }
        self.iam_mock.get_role.side_effect = ClientError(
            error_response, 'GetRole'
        )
        
        # Call the method
        result = self.creator._get_role_arn(self.role_name)
        
        # Verify the result
        self.assertIsNone(result)
        
        # Verify that the mock was called with the correct parameters
        self.iam_mock.get_role.assert_called_once_with(RoleName=self.role_name)

    @patch('src.lambda_creator.lambda_creator.create_lambda_role')
    @patch('src.lambda_creator.lambda_creator.attach_s3_policy')
    @patch('time.sleep')
    def test_create_lambda_from_ecr_success(self, mock_sleep, mock_attach_s3_policy, mock_create_lambda_role):
        """Test creating a Lambda function from an ECR image successfully."""
        # Configure the mocks
        self.ecr_mock.describe_repositories.return_value = {
            'repositories': [
                {
                    'repositoryUri': self.ecr_repo_uri
                }
            ]
        }
        
        mock_create_lambda_role.return_value = self.role_arn
        
        self.lambda_mock.create_function.return_value = {
            'FunctionName': self.function_name,
            'FunctionArn': f'arn:aws:lambda:us-west-2:123456789012:function:{self.function_name}',
            'Runtime': 'provided',
            'Role': self.role_arn,
            'Handler': 'index.handler',
            'CodeSize': 1024,
            'Description': 'Test Lambda function',
            'Timeout': 30,
            'MemorySize': 128,
            'LastModified': '2023-01-01T00:00:00+00:00',
            'CodeSha256': 'abcdef1234567890',
            'Version': '$LATEST',
            'PackageType': 'Image'
        }
        
        # Call the method
        result = self.creator.create_lambda_from_ecr(
            function_name=self.function_name,
            ecr_repository_name=self.ecr_repo_name,
            memory_size=256,
            timeout=60,
            description='Test Lambda function'
        )
        
        # Verify the result
        self.assertEqual(result['FunctionName'], self.function_name)
        self.assertEqual(result['PackageType'], 'Image')
        
        # Verify that the mocks were called with the correct parameters
        self.ecr_mock.describe_repositories.assert_called_once_with(
            repositoryNames=[self.ecr_repo_name]
        )
        
        # Verify that create_lambda_role was called
        mock_create_lambda_role.assert_called_once()
        
        # Verify that attach_s3_policy was called
        mock_attach_s3_policy.assert_called_once()
        
        # Verify that create_function was called with the correct parameters
        self.lambda_mock.create_function.assert_called_once()
        call_args = self.lambda_mock.create_function.call_args[1]
        self.assertEqual(call_args['FunctionName'], self.function_name)
        self.assertEqual(call_args['Role'], self.role_arn)
        self.assertEqual(call_args['PackageType'], 'Image')
        self.assertEqual(call_args['Code']['ImageUri'], f"{self.ecr_repo_uri}:latest")
        self.assertEqual(call_args['Description'], 'Test Lambda function')
        self.assertEqual(call_args['Timeout'], 60)
        self.assertEqual(call_args['MemorySize'], 256)

    def test_create_lambda_from_ecr_repository_not_found(self):
        """Test creating a Lambda function when the ECR repository doesn't exist."""
        # Configure the mock to return an empty list of repositories
        self.ecr_mock.describe_repositories.return_value = {
            'repositories': []
        }
        
        # Call the method and expect a ValueError
        with self.assertRaises(ValueError) as context:
            self.creator.create_lambda_from_ecr(
                function_name=self.function_name,
                ecr_repository_name=self.ecr_repo_name
            )
        
        # Verify the error message
        self.assertIn(f"ECR repository {self.ecr_repo_name} not found", str(context.exception))

    def test_update_lambda_function_success(self):
        """Test updating a Lambda function successfully."""
        # Configure the mocks
        self.ecr_mock.describe_repositories.return_value = {
            'repositories': [
                {
                    'repositoryUri': self.ecr_repo_uri
                }
            ]
        }
        
        self.lambda_mock.update_function_code.return_value = {
            'FunctionName': self.function_name,
            'FunctionArn': f'arn:aws:lambda:us-west-2:123456789012:function:{self.function_name}',
            'PackageType': 'Image'
        }
        
        self.lambda_mock.update_function_configuration.return_value = {
            'FunctionName': self.function_name,
            'Description': 'Updated Lambda function',
            'Timeout': 120,
            'MemorySize': 512
        }
        
        # Call the method
        result = self.creator.update_lambda_function(
            function_name=self.function_name,
            ecr_repository_name=self.ecr_repo_name,
            memory_size=512,
            timeout=120,
            description='Updated Lambda function'
        )
        
        # Verify that the mocks were called with the correct parameters
        self.ecr_mock.describe_repositories.assert_called_once_with(
            repositoryNames=[self.ecr_repo_name]
        )
        
        self.lambda_mock.update_function_code.assert_called_once_with(
            FunctionName=self.function_name,
            ImageUri=f"{self.ecr_repo_uri}:latest"
        )
        
        self.lambda_mock.update_function_configuration.assert_called_once()
        call_args = self.lambda_mock.update_function_configuration.call_args[1]
        self.assertEqual(call_args['FunctionName'], self.function_name)
        self.assertEqual(call_args['Description'], 'Updated Lambda function')
        self.assertEqual(call_args['Timeout'], 120)
        self.assertEqual(call_args['MemorySize'], 512)

    def test_delete_lambda_function_success(self):
        """Test deleting a Lambda function successfully."""
        # Configure the mock
        self.lambda_mock.delete_function.return_value = {}
        
        # Call the method
        result = self.creator.delete_lambda_function(self.function_name)
        
        # Verify that the mock was called with the correct parameters
        self.lambda_mock.delete_function.assert_called_once_with(
            FunctionName=self.function_name
        )

    def test_get_lambda_function_success(self):
        """Test getting information about a Lambda function successfully."""
        # Configure the mock
        self.lambda_mock.get_function.return_value = {
            'Configuration': {
                'FunctionName': self.function_name,
                'FunctionArn': f'arn:aws:lambda:us-west-2:123456789012:function:{self.function_name}',
                'Runtime': 'provided',
                'Role': self.role_arn,
                'Handler': 'index.handler',
                'CodeSize': 1024,
                'Description': 'Test Lambda function',
                'Timeout': 30,
                'MemorySize': 128,
                'LastModified': '2023-01-01T00:00:00+00:00',
                'CodeSha256': 'abcdef1234567890',
                'Version': '$LATEST',
                'PackageType': 'Image'
            },
            'Code': {
                'ImageUri': self.image_uri,
                'RepositoryType': 'ECR'
            },
            'Tags': {
                'Environment': 'test'
            }
        }
        
        # Call the method
        result = self.creator.get_lambda_function(self.function_name)
        
        # Verify the result
        self.assertEqual(result['Configuration']['FunctionName'], self.function_name)
        self.assertEqual(result['Code']['ImageUri'], self.image_uri)
        
        # Verify that the mock was called with the correct parameters
        self.lambda_mock.get_function.assert_called_once_with(
            FunctionName=self.function_name
        )

    def test_invoke_lambda_function_success(self):
        """Test invoking a Lambda function successfully."""
        # Configure the mock
        payload_response = {'result': 'success', 'message': 'Hello from Lambda'}
        mock_payload = MagicMock()
        mock_payload.read.return_value = json.dumps(payload_response).encode()
        
        self.lambda_mock.invoke.return_value = {
            'StatusCode': 200,
            'ExecutedVersion': '$LATEST',
            'Payload': mock_payload
        }
        
        # Call the method
        result = self.creator.invoke_lambda_function(
            function_name=self.function_name,
            payload={'input': 'test'}
        )
        
        # Verify the result
        self.assertEqual(result['StatusCode'], 200)
        self.assertEqual(result['ResponsePayload'], payload_response)
        
        # Verify that the mock was called with the correct parameters
        self.lambda_mock.invoke.assert_called_once()
        call_args = self.lambda_mock.invoke.call_args[1]
        self.assertEqual(call_args['FunctionName'], self.function_name)
        self.assertEqual(call_args['InvocationType'], 'RequestResponse')
        self.assertEqual(json.loads(call_args['Payload'].decode()), {'input': 'test'})

    def test_list_lambda_functions_success(self):
        """Test listing Lambda functions successfully."""
        # Configure the mock
        paginator_mock = MagicMock()
        self.lambda_mock.get_paginator.return_value = paginator_mock
        
        paginator_mock.paginate.return_value = [
            {
                'Functions': [
                    {
                        'FunctionName': 'function1',
                        'FunctionArn': 'arn:aws:lambda:us-west-2:123456789012:function:function1',
                        'Runtime': 'provided',
                        'Role': 'arn:aws:iam::123456789012:role/role1',
                        'PackageType': 'Image'
                    },
                    {
                        'FunctionName': 'function2',
                        'FunctionArn': 'arn:aws:lambda:us-west-2:123456789012:function:function2',
                        'Runtime': 'provided',
                        'Role': 'arn:aws:iam::123456789012:role/role2',
                        'PackageType': 'Image'
                    }
                ]
            }
        ]
        
        # Call the method
        result = self.creator.list_lambda_functions()
        
        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['FunctionName'], 'function1')
        self.assertEqual(result[1]['FunctionName'], 'function2')
        
        # Verify that the mock was called with the correct parameters
        self.lambda_mock.get_paginator.assert_called_once_with('list_functions')
        paginator_mock.paginate.assert_called_once_with(MaxItems=50)

    @patch('src.lambda_creator.lambda_creator.LambdaCreator')
    def test_create_lambda_function_convenience_function(self, mock_lambda_creator_class):
        """Test the create_lambda_function convenience function."""
        # Configure the mock
        mock_lambda_creator = MagicMock()
        mock_lambda_creator_class.return_value = mock_lambda_creator
        
        mock_lambda_creator.create_lambda_from_ecr.return_value = {
            'FunctionName': self.function_name,
            'FunctionArn': f'arn:aws:lambda:us-west-2:123456789012:function:{self.function_name}'
        }
        
        # Call the function
        result = create_lambda_function(
            function_name=self.function_name,
            ecr_repository_name=self.ecr_repo_name,
            region_name='us-west-2',
            memory_size=256,
            timeout=60,
            description='Test Lambda function'
        )
        
        # Verify the result
        self.assertEqual(result['FunctionName'], self.function_name)
        
        # Verify that the mock was called with the correct parameters
        mock_lambda_creator_class.assert_called_once_with(region_name='us-west-2')
        mock_lambda_creator.create_lambda_from_ecr.assert_called_once_with(
            function_name=self.function_name,
            ecr_repository_name=self.ecr_repo_name,
            role_name=None,
            image_tag='latest',
            memory_size=256,
            timeout=60,
            environment_variables=None,
            description='Test Lambda function',
            tags=None,
            vpc_config=None
        )


if __name__ == '__main__':
    unittest.main()
