import pygame
from src.components.animations import AnimatedTile
from src.effects.footprint import FootprintManager
from src.core.config import Config


class Player:
    def __init__(self, x, y, asset_manager, config, map_width=0, map_height=0):
        self.x = x
        self.y = y
        # Store float positions for smooth movement calculations
        self.float_x = float(x)
        self.float_y = float(y)
        
        # Store config reference
        self.config = config
        
        # Character tileset path
        self.character_tileset = "data/assets/tilesets/animated/Main_Character/Basic Charakter Spritesheet.tsj"
        
        # Load the character tileset to get dimensions
        tileset = asset_manager.load_tileset(self.character_tileset)
        self.width = tileset.get('tilewidth', 16)
        self.height = tileset.get('tileheight', 16)
        
        # Get player speed from config
        self.speed = config.get("PLAYER_SPEED", 600) / 300  # Convert to pixels per frame
        
        # Map key strings to pygame constants
        self.key_mapping = {
            "K_UP": pygame.K_UP,
            "K_DOWN": pygame.K_DOWN,
            "K_LEFT": pygame.K_LEFT,
            "K_RIGHT": pygame.K_RIGHT,
            "K_w": pygame.K_w,
            "K_a": pygame.K_a,
            "K_s": pygame.K_s,
            "K_d": pygame.K_d
        }
        
        # Collision box modifier - make the collision box smaller than the sprite
        self.collision_margin_x = 4  # pixels from each side horizontally
        self.collision_margin_y = 4  # pixels from top and 4 from bottom
        
        # Footprint system
        self.footprint_manager = FootprintManager(
            asset_manager,
            step_distance=12,  # Distance between footprints
            scale_factor=0.03,  # Scale footprints to 3% of original size
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
        
        # Cached collision points for optimization
        self.collision_points = []
        self._update_collision_points()
        
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
        
        # Get key constants from config strings
        key_left = self.key_mapping.get(self.config.get("PLAYER_MOV_LEFT", "K_LEFT"))
        key_left_alt = self.key_mapping.get(self.config.get("PLAYER_MOV_LEFT_ALT", "K_a"))
        key_right = self.key_mapping.get(self.config.get("PLAYER_MOV_RIGHT", "K_RIGHT"))
        key_right_alt = self.key_mapping.get(self.config.get("PLAYER_MOV_RIGHT_ALT", "K_d"))
        key_up = self.key_mapping.get(self.config.get("PLAYER_MOV_UP", "K_UP"))
        key_up_alt = self.key_mapping.get(self.config.get("PLAYER_MOV_UP_ALT", "K_w"))
        key_down = self.key_mapping.get(self.config.get("PLAYER_MOV_DOWN", "K_DOWN"))
        key_down_alt = self.key_mapping.get(self.config.get("PLAYER_MOV_DOWN_ALT", "K_s"))
        
        # Track movement in each direction
        moving_left = keys[key_left] or keys[key_left_alt]
        moving_right = keys[key_right] or keys[key_right_alt]
        moving_up = keys[key_up] or keys[key_up_alt]
        moving_down = keys[key_down] or keys[key_down_alt]
        
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
            # Use smaller step size for more accurate collision detection
            step_size = min(self.speed / 2, 1.0)  # Smaller steps for thin barriers
            
            # Calculate number of steps needed
            total_dx = new_float_x - old_float_x
            total_dy = new_float_y - old_float_y
            steps = max(1, int(max(abs(total_dx), abs(total_dy)) / step_size))
            
            # Move in small increments to prevent clipping
            for step in range(1, steps + 1):
                # Calculate intermediate position
                step_x = old_float_x + (total_dx * step / steps)
                step_y = old_float_y + (total_dy * step / steps)
                
                # Try horizontal movement
                self.float_x = step_x
                self.x = int(self.float_x)
                
                # Check for collision in horizontal movement
                if self.check_collision(tilemap):
                    # Revert horizontal movement if collision detected
                    self.float_x = old_float_x
                    self.x = int(self.float_x)
                    break
                
                # Try vertical movement
                self.float_y = step_y
                self.y = int(self.float_y)
                
                # Check for collision in vertical movement
                if self.check_collision(tilemap):
                    # Revert vertical movement if collision detected
                    self.float_y = old_float_y
                    self.y = int(self.float_y)
                    break
                
                # Update old position for next step
                old_float_x = self.float_x
                old_float_y = self.float_y
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

    def _update_collision_points(self):
        """
        Update the collision points for the player
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
        self.collision_points = corners + edge_centers

    def check_collision(self, tilemap):
        """
        Optimized collision check - checks only necessary points
        """
        # Update collision points
        self._update_collision_points()
        
        # Broadphase - get player boundaries
        min_x = min(point[0] for point in self.collision_points)
        min_y = min(point[1] for point in self.collision_points)
        max_x = max(point[0] for point in self.collision_points)
        max_y = max(point[1] for point in self.collision_points)
        
        # Check if there is a collision with tiles within boundaries
        for tile_y in range(min_y // tilemap.tile_height, max_y // tilemap.tile_height + 1):
            for tile_x in range(min_x // tilemap.tile_width, max_x // tilemap.tile_width + 1):
                if 0 <= tile_x < tilemap.map_width and 0 <= tile_y < tilemap.map_height:
                    # If tile is collidable, check more closely
                    index = tile_y * tilemap.map_width + tile_x
                    if index < len(tilemap.collision_manager.collision_map) and tilemap.collision_manager.collision_map[index]:
                        # Narrowphase - check specific points
                        for point_x, point_y in self.collision_points:
                            if (tile_x * tilemap.tile_width <= point_x < (tile_x + 1) * tilemap.tile_width and
                                tile_y * tilemap.tile_height <= point_y < (tile_y + 1) * tilemap.tile_height):
                                return True
        
        # Check collision with objects
        for point_x, point_y in self.collision_points:
            if tilemap.is_position_collidable(point_x, point_y):
                return True
        
        return False
        
    def render_to_surface(self, surface, camera_x=0, camera_y=0, debug=False):
        """
        Render player to the provided surface
        
        Args:
            surface: The surface to render to
            camera_x, camera_y: Camera offset
            debug: Whether to show debug visualization
        """
        # Note: Footprints are now handled by the renderer directly
        # so we don't need to render them here
        
        # Draw the player sprite at the camera-adjusted position
        self.sprite.render_to_surface(surface, self.x - camera_x, self.y - camera_y)
        
        # Draw collision box in debug mode
        if debug:
            # Calculate collision box with margins
            col_x = self.x + self.collision_margin_x - camera_x
            col_y = self.y + self.collision_margin_y - camera_y
            col_width = self.width - (self.collision_margin_x * 2)
            col_height = self.height - (self.collision_margin_y * 2)
            
            # Draw the collision box as a green rectangle
            pygame.draw.rect(surface, (0, 255, 0), 
                           (col_x, col_y, col_width, col_height), 1)


