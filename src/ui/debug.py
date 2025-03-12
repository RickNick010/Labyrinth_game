from src.utils.fps_counter import FPSCounter
import pygame

class DebugUI:
    def __init__(self, player, map, renderer):
        self.fps_counter = FPSCounter(scale_factor=renderer.scale_factor)
        self.player = player
        self.map = map
        self.renderer= renderer
        self.is_active = True
        self.show_fps = True  # Enable FPS display by default when debug is active
        self.show_collision = True
        self.show_tile_info = True
        self.show_spatial_grid = False

        
    def toggle_fps(self):
        self.show_fps = not self.show_fps
        
    def toggle_spatial_grid(self):
        self.show_spatial_grid = not self.show_spatial_grid

    def toggle_active(self):
        self.is_active = not self.is_active

    def toggle_collision(self):
        self.show_collision = not self.show_collision

    def toggle_tile_info(self):
        self.show_tile_info = not self.show_tile_info
    

    def render_to_surface(self, surface, camera_x, camera_y):
        """Draw debug information on the screen"""         
        
        # Use a larger font size for UI layer (since it's not being scaled)
        font_size = 16 * self.renderer.scale_factor
        font = pygame.font.SysFont('monospace', int(font_size), bold=True)
        y_offset = 30 * self.renderer.scale_factor  # Starting y position for text
        
        if self.show_fps:
            # Initialize FPS counter with current scale factor
            if not self.fps_counter.initialized:
                self.fps_counter.initialize(self.renderer.scale_factor)
            self.fps_counter.render_to_surface(surface)
            self.fps_counter.update()
        
        # Draw player position
        pos_text = f"Player: ({self.player.x:.1f}, {self.player.y:.1f})"
        pos_surface = font.render(pos_text, True, (255, 255, 0))
        surface.blit(pos_surface, (10, y_offset))
        
        # Draw camera position (using the actual camera coordinates)
        y_offset += font_size + 5
        cam_text = f"Camera: ({camera_x:.1f}, {camera_y:.1f})"
        cam_surface = font.render(cam_text, True, (255, 255, 0))
        surface.blit(cam_surface, (10, y_offset))

        # Only process tile info if enabled
        if self.show_tile_info:
            # Draw tile info under cursor
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Convert screen coordinates to world coordinates
            world_x = (mouse_x / self.renderer.scale_factor) + camera_x
            world_y = (mouse_y / self.renderer.scale_factor) + camera_y
            # Convert world coordinates to tile coordinates
            tile_x = int(world_x // self.map.tile_width)
            tile_y = int(world_y // self.map.tile_height)
            
            # Get tile info if within map bounds
            y_offset += font_size + 5
            tile_info = "Tile: None"
            if 0 <= tile_x < self.map.map_width and 0 <= tile_y < self.map.map_height:
                # Get the tile GID at this position
                for layer in self.map.layers:
                    if layer['type'] == 'tilelayer':
                        index = tile_y * self.map.map_width + tile_x
                        if index < len(layer['data']):
                            gid = layer['data'][index]
                            if gid > 0:
                                collidable = "Yes" if gid in self.map.collision_manager.collidable_tiles else "No"
                                tile_info = f"Tile: GID {gid} at ({tile_x}, {tile_y}) Collidable: {collidable}"
            
            tile_surface = font.render(tile_info, True, (255, 255, 0))
            surface.blit(tile_surface, (10, y_offset))
        
        # Don't add to render queue here - this causes duplication
        # Instead, the game loop should handle this