import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class FlowService:
    """Service for managing bot flow through configuration files"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "flow_config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Flow config not found at {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing flow config: {e}")
            return {}
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
    
    def get_flow(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Get flow configuration by name"""
        return self.config.get('flows', {}).get(flow_name)
    
    def get_message(self, flow_name: str, language: str = 'en') -> Optional[str]:
        """Get message for specific flow and language"""
        flow = self.get_flow(flow_name)
        if not flow:
            return None
        
        messages = flow.get('message', {})
        return messages.get(language, messages.get('en', ''))
    
    def get_buttons(self, flow_name: str, language: str = 'en') -> list:
        """Get buttons for specific flow and language"""
        flow = self.get_flow(flow_name)
        if not flow:
            return []
        
        buttons = flow.get('buttons', [])
        localized_buttons = []
        
        for row in buttons:
            localized_row = []
            for button in row:
                if isinstance(button.get('text'), dict):
                    text = button['text'].get(language, button['text'].get('en', ''))
                else:
                    text = button.get('text', '')
                
                localized_row.append({
                    'text': text,
                    'callback_data': button.get('callback_data', '')
                })
            localized_buttons.append(localized_row)
        
        return localized_buttons
    
    def get_error_message(self, error_type: str, language: str = 'en') -> Optional[str]:
        """Get error message by type and language"""
        error_config = self.config.get('error_handling', {}).get(error_type, {})
        messages = error_config.get('message', {})
        return messages.get(language, messages.get('en', ''))
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules"""
        return self.config.get('validation', {})
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled"""
        features = self.config.get('features', {})
        return features.get(feature_name, False)
    
    def format_message(self, flow_name: str, language: str = 'en', **kwargs) -> str:
        """Format message with placeholders"""
        message = self.get_message(flow_name, language)
        if not message:
            return ""
        
        try:
            return message.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing placeholder {e} in message for flow {flow_name}")
            return message
    
    def get_next_state(self, flow_name: str) -> Optional[str]:
        """Get next state for flow"""
        flow = self.get_flow(flow_name)
        return flow.get('next_state') if flow else None
    
    def validate_config(self) -> list:
        """Validate configuration and return errors"""
        errors = []
        
        if not self.config:
            errors.append("Configuration file is empty or invalid")
            return errors
        
        # Check required flows
        required_flows = ['welcome', 'parse_error', 'no_data']
        for flow in required_flows:
            if not self.get_flow(flow):
                errors.append(f"Missing required flow: {flow}")
        
        # Check message translations
        flows = self.config.get('flows', {})
        for flow_name, flow_config in flows.items():
            messages = flow_config.get('message', {})
            if not messages.get('en'):
                errors.append(f"Missing English message for flow: {flow_name}")
        
        return errors 