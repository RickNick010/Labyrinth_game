import pygame
import math
from src.components.asset_manager import AssetManager

class Footprint:
    """
    A class representing a single footprint that fades over time
    """
    # Class-level variables for the footprint images
    left_footprint_image = None
    right_footprint_image = None
    
    # Default scale factor for footprints
    scale_factor = 0.5
    
    # Direction to angle mapping (in degrees)
    DIRECTION_ANGLES = {
        "up": 180,
        "down": 0,
        "left": 90,
        "right": 270,
        "up_left": 225,
        "up_right": 135,
        "down_left": 315,
        "down_right": 45
    }
    
    # Offset for left/right foot placement (in pixels)
    FOOT_OFFSETS = {
        "up": (3, 0),      # 3 pixels to the side
        "down": (3, 0),    # 3 pixels to the side
        "left": (0, 3),    # 3 pixels up/down
        "right": (0, 3),   # 3 pixels up/down
        "up_left": (-2, 2),     # Diagonal offset
        "up_right": (2, 2),    # Diagonal offset
        "down_left": (2, 2),   # Diagonal offset
        "down_right": (2, -2)   # Diagonal offset
    }
    
    @classmethod
    def load_images(cls, asset_manager, scale_factor=0.5):
        """
        Load the footprint images and scale them
        
        Args:
            asset_manager: The asset manager to load images
            scale_factor: How much to scale the footprint images (1.0 = original size)
        """
        cls.scale_factor = scale_factor
        
        if cls.left_footprint_image is None:
            original = asset_manager.load_image("data/assets/tilesets/static/Effects/left_footprint.png")
            # Scale the image
            new_width = int(original.get_width() * scale_factor)
            new_height = int(original.get_height() * scale_factor)
            cls.left_footprint_image = pygame.transform.scale(original, (new_width, new_height))
            
        if cls.right_footprint_image is None:
            original = asset_manager.load_image("data/assets/tilesets/static/Effects/right_footprint.png")
            # Scale the image
            new_width = int(original.get_width() * scale_factor)
            new_height = int(original.get_height() * scale_factor)
            cls.right_footprint_image = pygame.transform.scale(original, (new_width, new_height))
    
    def __init__(self, x, y, direction, is_left_foot=True, lifetime=1.0):
        self.x = x
        self.y = y
        self.direction = direction
        self.is_left_foot = is_left_foot
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        
        # Apply offset based on direction and left/right foot
        self.apply_foot_offset()
        
        # Rotation angle based on direction
        self.rotation = self._calculate_rotation()
    
    def apply_foot_offset(self):
        """Apply an offset to the footprint position based on direction and left/right foot"""
        offset_x, offset_y = self.FOOT_OFFSETS.get(self.direction, (0, 0))
        
        # Flip the offset for left foot
        if self.is_left_foot:
            offset_x = -offset_x
            offset_y = -offset_y
            
        self.x += offset_x
        self.y += offset_y
    
    def _calculate_rotation(self):
        """Calculate the rotation angle based on direction"""
        return self.DIRECTION_ANGLES.get(self.direction, 0)
    
    def update(self, dt):
        """Update the footprint's lifetime"""
        self.lifetime -= dt
        return self.lifetime > 0
    
    def render_to_surface(self, surface, camera_x=0, camera_y=0):
        """Draw the footprint with fading effect"""
        if Footprint.left_footprint_image is None or Footprint.right_footprint_image is None:
            return
            
        # Calculate alpha based on remaining lifetime
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        
        # Choose the appropriate footprint image
        footprint_image = Footprint.left_footprint_image if self.is_left_foot else Footprint.right_footprint_image
        
        # Create a copy of the image to modify
        image_copy = footprint_image.copy()
        
        # Rotate the image
        rotated_image = pygame.transform.rotate(image_copy, self.rotation)
        
        # Set the alpha value for transparency
        rotated_image.set_alpha(alpha)
        
        # Calculate position (centered on the footprint position)
        width, height = rotated_image.get_size()
        pos_x = self.x - width // 2 - camera_x
        pos_y = self.y - height // 2 - camera_y
        
        # Draw the footprint
        surface.blit(rotated_image, (pos_x, pos_y))


class FootprintManager:
    """
    Manages a collection of footprints, adding new ones and removing old ones
    """
    def __init__(self, asset_manager, step_distance=8, scale_factor=0.5, lifetime=1.0):
        self.footprints = []
        self.step_distance = step_distance  # Distance between footprints
        self.last_footprint_pos = None
        self.left_foot = True  # Toggle between left and right feet
        self.footprint_lifetime = lifetime
        self.last_direction = None  # Track the last direction for better foot placement
        
        # Load the footprint images with scaling
        Footprint.load_images(asset_manager, scale_factor)
    
    def add_footprint(self, x, y, direction, movement_vector=None):
        """
        Add a new footprint if far enough from the last one
        
        Args:
            x, y: Position of the footprint
            direction: Primary direction (up, down, left, right)
            movement_vector: Optional (dx, dy) tuple for diagonal detection
        """
        # Determine if this is a diagonal movement
        if movement_vector:
            dx, dy = movement_vector
            # Only process if there's actual movement
            if dx != 0 and dy != 0:
                # Fix the diagonal direction detection
                if dx < 0 and dy < 0:
                    direction = "up_left"     # Moving up and left
                elif dx > 0 and dy < 0:
                    direction = "up_right"    # Moving up and right
                elif dx < 0 and dy > 0:
                    direction = "down_left"   # Moving down and left
                elif dx > 0 and dy > 0:
                    direction = "down_right"  # Moving down and right
        
        # If direction changed, reset the foot pattern
        if direction != self.last_direction and self.last_direction is not None:
            # Only reset if changing between major directions (not diagonals)
            major_directions = {"up", "down", "left", "right"}
            if direction in major_directions and self.last_direction in major_directions:
                self.left_foot = True
        
        self.last_direction = direction
        
        if self.last_footprint_pos is None:
            # First footprint
            self.footprints.append(Footprint(x, y, direction, self.left_foot, self.footprint_lifetime))
            self.last_footprint_pos = (x, y)
            self.left_foot = not self.left_foot  # Toggle foot
            return
        
        # Calculate distance from last footprint
        last_x, last_y = self.last_footprint_pos
        distance = math.sqrt((x - last_x)**2 + (y - last_y)**2)
        
        if distance >= self.step_distance:
            self.footprints.append(Footprint(x, y, direction, self.left_foot, self.footprint_lifetime))
            self.last_footprint_pos = (x, y)
            self.left_foot = not self.left_foot  # Toggle foot
    
    def update(self, dt):
        """Update all footprints and remove expired ones"""
        self.footprints = [fp for fp in self.footprints if fp.update(dt)]
    
    def render_to_surface(self, surface, camera_x=0, camera_y=0):
        """Draw all footprints"""
        for footprint in self.footprints:
            footprint.render_to_surface(surface, camera_x, camera_y) 