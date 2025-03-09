"""
Lambda Role Module

This module provides functionality to create and manage IAM roles for AWS Lambda functions.
It ensures that Lambda functions have the necessary permissions to access AWS resources,
particularly S3 buckets.
"""

import json
import logging
import time
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def create_lambda_role(iam_client, role_name: str) -> str:
    """
    Create an IAM role for Lambda function execution.

    Args:
        iam_client: Boto3 IAM client
        role_name: Name of the IAM role to create

    Returns:
        ARN of the created IAM role
    """
    try:
        # Define the trust relationship policy document for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        logger.info(f"Creating IAM role {role_name} for Lambda execution")
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"IAM role for Lambda function execution created by LambdaCreator"
        )

        # Attach the AWS managed policy for Lambda basic execution
        logger.info(f"Attaching AWSLambdaBasicExecutionRole policy to role {role_name}")
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )

        # Return the ARN of the created role
        role_arn = response['Role']['Arn']
        logger.info(f"IAM role {role_name} created with ARN: {role_arn}")
        return role_arn

    except ClientError as e:
        logger.error(f"Error creating IAM role: {e}")
        raise


def attach_s3_policy(iam_client, role_name: str) -> None:
    """
    Attach a policy to the IAM role that grants access to all S3 buckets.

    Args:
        iam_client: Boto3 IAM client
        role_name: Name of the IAM role to attach the policy to
    """
    try:
        # Define the policy document for S3 access
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket",
                        "s3:GetBucketLocation",
                        "s3:ListAllMyBuckets"
                    ],
                    "Resource": [
                        "arn:aws:s3:::*",
                        "arn:aws:s3:::*/*"
                    ]
                }
            ]
        }

        # Create the policy
        policy_name = f"{role_name}-s3-access-policy"
        logger.info(f"Creating IAM policy {policy_name} for S3 access")
        
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(s3_policy),
            Description="Policy for Lambda function to access all S3 buckets"
        )

        # Attach the policy to the role
        policy_arn = response['Policy']['Arn']
        logger.info(f"Attaching policy {policy_name} to role {role_name}")
        
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        
        logger.info(f"Policy {policy_name} attached to role {role_name}")

    except ClientError as e:
        logger.error(f"Error attaching S3 policy to IAM role: {e}")
        raise


def create_lambda_role_with_s3_access(region_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create an IAM role for Lambda with S3 access (convenience function).

    Args:
        region_name: AWS region name

    Returns:
        Dict containing information about the created IAM role
    """
    try:
        iam_client = boto3.client('iam', region_name=region_name)
        
        # Create a unique role name with timestamp
        role_name = f"lambda-s3-access-role-{int(time.time())}"
        
        # Create the role
        role_arn = create_lambda_role(iam_client, role_name)
        
        # Attach S3 access policy
        attach_s3_policy(iam_client, role_name)
        
        # Wait for role to propagate
        logger.info(f"Waiting for role {role_name} to propagate...")
        time.sleep(10)
        
        return {
            'RoleName': role_name,
            'RoleArn': role_arn
        }
        
    except ClientError as e:
        logger.error(f"Error creating Lambda role with S3 access: {e}")
        raise


def delete_role_and_policies(role_name: str, region_name: Optional[str] = None) -> None:
    """
    Delete an IAM role and its attached policies.

    Args:
        role_name: Name of the IAM role to delete
        region_name: AWS region name
    """
    try:
        iam_client = boto3.client('iam', region_name=region_name)
        
        # List attached role policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        
        # Detach each policy
        for policy in attached_policies.get('AttachedPolicies', []):
            policy_arn = policy['PolicyArn']
            logger.info(f"Detaching policy {policy_arn} from role {role_name}")
            iam_client.detach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            # If it's a custom policy (not AWS managed), delete it
            if not policy_arn.startswith('arn:aws:iam::aws:policy/'):
                logger.info(f"Deleting custom policy {policy_arn}")
                iam_client.delete_policy(PolicyArn=policy_arn)
        
        # List inline policies
        inline_policies = iam_client.list_role_policies(RoleName=role_name)
        
        # Delete each inline policy
        for policy_name in inline_policies.get('PolicyNames', []):
            logger.info(f"Deleting inline policy {policy_name} from role {role_name}")
            iam_client.delete_role_policy(
                RoleName=role_name,
                PolicyName=policy_name
            )
        
        # Delete the role
        logger.info(f"Deleting role {role_name}")
        iam_client.delete_role(RoleName=role_name)
        logger.info(f"Role {role_name} deleted successfully")
        
    except ClientError as e:
        logger.error(f"Error deleting role and policies: {e}")
        raise
