import pygame
from src.animated_tile import AnimatedTile

class Player:
    def __init__(self, x, y, asset_manager, map_width=0, map_height=0):
        self.x = x
        self.y = y
        # Store float positions for smooth movement calculations
        self.float_x = float(x)
        self.float_y = float(y)
        
        # Character tileset path
        self.character_tileset = "data/assets/tilesets/animated/Main_Character/Basic Charakter Spritesheet.tsj"
        
        # Load the character tileset to get dimensions
        tileset = asset_manager.load_tileset(self.character_tileset)
        self.width = tileset.get('tilewidth', 16)
        self.height = tileset.get('tileheight', 16)
        self.speed = 2
        
        # Map boundaries
        self.map_width = map_width
        self.map_height = map_height
        
        # Movement state
        self.moving = False
        self.direction = "down"  # down, up, left, right
        
        # Create the animated tile for the player
        self.sprite = AnimatedTile(
            asset_manager, 
            self.character_tileset,
            14  # Starting tile ID (down movement animation)
        )
        
        # Set initial direction and state
        self.update_animation_state()
        
    def set_map_boundaries(self, map_width, map_height):
        """
        Set the map boundaries to constrain player movement
        """
        self.map_width = map_width
        self.map_height = map_height
        
    def update_animation_state(self):
        """
        Update the animation based on movement state and direction
        """
        state = "movement" if self.moving else "idle"
        self.sprite.set_direction_and_state(self.direction, state)
        
    def update(self, keys, dt=1/60, tilemap=None):
        # Previous position for movement detection
        prev_x, prev_y = self.x, self.y
        
        # Track movement in each direction
        moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        moving_up = keys[pygame.K_w] or keys[pygame.K_UP]
        moving_down = keys[pygame.K_s] or keys[pygame.K_DOWN]
        
        # Calculate movement vector
        dx, dy = 0, 0
        
        if moving_left:
            dx -= 1
        if moving_right:
            dx += 1
        if moving_up:
            dy -= 1
        if moving_down:
            dy += 1
            
        # Normalize diagonal movement to maintain consistent speed
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        
        # Store current position before movement
        old_float_x = self.float_x
        old_float_y = self.float_y
        
        # Calculate new float position
        new_float_x = self.float_x + dx * self.speed
        new_float_y = self.float_y + dy * self.speed
        
        # Check map boundaries if they are set
        if self.map_width > 0 and self.map_height > 0:
            # Constrain to map boundaries, accounting for player size
            new_float_x = max(0, min(new_float_x, self.map_width - self.width))
            new_float_y = max(0, min(new_float_y, self.map_height - self.height))
        
        # Check for collisions if a tilemap is provided
        if tilemap:
            # Try horizontal movement first
            self.float_x = new_float_x
            self.x = int(self.float_x)
            
            # Check for collision in horizontal movement
            if self.check_collision(tilemap):
                # Revert horizontal movement if collision detected
                self.float_x = old_float_x
                self.x = int(self.float_x)
            
            # Try vertical movement
            self.float_y = new_float_y
            self.y = int(self.float_y)
            
            # Check for collision in vertical movement
            if self.check_collision(tilemap):
                # Revert vertical movement if collision detected
                self.float_y = old_float_y
                self.y = int(self.float_y)
        else:
            # No tilemap for collision, just apply movement
            self.float_x = new_float_x
            self.float_y = new_float_y
            self.x = int(self.float_x)
            self.y = int(self.float_y)
        
        # Determine direction based on movement
        if dx != 0 or dy != 0:
            # Prioritize the dominant direction for animation
            if abs(dx) > abs(dy):
                # Horizontal movement is dominant
                self.direction = "right" if dx > 0 else "left"
            else:
                # Vertical movement is dominant
                self.direction = "down" if dy > 0 else "up"
        
        # Determine if moving
        self.moving = (prev_x != self.x or prev_y != self.y)
        
        # Update animation state based on movement
        self.update_animation_state()
        
        # Update the sprite animation
        self.sprite.update(dt)

    def check_collision(self, tilemap):
        """
        Check if the player is colliding with any collidable tiles
        Returns True if collision detected, False otherwise
        """
        # Check each corner of the player's hitbox
        corners = [
            (self.x, self.y),  # Top-left
            (self.x + self.width - 1, self.y),  # Top-right
            (self.x, self.y + self.height - 1),  # Bottom-left
            (self.x + self.width - 1, self.y + self.height - 1)  # Bottom-right
        ]
        
        # Check center points of each edge for better collision detection
        edge_centers = [
            (self.x + self.width // 2, self.y),  # Top center
            (self.x + self.width - 1, self.y + self.height // 2),  # Right center
            (self.x + self.width // 2, self.y + self.height - 1),  # Bottom center
            (self.x, self.y + self.height // 2)  # Left center
        ]
        
        # Combine all points to check
        check_points = corners + edge_centers
        
        # Check if any of these points are in a collidable tile
        for point_x, point_y in check_points:
            tile_x = point_x // tilemap.tile_width
            tile_y = point_y // tilemap.tile_height
            
            if tilemap.is_position_collidable(point_x, point_y):
                print(f"Collision detected at ({point_x}, {point_y}) - Tile ({tile_x}, {tile_y})")
                return True
        
        return False
        
    def draw(self, screen, camera_x=0, camera_y=0):
        # Draw the player sprite at the camera-adjusted position
        self.sprite.draw(screen, self.x - camera_x, self.y - camera_y)

