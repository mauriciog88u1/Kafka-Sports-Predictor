"""Schema validation utilities."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from jsonschema import validate, ValidationError
from jsonschema.validators import validator_for

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass


class SchemaValidator:
    """Schema validator for match updates and predictions."""
    
    def __init__(self):
        """Initialize the schema validator."""
        self.schemas = {}
        self._load_schemas()
    
    def _load_schemas(self) -> None:
        """Load JSON schemas from the static directory."""
        schema_dir = Path(__file__).parent.parent.parent / 'tests' / 'static' / 'schemas'
        
        for schema_file in schema_dir.glob('*.json'):
            with open(schema_file, 'r') as f:
                schema = json.load(f)
                schema_name = schema_file.stem
                self.schemas[schema_name] = schema
                
                # Create a validator for the schema
                validator_class = validator_for(schema)
                validator_class.check_schema(schema)
                self.schemas[f"{schema_name}_validator"] = validator_class(schema)
    
    def validate_match_update(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate a match update against the schema.
        
        Args:
            data: The match update data to validate
            
        Returns:
            The validated data if successful
            
        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            validate(instance=data, schema=self.schemas['match_update'])
            logger.debug("Match update validation successful")
            return data
        except ValidationError as e:
            logger.error(f"Match update validation failed: {str(e)}")
            raise SchemaValidationError(f"Invalid match update: {str(e)}")
    
    def validate_prediction_response(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate a prediction response against the schema.
        
        Args:
            data: The prediction response data to validate
            
        Returns:
            The validated data if successful
            
        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            validate(instance=data, schema=self.schemas['prediction_response'])
            logger.debug("Prediction response validation successful")
            return data
        except ValidationError as e:
            logger.error(f"Prediction response validation failed: {str(e)}")
            raise SchemaValidationError(f"Invalid prediction response: {str(e)}")
    
    def get_schema_errors(self, data: Dict[str, Any], schema_name: str) -> list:
        """Get detailed validation errors for a given schema.
        
        Args:
            data: The data to validate
            schema_name: Name of the schema to validate against
            
        Returns:
            List of validation errors
        """
        errors = []
        validator = self.schemas.get(f"{schema_name}_validator")
        
        if validator:
            for error in validator.iter_errors(data):
                errors.append({
                    'path': list(error.path),
                    'message': error.message,
                    'validator': error.validator,
                    'validator_value': error.validator_value
                })
        
        return errors 