import pygame
import os
from src.entities.player import Player
from src.core.world import TileMap
from src.components.asset_manager import AssetManager
from src.utils.fps_counter import FPSCounter
from src.core.config import Config
from src.components.renderer import Renderer

class Game:
    def __init__(self, scale_factor=6):
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
        
    def render_debug_info(self, surface):
        """
        Draw debug information on the screen
        """
        if not self.debug_mode:
            return
            
        # Draw FPS counter
        self.fps_counter.draw(surface)
        self.fps_counter.update()
        
        # Draw player position
        font = pygame.font.SysFont('monospace', 16, bold=True)
        pos_text = f"Player: ({self.player.x}, {self.player.y})"
        pos_surface = font.render(pos_text, True, (255, 255, 0))
        surface.blit(pos_surface, (10, 30))
        
        # Draw camera position
        cam_text = f"Camera: ({self.camera_x}, {self.camera_y})"
        cam_surface = font.render(cam_text, True, (255, 255, 0))
        surface.blit(cam_surface, (10, 50))

        # Draw tile info under cursor
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Convert screen coordinates to world coordinates
        world_x = (mouse_x // self.scale_factor) + self.camera_x
        world_y = (mouse_y // self.scale_factor) + self.camera_y
        # Convert world coordinates to tile coordinates
        tile_x = world_x // self.map.tile_width
        tile_y = world_y // self.map.tile_height
        
        # Get tile info if within map bounds
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
        surface.blit(tile_surface, (10, 70))
        
    def run(self):
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(60) / 1000.0  # Convert to seconds
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1:
                        # Toggle debug mode
                        self.debug_mode = not self.debug_mode
                        # Синхронизируем режим отладки с рендерером
                        self.renderer.set_debug_mode(self.debug_mode)
                        print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
                
            # Get keyboard input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.running = False
                
            # Update player with tilemap for collision detection
            self.player.update(keys, dt, self.map)
            
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
                # 1. Рендерим карту первой
                self.renderer.render_map(self.map)
                
            # 2. Рендерим эффекты следов ДО игрока в слой "below"
            self.renderer.render_effect(self.player.footprint_manager, "below")

            # 3. Рендерим игрока
            self.renderer.render_entity(self.player, "entities")
            
            # Add UI and debug info
            if self.debug_mode:
                self.renderer.render_ui_element(
                    lambda surface, _, __: self.render_debug_info(surface)
                )
            
            # Render everything to the screen
            self.renderer.render_to_screen(self.screen)
            
            # Update the display
            pygame.display.flip()
            
        pygame.quit()
