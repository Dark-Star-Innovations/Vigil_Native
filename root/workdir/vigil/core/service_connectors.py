"""
VIGIL - Service Connectors
Connectors for various platforms and services
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from abc import ABC, abstractmethod
import requests


@dataclass
class ServiceConfig:
    """Configuration for a service connector."""
    name: str
    url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ServiceConnector(ABC):
    """Base class for service connectors."""
    
    def __init__(self, config: ServiceConfig):
        """Initialize connector with configuration."""
        self.config = config
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with authentication and headers."""
        if self.config.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.config.api_key}'
        
        for key, value in self.config.custom_headers.items():
            self.session.headers[key] = value
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the connection to the service works."""
        pass
    
    @abstractmethod
    def get_data(self, endpoint: str, **kwargs) -> Optional[Dict]:
        """Generic method to get data from the service."""
        pass
    
    @abstractmethod
    def post_data(self, endpoint: str, data: Dict, **kwargs) -> Optional[Dict]:
        """Generic method to post data to the service."""
        pass


class TaskadeConnector(ServiceConnector):
    """Connector for Taskade."""
    
    def __init__(self, api_key: str):
        config = ServiceConfig(
            name="Taskade",
            url="https://www.taskade.com/api/v1",
            api_key=api_key
        )
        super().__init__(config)
    
    def test_connection(self) -> bool:
        try:
            response = self.session.get(f"{self.config.url}/user")
            return response.status_code == 200
        except:
            return False
    
    def get_data(self, endpoint: str, **kwargs) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.config.url}/{endpoint}", **kwargs)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def post_data(self, endpoint: str, data: Dict, **kwargs) -> Optional[Dict]:
        try:
            response = self.session.post(f"{self.config.url}/{endpoint}", json=data, **kwargs)
            return response.json() if response.status_code in [200, 201] else None
        except:
            return None


class GitHubConnector(ServiceConnector):
    """Connector for GitHub."""
    
    def __init__(self, api_key: str):
        config = ServiceConfig(
            name="GitHub",
            url="https://api.github.com",
            api_key=api_key,
            custom_headers={"Accept": "application/vnd.github.v3+json"}
        )
        super().__init__(config)
    
    def test_connection(self) -> bool:
        try:
            response = self.session.get(f"{self.config.url}/user")
            return response.status_code == 200
        except:
            return False
    
    def get_data(self, endpoint: str, **kwargs) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.config.url}/{endpoint}", **kwargs)
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def post_data(self, endpoint: str, data: Dict, **kwargs) -> Optional[Dict]:
        try:
            response = self.session.post(f"{self.config.url}/{endpoint}", json=data, **kwargs)
            return response.json() if response.status_code in [200, 201] else None
        except:
            return None


class CustomConnector(ServiceConnector):
    """
    Generic connector for custom/unorthodox websites.
    Allows users to add any service with custom configuration.
    """
    
    def __init__(
        self,
        name: str,
        url: str,
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        auth_type: str = "bearer",  # bearer, basic, custom
        **kwargs
    ):
        config = ServiceConfig(
            name=name,
            url=url,
            api_key=api_key,
            custom_headers=custom_headers or {},
            metadata=kwargs
        )
        self.auth_type = auth_type
        super().__init__(config)
    
    def _setup_session(self):
        """Setup session with custom authentication."""
        if self.config.api_key:
            if self.auth_type == "bearer":
                self.session.headers['Authorization'] = f'Bearer {self.config.api_key}'
            elif self.auth_type == "basic":
                self.session.headers['Authorization'] = f'Basic {self.config.api_key}'
            elif self.auth_type == "api-key":
                self.session.headers['X-API-Key'] = self.config.api_key
        
        for key, value in self.config.custom_headers.items():
            self.session.headers[key] = value
    
    def test_connection(self) -> bool:
        try:
            response = self.session.get(self.config.url)
            return response.status_code in [200, 301, 302]
        except:
            return False
    
    def get_data(self, endpoint: str, **kwargs) -> Optional[Dict]:
        try:
            url = f"{self.config.url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = self.session.get(url, **kwargs)
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {"content": response.text, "status": response.status_code}
            return None
        except Exception as e:
            print(f"Error getting data from {self.config.name}: {e}")
            return None
    
    def post_data(self, endpoint: str, data: Dict, **kwargs) -> Optional[Dict]:
        try:
            url = f"{self.config.url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = self.session.post(url, json=data, **kwargs)
            if response.status_code in [200, 201]:
                try:
                    return response.json()
                except:
                    return {"content": response.text, "status": response.status_code}
            return None
        except Exception as e:
            print(f"Error posting data to {self.config.name}: {e}")
            return None


class ConnectorManager:
    """
    Manages all service connectors for Vigil.
    Handles registration, storage, and retrieval of connectors.
    """
    
    # Pre-configured platform endpoints
    PLATFORM_CONFIGS = {
        "taskade": {
            "name": "Taskade",
            "url": "https://www.taskade.com/api/v1",
            "auth_type": "bearer",
            "env_key": "TASKADE_API_KEY"
        },
        "youtube": {
            "name": "YouTube",
            "url": "https://www.googleapis.com/youtube/v3",
            "auth_type": "bearer",
            "env_key": "YOUTUBE_API_KEY"
        },
        "facebook": {
            "name": "Facebook",
            "url": "https://graph.facebook.com/v18.0",
            "auth_type": "bearer",
            "env_key": "FACEBOOK_ACCESS_TOKEN"
        },
        "stripe": {
            "name": "Stripe",
            "url": "https://api.stripe.com/v1",
            "auth_type": "bearer",
            "env_key": "STRIPE_API_KEY"
        },
        "shopify": {
            "name": "Shopify",
            "url": "https://{shop}.myshopify.com/admin/api/2024-01",
            "auth_type": "bearer",
            "env_key": "SHOPIFY_ACCESS_TOKEN"
        },
        "github": {
            "name": "GitHub",
            "url": "https://api.github.com",
            "auth_type": "bearer",
            "env_key": "GITHUB_TOKEN"
        },
        "gmail": {
            "name": "Gmail",
            "url": "https://gmail.googleapis.com/gmail/v1",
            "auth_type": "bearer",
            "env_key": "GMAIL_API_KEY"
        },
        "openai": {
            "name": "OpenAI",
            "url": "https://api.openai.com/v1",
            "auth_type": "bearer",
            "env_key": "OPENAI_API_KEY"
        },
        "aws": {
            "name": "AWS",
            "url": "https://aws.amazon.com",
            "auth_type": "custom",
            "env_key": "AWS_ACCESS_KEY"
        },
        "capcut": {
            "name": "CapCut",
            "url": "https://www.capcut.com/api",
            "auth_type": "bearer",
            "env_key": "CAPCUT_API_KEY"
        },
        "canva": {
            "name": "Canva",
            "url": "https://api.canva.com/rest/v1",
            "auth_type": "bearer",
            "env_key": "CANVA_API_KEY"
        },
        "replit": {
            "name": "Replit",
            "url": "https://replit.com/api/v0",
            "auth_type": "bearer",
            "env_key": "REPLIT_API_KEY"
        }
    }
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize connector manager."""
        self.storage_path = storage_path or Path.home() / ".vigil" / "connectors"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.connectors_file = self.storage_path / "connectors.json"
        self.connectors: Dict[str, ServiceConnector] = {}
        
        self._load_connectors()
    
    def _load_connectors(self):
        """Load connector configurations from disk and environment."""
        # Load custom connectors from file
        if self.connectors_file.exists():
            try:
                with open(self.connectors_file, 'r') as f:
                    configs = json.load(f)
                    for name, config_data in configs.items():
                        self._create_connector_from_config(name, config_data)
            except Exception as e:
                print(f"Error loading connectors: {e}")
        
        # Auto-configure from environment variables
        self._auto_configure_from_env()
    
    def _auto_configure_from_env(self):
        """Auto-configure connectors from environment variables."""
        for platform_key, platform_config in self.PLATFORM_CONFIGS.items():
            env_key = platform_config.get("env_key")
            if env_key and os.getenv(env_key):
                if platform_key not in self.connectors:
                    self.add_platform_connector(
                        platform_key,
                        os.getenv(env_key)
                    )
    
    def _create_connector_from_config(self, name: str, config: Dict):
        """Create a connector from configuration dictionary."""
        try:
            connector = CustomConnector(
                name=config.get("name", name),
                url=config["url"],
                api_key=config.get("api_key"),
                custom_headers=config.get("custom_headers", {}),
                auth_type=config.get("auth_type", "bearer")
            )
            self.connectors[name] = connector
        except Exception as e:
            print(f"Error creating connector {name}: {e}")
    
    def _save_connectors(self):
        """Save connector configurations to disk."""
        try:
            configs = {}
            for name, connector in self.connectors.items():
                if isinstance(connector, CustomConnector):
                    configs[name] = {
                        "name": connector.config.name,
                        "url": connector.config.url,
                        "api_key": connector.config.api_key,
                        "custom_headers": connector.config.custom_headers,
                        "auth_type": connector.auth_type
                    }
            
            with open(self.connectors_file, 'w') as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            print(f"Error saving connectors: {e}")
    
    def add_platform_connector(self, platform: str, api_key: str, **kwargs) -> bool:
        """Add a pre-configured platform connector."""
        if platform not in self.PLATFORM_CONFIGS:
            print(f"Unknown platform: {platform}")
            return False
        
        config = self.PLATFORM_CONFIGS[platform]
        
        # Handle special cases like Shopify that need shop name
        url = config["url"]
        if "{shop}" in url and "shop" in kwargs:
            url = url.format(shop=kwargs["shop"])
        
        connector = CustomConnector(
            name=config["name"],
            url=url,
            api_key=api_key,
            auth_type=config["auth_type"],
            **kwargs
        )
        
        self.connectors[platform] = connector
        self._save_connectors()
        return True
    
    def add_custom_connector(
        self,
        name: str,
        url: str,
        api_key: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        auth_type: str = "bearer"
    ) -> bool:
        """Add a custom connector for any website."""
        try:
            connector = CustomConnector(
                name=name,
                url=url,
                api_key=api_key,
                custom_headers=custom_headers or {},
                auth_type=auth_type
            )
            
            self.connectors[name.lower()] = connector
            self._save_connectors()
            return True
        except Exception as e:
            print(f"Error adding custom connector: {e}")
            return False
    
    def get_connector(self, name: str) -> Optional[ServiceConnector]:
        """Get a connector by name."""
        return self.connectors.get(name.lower())
    
    def list_connectors(self) -> List[str]:
        """List all available connectors."""
        return list(self.connectors.keys())
    
    def test_connector(self, name: str) -> bool:
        """Test a connector."""
        connector = self.get_connector(name)
        if not connector:
            return False
        return connector.test_connection()
    
    def remove_connector(self, name: str) -> bool:
        """Remove a connector."""
        if name.lower() in self.connectors:
            del self.connectors[name.lower()]
            self._save_connectors()
            return True
        return False
    
    def get_available_platforms(self) -> List[str]:
        """Get list of pre-configured platforms."""
        return list(self.PLATFORM_CONFIGS.keys())


if __name__ == "__main__":
    # Test connector manager
    cm = ConnectorManager()
    
    print("Available pre-configured platforms:")
    for platform in cm.get_available_platforms():
        print(f"  - {platform}")
    
    print("\nAdding a custom connector...")
    cm.add_custom_connector(
        name="MyCustomAPI",
        url="https://api.example.com",
        api_key="test-key-123",
        auth_type="bearer"
    )
    
    print("\nActive connectors:")
    for connector_name in cm.list_connectors():
        print(f"  - {connector_name}")
    
    print("\nTesting custom connector...")
    connector = cm.get_connector("mycustomapi")
    if connector:
        print(f"  Connector found: {connector.config.name}")
        print(f"  URL: {connector.config.url}")
