"""
Validators Module

This module provides validation functions for the Lambda Creator.
"""

import re
from typing import Dict, Any, Optional, List, Union


def validate_function_name(function_name: str) -> bool:
    """
    Validate a Lambda function name.
    
    Lambda function names must be at least 1 character and at most 64 characters.
    They can contain only letters, numbers, hyphens, and underscores.
    
    Args:
        function_name: Name of the Lambda function to validate
        
    Returns:
        True if the function name is valid, False otherwise
    """
    if not function_name:
        return False
        
    # Check length
    if len(function_name) > 64:
        return False
        
    # Check characters
    pattern = r'^[a-zA-Z0-9-_]+$'
    return bool(re.match(pattern, function_name))


def validate_role_name(role_name: str) -> bool:
    """
    Validate an IAM role name.
    
    IAM role names must be at least 1 character and at most 64 characters.
    They can contain only letters, numbers, and the following characters: +=,.@-_
    
    Args:
        role_name: Name of the IAM role to validate
        
    Returns:
        True if the role name is valid, False otherwise
    """
    if not role_name:
        return False
        
    # Check length
    if len(role_name) > 64:
        return False
        
    # Check characters
    pattern = r'^[a-zA-Z0-9+=,.@\-_]+$'
    return bool(re.match(pattern, role_name))


def validate_ecr_repository_name(repository_name: str) -> bool:
    """
    Validate an ECR repository name.
    
    ECR repository names must be at least 2 characters and at most 256 characters.
    They can contain only letters, numbers, hyphens, underscores, and forward slashes.
    
    Args:
        repository_name: Name of the ECR repository to validate
        
    Returns:
        True if the repository name is valid, False otherwise
    """
    if not repository_name:
        return False
        
    # Check length
    if len(repository_name) < 2 or len(repository_name) > 256:
        return False
        
    # Check characters
    pattern = r'^[a-zA-Z0-9-_/]+$'
    return bool(re.match(pattern, repository_name))


def validate_image_tag(image_tag: str) -> bool:
    """
    Validate an ECR image tag.
    
    ECR image tags must be at least 1 character and at most 128 characters.
    They can contain only letters, numbers, hyphens, underscores, periods, and plus signs.
    
    Args:
        image_tag: Tag of the ECR image to validate
        
    Returns:
        True if the image tag is valid, False otherwise
    """
    if not image_tag:
        return False
        
    # Check length
    if len(image_tag) > 128:
        return False
        
    # Check characters
    pattern = r'^[a-zA-Z0-9-_.+]+$'
    return bool(re.match(pattern, image_tag))


def validate_memory_size(memory_size: int) -> bool:
    """
    Validate a Lambda function memory size.
    
    Lambda function memory size must be at least 128 MB and at most 10240 MB (10 GB).
    It must be a multiple of 64 MB.
    
    Args:
        memory_size: Memory size for the Lambda function in MB
        
    Returns:
        True if the memory size is valid, False otherwise
    """
    # Check range
    if memory_size < 128 or memory_size > 10240:
        return False
        
    # Check if it's a multiple of 64
    return memory_size % 64 == 0


def validate_timeout(timeout: int) -> bool:
    """
    Validate a Lambda function timeout.
    
    Lambda function timeout must be at least 1 second and at most 900 seconds (15 minutes).
    
    Args:
        timeout: Timeout for the Lambda function in seconds
        
    Returns:
        True if the timeout is valid, False otherwise
    """
    # Check range
    return 1 <= timeout <= 900


def validate_environment_variables(env_vars: Dict[str, str]) -> bool:
    """
    Validate Lambda function environment variables.
    
    Lambda function environment variables must have keys that start with a letter
    and contain only letters, numbers, and underscores.
    The total size of all environment variables cannot exceed 4 KB.
    
    Args:
        env_vars: Environment variables for the Lambda function
        
    Returns:
        True if the environment variables are valid, False otherwise
    """
    if not env_vars:
        return True
        
    # Check keys
    for key in env_vars.keys():
        if not key:
            return False
            
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
        if not re.match(pattern, key):
            return False
            
    # Check total size
    total_size = sum(len(key) + len(str(value)) for key, value in env_vars.items())
    return total_size <= 4096


def validate_tags(tags: Dict[str, str]) -> bool:
    """
    Validate Lambda function tags.
    
    Lambda function tags must have keys that are at least 1 character and at most 128 characters.
    Tag values can be up to 256 characters.
    
    Args:
        tags: Tags to attach to the Lambda function
        
    Returns:
        True if the tags are valid, False otherwise
    """
    if not tags:
        return True
        
    # Check keys and values
    for key, value in tags.items():
        if not key or len(key) > 128:
            return False
            
        if len(str(value)) > 256:
            return False
            
    return True


def validate_vpc_config(vpc_config: Dict[str, List[str]]) -> bool:
    """
    Validate Lambda function VPC configuration.
    
    Lambda function VPC configuration must include subnet IDs and security group IDs.
    
    Args:
        vpc_config: VPC configuration for the Lambda function
        
    Returns:
        True if the VPC configuration is valid, False otherwise
    """
    # None is valid (no VPC config)
    if vpc_config is None:
        return True
        
    # Empty dict is invalid
    if not vpc_config:
        return False
        
    # Check required keys
    if 'SubnetIds' not in vpc_config or 'SecurityGroupIds' not in vpc_config:
        return False
        
    # Check that there is at least one subnet and one security group
    if not vpc_config['SubnetIds'] or not vpc_config['SecurityGroupIds']:
        return False
        
    return True


def validate_input_parameters(
    function_name: str,
    ecr_repository_name: str,
    role_name: Optional[str] = None,
    image_tag: str = 'latest',
    memory_size: int = 128,
    timeout: int = 30,
    environment_variables: Optional[Dict[str, str]] = None,
    tags: Optional[Dict[str, str]] = None,
    vpc_config: Optional[Dict[str, List[str]]] = None
) -> Dict[str, Union[bool, str]]:
    """
    Validate all input parameters for creating a Lambda function.
    
    Args:
        function_name: Name of the Lambda function
        ecr_repository_name: Name of the ECR repository
        role_name: Name of the IAM role to use
        image_tag: Tag of the ECR image to use
        memory_size: Memory size for the Lambda function in MB
        timeout: Timeout for the Lambda function in seconds
        environment_variables: Environment variables for the Lambda function
        tags: Tags to attach to the Lambda function
        vpc_config: VPC configuration for the Lambda function
        
    Returns:
        Dict with 'valid' key indicating if all parameters are valid,
        and 'message' key with error message if not valid
    """
    # Validate function name
    if not validate_function_name(function_name):
        return {
            'valid': False,
            'message': 'Invalid function name. Function names must be at most 64 characters and can contain only letters, numbers, hyphens, and underscores.'
        }
        
    # Validate ECR repository name
    if not validate_ecr_repository_name(ecr_repository_name):
        return {
            'valid': False,
            'message': 'Invalid ECR repository name. Repository names must be 2-256 characters and can contain only letters, numbers, hyphens, underscores, and forward slashes.'
        }
        
    # Validate role name if provided
    if role_name and not validate_role_name(role_name):
        return {
            'valid': False,
            'message': 'Invalid role name. Role names must be at most 64 characters and can contain only letters, numbers, and the following characters: +=,.@-_'
        }
        
    # Validate image tag
    if not validate_image_tag(image_tag):
        return {
            'valid': False,
            'message': 'Invalid image tag. Image tags must be at most 128 characters and can contain only letters, numbers, hyphens, underscores, periods, and plus signs.'
        }
        
    # Validate memory size
    if not validate_memory_size(memory_size):
        return {
            'valid': False,
            'message': 'Invalid memory size. Memory size must be between 128 MB and 10240 MB (10 GB) and must be a multiple of 64 MB.'
        }
        
    # Validate timeout
    if not validate_timeout(timeout):
        return {
            'valid': False,
            'message': 'Invalid timeout. Timeout must be between 1 second and 900 seconds (15 minutes).'
        }
        
    # Validate environment variables
    if environment_variables and not validate_environment_variables(environment_variables):
        return {
            'valid': False,
            'message': 'Invalid environment variables. Keys must start with a letter and contain only letters, numbers, and underscores. Total size cannot exceed 4 KB.'
        }
        
    # Validate tags
    if tags and not validate_tags(tags):
        return {
            'valid': False,
            'message': 'Invalid tags. Tag keys must be 1-128 characters. Tag values can be up to 256 characters.'
        }
        
    # Validate VPC configuration
    if vpc_config and not validate_vpc_config(vpc_config):
        return {
            'valid': False,
            'message': 'Invalid VPC configuration. VPC configuration must include subnet IDs and security group IDs.'
        }
        
    # All validations passed
    return {
        'valid': True,
        'message': 'All parameters are valid.'
    }
