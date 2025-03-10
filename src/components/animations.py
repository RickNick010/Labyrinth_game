import pygame

class AnimatedTile:
    """
    A universal class to handle animated tiles from tilesets.
    Works for both map tiles and character sprites.
    """
    def __init__(self, asset_manager, tileset_path, tile_id=0, properties=None):
        self.asset_manager = asset_manager
        self.tileset_path = tileset_path
        self.tile_id = tile_id
        self.properties = properties or {}
        
        # Load the tileset
        self.tileset_data = asset_manager.load_tileset(tileset_path)
        
        # Animation state
        self.current_frame = 0
        self.animation_timer = 0
        self.frames = []
        self.durations = []
        self.total_duration = 0
        self.is_animated = False
        
        # Direction and state for character animations
        self.direction = self.properties.get('direction', 'down')
        self.state = self.properties.get('state', 'idle')
        
        # Dictionary to store animations by direction and state
        self.directional_animations = {}
        
        # Load the animation data
        self._load_animation()
    
    def _load_animation(self):
        """
        Load animation data for this specific tile
        """
        if not self.tileset_data:
            return
            
        # Check if this tile has animation data in the tileset
        animation_name = f"tile_{self.tile_id}"
        animation_data = self.asset_manager.get_animation(self.tileset_path, animation_name)
        
        if animation_data:
            self.frames = animation_data['frames']
            self.durations = animation_data['durations']
            self.total_duration = animation_data['total_duration']
            self.is_animated = True
            print(f"Loaded animation for tile {self.tile_id} with {len(self.frames)} frames")
        else:
            # No animation data, use the tile as a static image
            self.frames = [self.tile_id]
            self.durations = [1.0]
            self.is_animated = False
            
        # Load directional animations if available in the tileset
        if 'tiles' in self.tileset_data:
            for tile_info in self.tileset_data['tiles']:
                # Skip tiles without animation
                if 'animation' not in tile_info:
                    continue
                    
                # Check if this tile has direction and state properties
                tile_properties = {}
                if 'properties' in tile_info:
                    for prop in tile_info['properties']:
                        tile_properties[prop.get('name', '')] = prop.get('value', '')
                
                direction = tile_properties.get('direction')
                state = tile_properties.get('state')
                
                # If this tile has direction and state, store its animation
                if direction and state:
                    if direction not in self.directional_animations:
                        self.directional_animations[direction] = {}
                        
                    # Extract frames and durations
                    frames = [frame['tileid'] for frame in tile_info['animation']]
                    durations = [frame['duration'] / 1000.0 for frame in tile_info['animation']]
                    
                    # Store the animation
                    self.directional_animations[direction][state] = {
                        'frames': frames,
                        'durations': durations,
                        'total_duration': sum(durations)
                    }
                    print(f"Loaded {direction} {state} animation with {len(frames)} frames")
    
    def set_direction_and_state(self, direction, state):
        """
        Set the direction and state for character animations
        """
        if direction in self.directional_animations and state in self.directional_animations[direction]:
            if direction != self.direction or state != self.state:
                self.direction = direction
                self.state = state
                self.current_frame = 0
                self.animation_timer = 0
                
                # Update frames and durations
                anim_data = self.directional_animations[direction][state]
                self.frames = anim_data['frames']
                self.durations = anim_data['durations']
                self.total_duration = anim_data['total_duration']
                self.is_animated = True
    
    def update(self, dt):
        """
        Update the animation state
        """
        if not self.is_animated:
            return
            
        # Update animation timer
        self.animation_timer += dt
        
        # Find the current frame based on the timer
        if self.animation_timer >= self.durations[self.current_frame]:
            # Move to the next frame
            self.animation_timer -= self.durations[self.current_frame]
            self.current_frame = (self.current_frame + 1) % len(self.frames)
    
    def get_current_frame(self):
        """
        Get the current frame index
        """
        if not self.frames:
            return self.tile_id
        return self.frames[self.current_frame]
    
    def get_frame_image(self):
        """
        Get the current frame as a surface
        """
        if not self.tileset_data:
            # Return a placeholder if no tileset
            surface = pygame.Surface((16, 16))
            surface.fill((255, 0, 255))  # Magenta for missing textures
            return surface
            
        # Get the current frame index
        frame_index = self.get_current_frame()
        
        # Calculate position in the tileset
        columns = self.tileset_data['columns']
        tile_width = self.tileset_data['tilewidth']
        tile_height = self.tileset_data['tileheight']
        
        tile_x = (frame_index % columns) * tile_width
        tile_y = (frame_index // columns) * tile_height
        
        # Create a surface for the frame
        frame_surface = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
        
        # Copy the frame from the tileset image
        frame_surface.blit(self.tileset_data['image'], (0, 0), 
                         (tile_x, tile_y, tile_width, tile_height))
        
        return frame_surface
    
    def render_to_surface(self, surface, x, y):
        """Render the current frame at the specified position"""
        frame_image = self.get_frame_image()
        surface.blit(frame_image, (x, y)) 