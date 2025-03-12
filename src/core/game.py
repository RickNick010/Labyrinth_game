import pygame
import os
from src.entities.player import Player
from src.core.world import TileMap
from src.components.asset_manager import AssetManager
from src.utils.fps_counter import FPSCounter
from src.core.config import Config
from src.components.renderer import Renderer

class Game:
    def __init__(self, scale_factor=5):
        pygame.init()
        
        # Load configuration
        self.config = Config()
        
        # Get screen dimensions from config
        self.screen_width = self.config.get("SCREEN_WIDTH")
        self.screen_height = self.config.get("SCREEN_HEIGHT")
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("The Labyrinth Game")
        
        # Scale factor for zooming in
        self.scale_factor = scale_factor
        
        # Create a smaller render surface that we'll scale up
        self.render_width = self.screen_width // scale_factor
        self.render_height = self.screen_height // scale_factor
        self.render_surface = pygame.Surface((self.render_width, self.render_height))
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Debug mode
        self.debug_mode = False
        self.debug_mode_spatial_grid = False
        
        # FPS counter
        self.fps_counter = FPSCounter()
        
        # Create asset manager
        self.asset_manager = AssetManager()
        
        # Create player at the center of the render surface
        self.player = Player(
            self.render_width // 2, 
            self.render_height // 2, 
            self.asset_manager,
            self.config
        )
        
        # Camera position
        self.camera_x = 0
        self.camera_y = 0
        
        # Load the map
        self.map = None
        self.load_map("data/assets/maps/test_map.tmj")
        
        # Create the renderer
        self.renderer = Renderer(self.screen_width, self.screen_height, scale_factor)
        
        # Set up debug references in renderer
        self.renderer.set_debug_references(self.player, self.map, self.fps_counter)
        
        # Caching for optimization
        self.cached_collision_state = {}
        self.collision_cache_valid = False
        
    def load_map(self, map_path):
        if os.path.exists(self.asset_manager.get_asset_path(map_path)):
            self.map = TileMap(map_path)
            print(f"Map loaded: {map_path}")
            
            # Set map boundaries for the player
            if self.map:
                map_pixel_width = self.map.map_width * self.map.tile_width
                map_pixel_height = self.map.map_height * self.map.tile_height
                self.player.set_map_boundaries(map_pixel_width, map_pixel_height)
        else:
            print(f"Map file not found: {map_path}")
            
    def update_camera(self):
        # Center the camera on the player
        self.camera_x = self.player.x - (self.render_width // 2) + (self.player.width // 2)
        self.camera_y = self.player.y - (self.render_height // 2) + (self.player.height // 2)
        
        # Keep the camera within the map bounds
        if self.map:
            self.camera_x = max(0, min(self.camera_x, self.map.map_width * self.map.tile_width - self.render_width))
            self.camera_y = max(0, min(self.camera_y, self.map.map_height * self.map.tile_height - self.render_height))
        
    def update_collision_cache(self):
        """
        Update collision cache
        """
        if self.map and hasattr(self.map, 'collision_manager'):
            # Clear cache
            self.cached_collision_state.clear()
            
            # Get visible area around player
            player_tile_x = int(self.player.x // self.map.tile_width)
            player_tile_y = int(self.player.y // self.map.tile_height)
            
            # Cache collision state in area around player
            cache_radius = 5  # Adjustable parameter - how many tiles around player to cache
            for y in range(player_tile_y - cache_radius, player_tile_y + cache_radius + 1):
                for x in range(player_tile_x - cache_radius, player_tile_x + cache_radius + 1):
                    if 0 <= x < self.map.map_width and 0 <= y < self.map.map_height:
                        # Cache collision value for this tile
                        tile_key = (x, y)
                        self.cached_collision_state[tile_key] = self.map.collision_manager.collision_map[y * self.map.map_width + x]
            
            self.collision_cache_valid = True

    def run(self):
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(60) / 1000.0  # GAME FPS
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        # Toggle debug mode
                        self.debug_mode = not self.debug_mode
                        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
                    elif event.key == pygame.K_F2 and self.debug_mode:
                        # Toggle spatial grid display
                        self.debug_mode_spatial_grid = not self.debug_mode_spatial_grid
                        self.map.collision_manager.debug_grid = self.debug_mode_spatial_grid
                        print(f"Spatial grid: {'ON' if self.debug_mode_spatial_grid else 'OFF'}")
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                
            # Get keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.running = False
                
            # Update collision cache every 5 frames
            if not self.collision_cache_valid or self.fps_counter.frame_count % 5 == 0:
                self.update_collision_cache()
            
            # Update player with tilemap for collision detection
            self.player.update(keys, dt, self.map)
            
            # Invalidate collision cache if player moved
            if self.player.moving:
                self.collision_cache_valid = False
            
            # Update animated tiles in the map
            if self.map:
                self.map.update(dt)
            
            # Clear the renderer
            self.renderer.clear()
            
            # Set camera position
            self.update_camera()
            self.renderer.set_camera(self.camera_x, self.camera_y)
            
            # Add renderable items to queue in correct order
            if self.map:
                self.renderer.render_map(self.map)
            self.renderer.render_effect(self.player.footprint_manager, "below")
            self.renderer.render_entity(self.player, "entities")
            
            # Add UI and debug info
            if self.debug_mode:
                self.renderer.render_ui_element(
                    lambda surface, _, __: self.renderer.render_debug_info(surface, self.debug_mode_spatial_grid)
                )
                if self.debug_mode and self.debug_mode_spatial_grid:
                    self.renderer.add_to_render_queue("effects",
                        lambda surface, cam_x, cam_y: self.map.collision_manager.render_debug_to_surface(
                            surface, cam_x, cam_y
                        )
                    )    
            
            # Render everything to the screen
            self.renderer.render_to_screen(self.screen)
            
            # Update the display
            pygame.display.flip()
            
        pygame.quit()
