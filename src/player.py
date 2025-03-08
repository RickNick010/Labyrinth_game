import pygame
from src.animated_tile import AnimatedTile
from src.footprint import FootprintManager

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
        
        # Collision box modifier - make the collision box smaller than the sprite
        # This creates a smoother experience when moving around obstacles
        self.collision_margin_x = 4  # pixels from each side horizontally
        self.collision_margin_y = 2  # pixels from top and 4 from bottom
        
        # Footprint system
        self.footprint_manager = FootprintManager(
            asset_manager,
            step_distance=12,  # Distance between footprints
            scale_factor=0.03,  # Scale footprints to 40% of original size
            lifetime=1.5       # Footprints last for 1.5 seconds
        )
        
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
        
        # Add footprints if moving
        if self.moving:
            # Add footprint at the center bottom of the player
            footprint_x = self.x + self.width // 2
            footprint_y = self.y + self.height - 2  # Slightly above the bottom
            self.footprint_manager.add_footprint(footprint_x, footprint_y, self.direction, (dx, dy))
        
        # Update footprints
        self.footprint_manager.update(dt)
        
        # Update animation state based on movement
        self.update_animation_state()
        
        # Update the sprite animation
        self.sprite.update(dt)

    def check_collision(self, tilemap):
        """
        Check if the player is colliding with any collidable tiles
        Returns True if collision detected, False otherwise
        """
        # Calculate collision box with margins
        col_x = self.x + self.collision_margin_x
        col_y = self.y + self.collision_margin_y
        col_width = self.width - (self.collision_margin_x * 2)
        col_height = self.height - (self.collision_margin_y * 2)
        
        # Check each corner of the player's collision box
        corners = [
            (col_x, col_y),  # Top-left
            (col_x + col_width - 1, col_y),  # Top-right
            (col_x, col_y + col_height - 1),  # Bottom-left
            (col_x + col_width - 1, col_y + col_height - 1)  # Bottom-right
        ]
        
        # Check center points of each edge for better collision detection
        edge_centers = [
            (col_x + col_width // 2, col_y),  # Top center
            (col_x + col_width - 1, col_y + col_height // 2),  # Right center
            (col_x + col_width // 2, col_y + col_height - 1),  # Bottom center
            (col_x, col_y + col_height // 2)  # Left center
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
        
    def draw(self, screen, camera_x=0, camera_y=0, debug=False):
        # Draw footprints first (so they appear behind the player)
        self.footprint_manager.draw(screen, camera_x, camera_y)
        
        # Draw the player sprite at the camera-adjusted position
        self.sprite.draw(screen, self.x - camera_x, self.y - camera_y)
        
        # Draw collision box in debug mode
        if debug:
            # Calculate collision box with margins
            col_x = self.x + self.collision_margin_x - camera_x
            col_y = self.y + self.collision_margin_y - camera_y
            col_width = self.width - (self.collision_margin_x * 2)
            col_height = self.height - (self.collision_margin_y * 2)
            
            # Draw the collision box as a green rectangle
            pygame.draw.rect(screen, (0, 255, 0), 
                            (col_x, col_y, col_width, col_height), 1)

