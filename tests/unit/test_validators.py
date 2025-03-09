"""
Unit tests for the Validators module.

These tests verify the functionality of the validators module for validating
input parameters for AWS Lambda functions.
"""

import unittest

import pytest

from src.lambda_creator.utils.validators import (
    validate_function_name,
    validate_role_name,
    validate_ecr_repository_name,
    validate_image_tag,
    validate_memory_size,
    validate_timeout,
    validate_environment_variables,
    validate_tags,
    validate_vpc_config,
    validate_input_parameters
)


class TestValidators(unittest.TestCase):
    """Test cases for the validators module."""

    def test_validate_function_name(self):
        """Test validating Lambda function names."""
        # Valid function names
        self.assertTrue(validate_function_name('my-function'))
        self.assertTrue(validate_function_name('my_function'))
        self.assertTrue(validate_function_name('myFunction123'))
        self.assertTrue(validate_function_name('a' * 64))  # Max length
        
        # Invalid function names
        self.assertFalse(validate_function_name(''))  # Empty
        self.assertFalse(validate_function_name('a' * 65))  # Too long
        self.assertFalse(validate_function_name('my function'))  # Space
        self.assertFalse(validate_function_name('my.function'))  # Period
        self.assertFalse(validate_function_name('my@function'))  # Special character

    def test_validate_role_name(self):
        """Test validating IAM role names."""
        # Valid role names
        self.assertTrue(validate_role_name('my-role'))
        self.assertTrue(validate_role_name('my_role'))
        self.assertTrue(validate_role_name('myRole123'))
        self.assertTrue(validate_role_name('my.role'))
        self.assertTrue(validate_role_name('my+role'))
        self.assertTrue(validate_role_name('my=role'))
        self.assertTrue(validate_role_name('my,role'))
        self.assertTrue(validate_role_name('my@role'))
        self.assertTrue(validate_role_name('a' * 64))  # Max length
        
        # Invalid role names
        self.assertFalse(validate_role_name(''))  # Empty
        self.assertFalse(validate_role_name('a' * 65))  # Too long
        self.assertFalse(validate_role_name('my role'))  # Space
        self.assertFalse(validate_role_name('my#role'))  # Invalid special character
        self.assertFalse(validate_role_name('my*role'))  # Invalid special character

    def test_validate_ecr_repository_name(self):
        """Test validating ECR repository names."""
        # Valid repository names
        self.assertTrue(validate_ecr_repository_name('my-repo'))
        self.assertTrue(validate_ecr_repository_name('my_repo'))
        self.assertTrue(validate_ecr_repository_name('myRepo123'))
        self.assertTrue(validate_ecr_repository_name('my/repo'))
        self.assertTrue(validate_ecr_repository_name('a' * 256))  # Max length
        
        # Invalid repository names
        self.assertFalse(validate_ecr_repository_name(''))  # Empty
        self.assertFalse(validate_ecr_repository_name('a'))  # Too short
        self.assertFalse(validate_ecr_repository_name('a' * 257))  # Too long
        self.assertFalse(validate_ecr_repository_name('my repo'))  # Space
        self.assertFalse(validate_ecr_repository_name('my.repo'))  # Period
        self.assertFalse(validate_ecr_repository_name('my@repo'))  # Special character

    def test_validate_image_tag(self):
        """Test validating ECR image tags."""
        # Valid image tags
        self.assertTrue(validate_image_tag('latest'))
        self.assertTrue(validate_image_tag('v1.0.0'))
        self.assertTrue(validate_image_tag('1.0'))
        self.assertTrue(validate_image_tag('my-tag'))
        self.assertTrue(validate_image_tag('my_tag'))
        self.assertTrue(validate_image_tag('my.tag'))
        self.assertTrue(validate_image_tag('my+tag'))
        self.assertTrue(validate_image_tag('a' * 128))  # Max length
        
        # Invalid image tags
        self.assertFalse(validate_image_tag(''))  # Empty
        self.assertFalse(validate_image_tag('a' * 129))  # Too long
        self.assertFalse(validate_image_tag('my tag'))  # Space
        self.assertFalse(validate_image_tag('my@tag'))  # Invalid special character
        self.assertFalse(validate_image_tag('my/tag'))  # Invalid special character

    def test_validate_memory_size(self):
        """Test validating Lambda function memory sizes."""
        # Valid memory sizes
        self.assertTrue(validate_memory_size(128))  # Min
        self.assertTrue(validate_memory_size(256))
        self.assertTrue(validate_memory_size(512))
        self.assertTrue(validate_memory_size(1024))
        self.assertTrue(validate_memory_size(10240))  # Max
        
        # Invalid memory sizes
        self.assertFalse(validate_memory_size(0))  # Too small
        self.assertFalse(validate_memory_size(127))  # Too small
        self.assertFalse(validate_memory_size(10241))  # Too large
        self.assertFalse(validate_memory_size(129))  # Not a multiple of 64
        self.assertFalse(validate_memory_size(200))  # Not a multiple of 64

    def test_validate_timeout(self):
        """Test validating Lambda function timeouts."""
        # Valid timeouts
        self.assertTrue(validate_timeout(1))  # Min
        self.assertTrue(validate_timeout(30))
        self.assertTrue(validate_timeout(300))
        self.assertTrue(validate_timeout(900))  # Max
        
        # Invalid timeouts
        self.assertFalse(validate_timeout(0))  # Too small
        self.assertFalse(validate_timeout(901))  # Too large
        self.assertFalse(validate_timeout(-1))  # Negative

    def test_validate_environment_variables(self):
        """Test validating Lambda function environment variables."""
        # Valid environment variables
        self.assertTrue(validate_environment_variables({}))  # Empty
        self.assertTrue(validate_environment_variables({'ENV': 'prod'}))
        self.assertTrue(validate_environment_variables({'ENV_VAR': 'value'}))
        self.assertTrue(validate_environment_variables({'ENV1': 'value1', 'ENV2': 'value2'}))
        
        # Create a dict with keys and values that are just under the 4KB limit
        large_env = {'KEY1': 'a' * 2000, 'KEY2': 'b' * 2000}
        self.assertTrue(validate_environment_variables(large_env))
        
        # Invalid environment variables
        self.assertFalse(validate_environment_variables({'1ENV': 'prod'}))  # Key starts with number
        self.assertFalse(validate_environment_variables({'ENV-VAR': 'value'}))  # Key contains hyphen
        self.assertFalse(validate_environment_variables({'ENV.VAR': 'value'}))  # Key contains period
        
        # Create a dict with keys and values that exceed the 4KB limit
        too_large_env = {'KEY1': 'a' * 2048, 'KEY2': 'b' * 2048}
        self.assertFalse(validate_environment_variables(too_large_env))

    def test_validate_tags(self):
        """Test validating Lambda function tags."""
        # Valid tags
        self.assertTrue(validate_tags({}))  # Empty
        self.assertTrue(validate_tags({'env': 'prod'}))
        self.assertTrue(validate_tags({'env': 'prod', 'owner': 'team'}))
        
        # Create a tag with key at max length and value at max length
        max_tag = {'a' * 128: 'b' * 256}
        self.assertTrue(validate_tags(max_tag))
        
        # Invalid tags
        self.assertFalse(validate_tags({'': 'value'}))  # Empty key
        self.assertFalse(validate_tags({'a' * 129: 'value'}))  # Key too long
        self.assertFalse(validate_tags({'key': 'b' * 257}))  # Value too long

    def test_validate_vpc_config(self):
        """Test validating Lambda function VPC configurations."""
        # Valid VPC configurations
        self.assertTrue(validate_vpc_config(None))  # None
        self.assertTrue(validate_vpc_config({
            'SubnetIds': ['subnet-12345'],
            'SecurityGroupIds': ['sg-12345']
        }))
        self.assertTrue(validate_vpc_config({
            'SubnetIds': ['subnet-12345', 'subnet-67890'],
            'SecurityGroupIds': ['sg-12345', 'sg-67890']
        }))
        
        # Invalid VPC configurations
        self.assertFalse(validate_vpc_config({}))  # Empty dict
        self.assertFalse(validate_vpc_config({
            'SubnetIds': []
        }))  # Missing SecurityGroupIds
        self.assertFalse(validate_vpc_config({
            'SecurityGroupIds': []
        }))  # Missing SubnetIds
        self.assertFalse(validate_vpc_config({
            'SubnetIds': [],
            'SecurityGroupIds': ['sg-12345']
        }))  # Empty SubnetIds
        self.assertFalse(validate_vpc_config({
            'SubnetIds': ['subnet-12345'],
            'SecurityGroupIds': []
        }))  # Empty SecurityGroupIds

    def test_validate_input_parameters_valid(self):
        """Test validating all input parameters with valid values."""
        result = validate_input_parameters(
            function_name='my-function',
            ecr_repository_name='my-repo',
            role_name='my-role',
            image_tag='latest',
            memory_size=256,
            timeout=30,
            environment_variables={'ENV': 'prod'},
            tags={'env': 'prod'},
            vpc_config={
                'SubnetIds': ['subnet-12345'],
                'SecurityGroupIds': ['sg-12345']
            }
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['message'], 'All parameters are valid.')

    def test_validate_input_parameters_invalid_function_name(self):
        """Test validating all input parameters with an invalid function name."""
        result = validate_input_parameters(
            function_name='my function',  # Invalid: contains space
            ecr_repository_name='my-repo',
            role_name='my-role',
            image_tag='latest',
            memory_size=256,
            timeout=30
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid function name', result['message'])

    def test_validate_input_parameters_invalid_ecr_repository_name(self):
        """Test validating all input parameters with an invalid ECR repository name."""
        result = validate_input_parameters(
            function_name='my-function',
            ecr_repository_name='my.repo',  # Invalid: contains period
            role_name='my-role',
            image_tag='latest',
            memory_size=256,
            timeout=30
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid ECR repository name', result['message'])

    def test_validate_input_parameters_invalid_role_name(self):
        """Test validating all input parameters with an invalid role name."""
        result = validate_input_parameters(
            function_name='my-function',
            ecr_repository_name='my-repo',
            role_name='my role',  # Invalid: contains space
            image_tag='latest',
            memory_size=256,
            timeout=30
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid role name', result['message'])

    def test_validate_input_parameters_invalid_image_tag(self):
        """Test validating all input parameters with an invalid image tag."""
        result = validate_input_parameters(
            function_name='my-function',
            ecr_repository_name='my-repo',
            role_name='my-role',
            image_tag='my/tag',  # Invalid: contains forward slash
            memory_size=256,
            timeout=30
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid image tag', result['message'])

    def test_validate_input_parameters_invalid_memory_size(self):
        """Test validating all input parameters with an invalid memory size."""
        result = validate_input_parameters(
            function_name='my-function',
            ecr_repository_name='my-repo',
            role_name='my-role',
            image_tag='latest',
            memory_size=100,  # Invalid: less than 128
            timeout=30
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid memory size', result['message'])

    def test_validate_input_parameters_invalid_timeout(self):
        """Test validating all input parameters with an invalid timeout."""
        result = validate_input_parameters(
            function_name='my-function',
            ecr_repository_name='my-repo',
            role_name='my-role',
            image_tag='latest',
            memory_size=256,
            timeout=1000  # Invalid: greater than 900
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid timeout', result['message'])


if __name__ == '__main__':
    unittest.main()
