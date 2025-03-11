import pygame

class KeyMapper:
    """
    Maps string key representations from config to pygame key constants
    """
    def __init__(self, config):

        self.config = config
        
        # Create mapping from strings to pygame constants
        self.key_map = {
            # Letters
            "a": pygame.K_a, "b": pygame.K_b, "c": pygame.K_c, "d": pygame.K_d,
            "e": pygame.K_e, "f": pygame.K_f, "g": pygame.K_g, "h": pygame.K_h,
            "i": pygame.K_i, "j": pygame.K_j, "k": pygame.K_k, "l": pygame.K_l,
            "m": pygame.K_m, "n": pygame.K_n, "o": pygame.K_o, "p": pygame.K_p,
            "q": pygame.K_q, "r": pygame.K_r, "s": pygame.K_s, "t": pygame.K_t,
            "u": pygame.K_u, "v": pygame.K_v, "w": pygame.K_w, "x": pygame.K_x,
            "y": pygame.K_y, "z": pygame.K_z,
            
            # Numbers
            "0": pygame.K_0, "1": pygame.K_1, "2": pygame.K_2, "3": pygame.K_3,
            "4": pygame.K_4, "5": pygame.K_5, "6": pygame.K_6, "7": pygame.K_7,
            "8": pygame.K_8, "9": pygame.K_9,
            
            # Arrow keys
            "up": pygame.K_UP, "down": pygame.K_DOWN,
            "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
            
            # Special keys
            "space": pygame.K_SPACE, "return": pygame.K_RETURN,
            "escape": pygame.K_ESCAPE, "tab": pygame.K_TAB,
            "backspace": pygame.K_BACKSPACE, "delete": pygame.K_DELETE,
            "shift": pygame.K_LSHIFT, "rshift": pygame.K_RSHIFT,
            "ctrl": pygame.K_LCTRL, "rctrl": pygame.K_RCTRL,
            "alt": pygame.K_LALT, "ralt": pygame.K_RALT
        }
    
    def get_key(self, key_string):
        """
        Get the pygame key constant for a key string
        
        Args:
            key_string: String representation of the key
            
        Returns:
            The pygame key constant, or None if not found
        """
        return self.key_map.get(key_string.lower())
    
    def get_config_key(self, config_key, default_key_string=""):
        """
        Get the pygame key constant for a config key
        
        Args:
            config_key: The key in the config file
            default_key_string: Default key string if config key is not found
            
        Returns:
            The pygame key constant, or None if not found
        """
        key_string = self.config.get(config_key, default_key_string)
        return self.get_key(key_string)
    
    def get_control_dict(self, control_map):
        """
        Create a dictionary of control keys from a mapping
        
        Args:
            control_map: Dictionary mapping control names to config keys
                Example: {"up": "PLAYER_MOV_UP", "up_alt": "PLAYER_MOV_UP_ALT"}
                
        Returns:
            Dictionary mapping control names to pygame key constants
        """
        controls = {}
        for control_name, config_key in control_map.items():
            controls[control_name] = self.get_config_key(config_key)
        return controls 