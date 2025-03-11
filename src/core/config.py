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
            if not os.path.isabs(self.config_path):
                # Try current directory
                if os.path.exists(self.config_path):
                    path = self.config_path
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
            """If config file cannot be loaded, create a new one with default values"""  
            self.config = {
                "SCREEN_WIDTH": 1920,
                "SCREEN_HEIGHT": 1080,
                "PLAYER_SPEED": 600,
                "PLAYER_SIZE": 40
            }
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f)
            print("Using default configuration")
    
    def get(self, key, default=None):
        """Get a configuration value by key"""
        return self.config.get(key, default)
    
    def __getitem__(self, key):
        """Allow dictionary-like access to config values"""
        return self.config.get(key) 