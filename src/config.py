import json
import os

class Config:
    """
    Loads and manages game configuration from a JSON file
    """
    def __init__(self, config_path="data/config.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            # Find the config file relative to the current directory
            if not os.path.isabs(self.config_path):
                # Try current directory
                if os.path.exists(self.config_path):
                    path = self.config_path
                # Try one directory up (if running from src/)
                elif os.path.exists(os.path.join("..", self.config_path)):
                    path = os.path.join("..", self.config_path)
                else:
                    raise FileNotFoundError(f"Config file not found: {self.config_path}")
            else:
                path = self.config_path
                
            with open(path, 'r') as f:
                self.config = json.load(f)
                print(f"Loaded configuration from {path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            # Set default values
            self.config = {
                "SCREEN_WIDTH": 1000,
                "SCREEN_HEIGHT": 1000,
                "PLAYER_SPEED": 600,
                "PLAYER_SIZE": 40
            }
            print("Using default configuration")
    
    def get(self, key, default=None):
        """Get a configuration value by key"""
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        """Allow dictionary-like access to config values"""
        return self.config.get(key) 