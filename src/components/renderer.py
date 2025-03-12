import pygame
import math

class Renderer:
    """
    A centralized rendering system that handles all drawing operations.
    """
    def __init__(self, screen_width, screen_height, scale_factor=1):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scale_factor = scale_factor
        
        # Main render surfaces
        self.main_surface = pygame.Surface((screen_width // scale_factor, 
                                           screen_height // scale_factor))
        self.ui_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        
        # Cache for scaled surface
        self.scaled_surface = pygame.Surface((screen_width, screen_height)) if scale_factor != 1 else None
        
        # Camera position
        self.camera_x = 0
        self.camera_y = 0
        
        # Visible area in tiles (for determining drawing boundaries)
        self.visible_width = (screen_width // scale_factor) // 16  # Assuming tile size is 16x16
        self.visible_height = (screen_height // scale_factor) // 16
        
        # Rendering layers (lower values = drawn on top)
        self.layers = {
            "background": [],    # Background elements (sky, distant objects)
            "terrain": [],       # Map terrain
            "below": [],         # Items below characters
            "entities": [],      # Characters and entities
            "above": [],         # Items above characters
            "effects": [],       # Visual effects  
            "debug":[],          # Debug Info
            "ui": []             # User interface elements
        }
           
        # Store game state references needed for debug info
        self.player = None
        self.map = None
        self.fps_counter = None
        
    def set_camera(self, x, y):
        """Set the camera position"""
        self.camera_x = x
        self.camera_y = y
        
    def clear(self):
        """Clear all rendering surfaces and layers for the next frame"""
        self.main_surface.fill((0, 0, 0))  # Black background
        self.ui_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Clear all rendering layers
        for layer in self.layers.values():
            layer.clear()
            
    def add_to_render_queue(self, layer_name, drawable, z_index=0):
        """
        Add an item to the rendering queue for a specific layer
        
        Args:
            layer_name: The name of the layer to add to
            drawable: A tuple of (surface, rect) or callable that takes (surface, camera_x, camera_y)
            z_index: Used for sorting within a layer
        """
        if layer_name in self.layers:
            self.layers[layer_name].append((z_index, drawable))
            
    def render_map(self, tile_map):
        """Render the tilemap to the terrain layer"""
        self.add_to_render_queue("terrain", 
            lambda surface, cam_x, cam_y: tile_map.render_to_surface(
                surface, cam_x, cam_y
            )
        )
        
        
    def render_entity(self, entity, layer="entities"):
        """Add an entity to the render queue"""
        z_index = entity.y  # Use Y position for depth sorting
        
        self.add_to_render_queue(layer, 
            lambda surface, cam_x, cam_y: entity.render_to_surface(
                surface, cam_x, cam_y
            ),
            z_index
        )
        
    def render_effect(self, effect, layer="effects"):
        """Add an effect to the render queue in the specified layer"""
        self.add_to_render_queue(layer, 
            lambda surface, cam_x, cam_y: effect.render_to_surface(
                surface, cam_x, cam_y
            )
        )
        
    def render_ui_element(self, ui_element, z_index=0):
        """Add a UI element to the UI layer"""
        self.add_to_render_queue("ui", ui_element, z_index)
        

    def render_debug(self, debug_ui):
        """Add debug UI to the UI layer (not affected by scaling)"""
        # Change to UI layer so it's rendered at full screen resolution
        self.add_to_render_queue("ui", 
            lambda surface, cam_x, cam_y: debug_ui.render_to_surface(
                surface, self.camera_x, self.camera_y
            )
        )

    def process_queue(self):
        """Process all items in the render queue for each layer"""
        # Сбросить счетчик отрисованных объектов
        self.rendered_objects_count = 0
        
        # Render world elements to main surface
        world_layers = ["background", "terrain", "below", "entities", "above", "effects", "debug"]
        
        # Skip empty layers
        for layer_name in world_layers:
            # If the layer is empty, skip it
            if not self.layers[layer_name]:
                continue
            
            # Sort items in the layer by z_index
            sorted_items = sorted(self.layers[layer_name], key=lambda item: item[0])
            
            # Render each item
            for _, drawable in sorted_items:
                if callable(drawable):
                    # If it's a function, call it with the surface and camera
                    drawable(self.main_surface, self.camera_x, self.camera_y)
                else:
                    # Otherwise assume it's a (surface, rect) tuple
                    surface, rect = drawable
                    
                    # Check if the object is in the visible area
                    if self.is_visible(rect):
                        # Adjust position by camera
                        adjusted_rect = rect.copy()
                        adjusted_rect.x -= self.camera_x
                        adjusted_rect.y -= self.camera_y
                        
                        self.main_surface.blit(surface, adjusted_rect)
                
                self.rendered_objects_count += 1
                
        # Render UI elements directly to UI surface (no camera adjustment)
        if self.layers["ui"]:  # Check if the UI layer is empty
            sorted_ui = sorted(self.layers["ui"], key=lambda item: item[0])
            for _, drawable in sorted_ui:
                if callable(drawable):
                    drawable(self.ui_surface, 0, 0)
                else:
                    surface, rect = drawable
                    self.ui_surface.blit(surface, rect)
                self.rendered_objects_count += 1
        
    def is_visible(self, rect):
        """Checks if the rectangle is in the visible area of the camera"""
        # Expand the visible area slightly to avoid "popping out" objects
        margin = 32
        
        # If the object is outside the visible area, do not render it
        if (rect.right < self.camera_x - margin or 
            rect.left > self.camera_x + self.main_surface.get_width() + margin or
            rect.bottom < self.camera_y - margin or 
            rect.top > self.camera_y + self.main_surface.get_height() + margin):
            return False
        return True

    def render_to_screen(self, screen):
        """Render all layers to the screen"""
        # Process the render queue
        self.process_queue()
        
        # Scale the main surface if needed
        if self.scale_factor != 1:
            # Use cached surface for scaling
            if self.scaled_surface is None:
                self.scaled_surface = pygame.Surface((self.screen_width, self.screen_height))
            
            # Use fast scaling method
            pygame.transform.scale(
                self.main_surface, 
                (self.screen_width, self.screen_height),
                self.scaled_surface
            )
            screen.blit(self.scaled_surface, (0, 0))
        else:
            screen.blit(self.main_surface, (0, 0))
            
        # Draw UI on top (already at screen resolution)
        screen.blit(self.ui_surface, (0, 0))
