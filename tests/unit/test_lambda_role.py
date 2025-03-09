"""
Unit tests for the Lambda Role module.

These tests verify the functionality of the lambda_role module for creating
and managing IAM roles for AWS Lambda functions with S3 access.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

import boto3
import pytest
from botocore.exceptions import ClientError

from src.lambda_creator.lambda_role import (
    create_lambda_role,
    attach_s3_policy,
    create_lambda_role_with_s3_access,
    delete_role_and_policies
)


class TestLambdaRole(unittest.TestCase):
    """Test cases for the lambda_role module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for the boto3 IAM client
        self.iam_mock = MagicMock()
        
        # Common test data
        self.role_name = 'test-lambda-role'
        self.role_arn = 'arn:aws:iam::123456789012:role/test-lambda-role'
        self.policy_name = f"{self.role_name}-s3-access-policy"
        self.policy_arn = f"arn:aws:iam::123456789012:policy/{self.policy_name}"

    def test_create_lambda_role_success(self):
        """Test creating a Lambda execution role successfully."""
        # Configure the mock to return a successful response
        self.iam_mock.create_role.return_value = {
            'Role': {
                'Path': '/',
                'RoleName': self.role_name,
                'RoleId': 'AROAEXAMPLEID',
                'Arn': self.role_arn,
                'CreateDate': '2023-01-01T00:00:00+00:00'
            }
        }
        
        # Call the function
        result = create_lambda_role(self.iam_mock, self.role_name)
        
        # Verify the result
        self.assertEqual(result, self.role_arn)
        
        # Verify that create_role was called with the correct parameters
        self.iam_mock.create_role.assert_called_once()
        call_args = self.iam_mock.create_role.call_args[1]
        self.assertEqual(call_args['RoleName'], self.role_name)
        
        # Verify that the trust policy is correct
        trust_policy = json.loads(call_args['AssumeRolePolicyDocument'])
        self.assertEqual(trust_policy['Version'], '2012-10-17')
        self.assertEqual(len(trust_policy['Statement']), 1)
        self.assertEqual(trust_policy['Statement'][0]['Effect'], 'Allow')
        self.assertEqual(trust_policy['Statement'][0]['Principal']['Service'], 'lambda.amazonaws.com')
        self.assertEqual(trust_policy['Statement'][0]['Action'], 'sts:AssumeRole')
        
        # Verify that attach_role_policy was called with the correct parameters
        self.iam_mock.attach_role_policy.assert_called_once_with(
            RoleName=self.role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )

    def test_create_lambda_role_error(self):
        """Test creating a Lambda execution role with an error."""
        # Configure the mock to raise an error
        error_response = {
            'Error': {
                'Code': 'EntityAlreadyExists',
                'Message': f"Role with name {self.role_name} already exists."
            }
        }
        self.iam_mock.create_role.side_effect = ClientError(
            error_response, 'CreateRole'
        )
        
        # Call the function and expect a ClientError
        with self.assertRaises(ClientError) as context:
            create_lambda_role(self.iam_mock, self.role_name)
        
        # Verify the error
        self.assertEqual(context.exception.response['Error']['Code'], 'EntityAlreadyExists')

    def test_attach_s3_policy_success(self):
        """Test attaching an S3 access policy to a role successfully."""
        # Configure the mock to return a successful response
        self.iam_mock.create_policy.return_value = {
            'Policy': {
                'PolicyName': self.policy_name,
                'PolicyId': 'ANPAEXAMPLEID',
                'Arn': self.policy_arn,
                'Path': '/',
                'DefaultVersionId': 'v1',
                'AttachmentCount': 0,
                'CreateDate': '2023-01-01T00:00:00+00:00'
            }
        }
        
        # Call the function
        attach_s3_policy(self.iam_mock, self.role_name)
        
        # Verify that create_policy was called with the correct parameters
        self.iam_mock.create_policy.assert_called_once()
        call_args = self.iam_mock.create_policy.call_args[1]
        self.assertEqual(call_args['PolicyName'], self.policy_name)
        
        # Verify that the policy document is correct
        policy_doc = json.loads(call_args['PolicyDocument'])
        self.assertEqual(policy_doc['Version'], '2012-10-17')
        self.assertEqual(len(policy_doc['Statement']), 1)
        self.assertEqual(policy_doc['Statement'][0]['Effect'], 'Allow')
        self.assertIn('s3:GetObject', policy_doc['Statement'][0]['Action'])
        self.assertIn('s3:PutObject', policy_doc['Statement'][0]['Action'])
        self.assertIn('s3:ListBucket', policy_doc['Statement'][0]['Action'])
        self.assertIn('arn:aws:s3:::*', policy_doc['Statement'][0]['Resource'])
        
        # Verify that attach_role_policy was called with the correct parameters
        self.iam_mock.attach_role_policy.assert_called_once_with(
            RoleName=self.role_name,
            PolicyArn=self.policy_arn
        )

    def test_attach_s3_policy_error(self):
        """Test attaching an S3 access policy with an error."""
        # Configure the mock to raise an error
        error_response = {
            'Error': {
                'Code': 'EntityAlreadyExists',
                'Message': f"Policy {self.policy_name} already exists."
            }
        }
        self.iam_mock.create_policy.side_effect = ClientError(
            error_response, 'CreatePolicy'
        )
        
        # Call the function and expect a ClientError
        with self.assertRaises(ClientError) as context:
            attach_s3_policy(self.iam_mock, self.role_name)
        
        # Verify the error
        self.assertEqual(context.exception.response['Error']['Code'], 'EntityAlreadyExists')

    @patch('boto3.Session')
    @patch('src.lambda_creator.lambda_role.create_lambda_role')
    @patch('src.lambda_creator.lambda_role.attach_s3_policy')
    @patch('time.sleep')
    def test_create_lambda_role_with_s3_access_success(
        self, mock_sleep, mock_attach_s3_policy, mock_create_lambda_role, mock_boto3_session
    ):
        """Test creating a Lambda role with S3 access successfully."""
        # Configure the mocks
        session_instance = MagicMock()
        mock_boto3_session.return_value = session_instance
        session_instance.client.return_value = self.iam_mock
        
        mock_create_lambda_role.return_value = self.role_arn
        
        # Call the function
        result = create_lambda_role_with_s3_access(region_name='us-west-2', profile_name='default')
        
        # Verify the result
        self.assertEqual(result['RoleArn'], self.role_arn)
        self.assertTrue(result['RoleName'].startswith('lambda-s3-access-role-'))
        
        # Verify that the mocks were called with the correct parameters
        mock_boto3_session.assert_called_once_with(region_name='us-west-2', profile_name='default')
        session_instance.client.assert_called_once_with('iam')
        mock_create_lambda_role.assert_called_once()
        mock_attach_s3_policy.assert_called_once()
        mock_sleep.assert_called_once_with(10)

    @patch('boto3.Session')
    def test_delete_role_and_policies_success(self, mock_boto3_session):
        """Test deleting a role and its policies successfully."""
        # Configure the mocks
        session_instance = MagicMock()
        mock_boto3_session.return_value = session_instance
        session_instance.client.return_value = self.iam_mock
        
        # Configure the IAM mock responses
        self.iam_mock.list_attached_role_policies.return_value = {
            'AttachedPolicies': [
                {
                    'PolicyName': 'AWSLambdaBasicExecutionRole',
                    'PolicyArn': 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
                },
                {
                    'PolicyName': self.policy_name,
                    'PolicyArn': self.policy_arn
                }
            ]
        }
        
        self.iam_mock.list_role_policies.return_value = {
            'PolicyNames': ['inline-policy-1', 'inline-policy-2']
        }
        
        # Call the function
        delete_role_and_policies(self.role_name, region_name='us-west-2', profile_name='default')
        
        # Verify that the mocks were called with the correct parameters
        mock_boto3_session.assert_called_once_with(region_name='us-west-2', profile_name='default')
        session_instance.client.assert_called_once_with('iam')
        
        self.iam_mock.list_attached_role_policies.assert_called_once_with(
            RoleName=self.role_name
        )
        
        # Verify that detach_role_policy was called for each attached policy
        self.assertEqual(self.iam_mock.detach_role_policy.call_count, 2)
        
        # Verify that delete_policy was called only for the custom policy
        self.iam_mock.delete_policy.assert_called_once_with(
            PolicyArn=self.policy_arn
        )
        
        self.iam_mock.list_role_policies.assert_called_once_with(
            RoleName=self.role_name
        )
        
        # Verify that delete_role_policy was called for each inline policy
        self.assertEqual(self.iam_mock.delete_role_policy.call_count, 2)
        
        # Verify that delete_role was called
        self.iam_mock.delete_role.assert_called_once_with(
            RoleName=self.role_name
        )

    @patch('boto3.Session')
    def test_delete_role_and_policies_error(self, mock_boto3_session):
        """Test deleting a role with an error."""
        # Configure the mocks
        session_instance = MagicMock()
        mock_boto3_session.return_value = session_instance
        session_instance.client.return_value = self.iam_mock
        
        # Configure the IAM mock to raise an error
        error_response = {
            'Error': {
                'Code': 'NoSuchEntity',
                'Message': f"The role with name {self.role_name} cannot be found."
            }
        }
        self.iam_mock.list_attached_role_policies.side_effect = ClientError(
            error_response, 'ListAttachedRolePolicies'
        )
        
        # Call the function and expect a ClientError
        with self.assertRaises(ClientError) as context:
            delete_role_and_policies(self.role_name, region_name='us-west-2', profile_name='default')
        
        # Verify the error
        self.assertEqual(context.exception.response['Error']['Code'], 'NoSuchEntity')


if __name__ == '__main__':
    unittest.main()
