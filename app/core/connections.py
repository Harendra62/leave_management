import logging
from typing import Optional, Dict, Any
from functools import wraps
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class LazyConnectionManager:
    """Base class for lazy connection managers"""
    
    def __init__(self):
        self._connection = None
        self._is_connected = False
    
    def _ensure_connection(self):
        """Ensure connection is established before use"""
        if not self._is_connected:
            self._connect()
    
    def _connect(self):
        """Override in subclasses to implement connection logic"""
        raise NotImplementedError
    
    def close(self):
        """Close the connection"""
        if self._connection and self._is_connected:
            try:
                self._connection.close()
                self._is_connected = False
                self._connection = None
                logger.info("Connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


class ValkeyRedisManager(LazyConnectionManager):
    """Lazy connection manager for AWS Valkey Redis"""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
    
    def _connect(self):
        """Establish connection to AWS Valkey Redis"""
        try:
            if not self.settings.AWS_VALKEY_ENDPOINT:
                raise ValueError("AWS_VALKEY_ENDPOINT not configured")
            
            connection_kwargs = {
                'host': self.settings.AWS_VALKEY_ENDPOINT,
                'port': self.settings.AWS_VALKEY_PORT,
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30
            }
            
            # Add authentication if provided
            if self.settings.AWS_VALKEY_USERNAME and self.settings.AWS_VALKEY_PASSWORD:
                connection_kwargs['username'] = self.settings.AWS_VALKEY_USERNAME
                connection_kwargs['password'] = self.settings.AWS_VALKEY_PASSWORD
            
            # Add TLS if enabled
            if self.settings.AWS_VALKEY_TLS:
                connection_kwargs['ssl'] = True
                connection_kwargs['ssl_cert_reqs'] = None
            
            self._connection = redis.Redis(**connection_kwargs)
            
            # Test connection
            self._connection.ping()
            self._is_connected = True
            logger.info("Successfully connected to AWS Valkey Redis")
            
        except Exception as e:
            logger.error(f"Failed to connect to AWS Valkey Redis: {e}")
            self._is_connected = False
            raise
    
    def get_connection(self):
        """Get Redis connection, establishing it if necessary"""
        self._ensure_connection()
        return self._connection
    
    def execute_command(self, command: str, *args, **kwargs):
        """Execute a Redis command with automatic connection management"""
        try:
            conn = self.get_connection()
            return conn.execute_command(command, *args, **kwargs)
        except redis.ConnectionError:
            logger.warning("Redis connection lost, attempting to reconnect...")
            self._is_connected = False
            self._connect()
            conn = self.get_connection()
            return conn.execute_command(command, *args, **kwargs)
    
    def set(self, key: str, value: str, ex: Optional[int] = None):
        """Set a key-value pair in Redis"""
        return self.execute_command('SET', key, value, ex=ex)
    
    def get(self, key: str) -> Optional[str]:
        """Get a value by key from Redis"""
        return self.execute_command('GET', key)
    
    def delete(self, key: str) -> int:
        """Delete a key from Redis"""
        return self.execute_command('DEL', key)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        return bool(self.execute_command('EXISTS', key))


class DynamoDBManager(LazyConnectionManager):
    """Lazy connection manager for AWS DynamoDB"""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self._resource = None
        self._client = None
    
    def _connect(self):
        """Establish connection to AWS DynamoDB"""
        try:
            # Configure AWS credentials and region
            aws_config = {
                'region_name': self.settings.AWS_DYNAMODB_REGION
            }
            
            # Add custom endpoint for local development/testing
            if self.settings.AWS_DYNAMODB_ENDPOINT_URL:
                aws_config['endpoint_url'] = self.settings.AWS_DYNAMODB_ENDPOINT_URL
            
            # Add explicit credentials if provided
            if (self.settings.AWS_DYNAMODB_ACCESS_KEY_ID and 
                self.settings.AWS_DYNAMODB_SECRET_ACCESS_KEY):
                aws_config['aws_access_key_id'] = self.settings.AWS_DYNAMODB_ACCESS_KEY_ID
                aws_config['aws_secret_access_key'] = self.settings.AWS_DYNAMODB_SECRET_ACCESS_KEY
            
            # Create DynamoDB resource and client
            self._resource = boto3.resource('dynamodb', **aws_config)
            self._client = boto3.client('dynamodb', **aws_config)
            
            # Test connection by listing tables
            self._client.list_tables(Limit=1)
            self._is_connected = True
            self._connection = self._resource
            logger.info("Successfully connected to AWS DynamoDB")
            
        except (NoCredentialsError, ClientError) as e:
            logger.error(f"Failed to connect to AWS DynamoDB: {e}")
            self._is_connected = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to DynamoDB: {e}")
            self._is_connected = False
            raise
    
    def get_resource(self):
        """Get DynamoDB resource, establishing connection if necessary"""
        self._ensure_connection()
        return self._resource
    
    def get_client(self):
        """Get DynamoDB client, establishing connection if necessary"""
        self._ensure_connection()
        return self._client
    
    def get_table(self, table_name: str):
        """Get a DynamoDB table by name"""
        full_table_name = f"{self.settings.AWS_DYNAMODB_TABLE_PREFIX}{table_name}"
        return self.get_resource().Table(full_table_name)
    
    def create_table(self, table_name: str, key_schema: list, attribute_definitions: list, **kwargs):
        """Create a new DynamoDB table"""
        full_table_name = f"{self.settings.AWS_DYNAMODB_TABLE_PREFIX}{table_name}"
        return self.get_resource().create_table(
            TableName=full_table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            **kwargs
        )
    
    def put_item(self, table_name: str, item: Dict[str, Any]):
        """Put an item in a DynamoDB table"""
        table = self.get_table(table_name)
        return table.put_item(Item=item)
    
    def get_item(self, table_name: str, key: Dict[str, Any]):
        """Get an item from a DynamoDB table"""
        table = self.get_table(table_name)
        return table.get_item(Key=key)
    
    def update_item(self, table_name: str, key: Dict[str, Any], **kwargs):
        """Update an item in a DynamoDB table"""
        table = self.get_table(table_name)
        return table.update_item(Key=key, **kwargs)
    
    def delete_item(self, table_name: str, key: Dict[str, Any]):
        """Delete an item from a DynamoDB table"""
        table = self.get_table(table_name)
        return table.delete_item(Key=key)
    
    def query(self, table_name: str, **kwargs):
        """Query items from a DynamoDB table"""
        table = self.get_table(table_name)
        return table.query(**kwargs)
    
    def scan(self, table_name: str, **kwargs):
        """Scan items from a DynamoDB table"""
        table = self.get_table(table_name)
        return table.scan(**kwargs)


# Global instances for lazy initialization
valkey_manager = ValkeyRedisManager()
dynamodb_manager = DynamoDBManager()


def with_redis_connection(func):
    """Decorator to ensure Redis connection is available for function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            valkey_manager._ensure_connection()
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            raise
    return wrapper


def with_dynamodb_connection(func):
    """Decorator to ensure DynamoDB connection is available for function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            dynamodb_manager._ensure_connection()
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"DynamoDB operation failed: {e}")
            raise
    return wrapper


def close_all_connections():
    """Close all active connections"""
    valkey_manager.close()
    dynamodb_manager.close()
    logger.info("All connections closed") 