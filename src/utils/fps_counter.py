import pygame
import time

class FPSCounter:
    """
    A simple FPS counter that calculates and displays the current frames per second.
    """
    def __init__(self, update_interval=0.5, scale_factor=1):
        """
        Initialize the FPS counter.
        
        Args:
            update_interval: How often to update the FPS value (in seconds)
            scale_factor: Scaling factor for the font size
        """
        self.frame_count = 0
        self.fps = 0
        self.last_update_time = time.time()
        self.update_interval = update_interval
        self.font = None
        self.initialized = False
        self.scale_factor = scale_factor
        
    def initialize(self, scale_factor=None):
        """
        Initialize the font for rendering.
        Called separately to avoid initializing pygame font before pygame is initialized.
        """
        if scale_factor is not None:
            self.scale_factor = scale_factor
            
        if not self.initialized:
            font_size = int(16)
            self.font = pygame.font.SysFont('monospace', font_size, bold=True)
            self.initialized = True
    
    def update(self):
        """
        Update the frame counter and recalculate FPS if needed.
        Should be called once per frame.
        """
        self.frame_count += 1
        
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        
        # Update FPS calculation every update_interval seconds
        if elapsed >= self.update_interval:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_update_time = current_time
    
    def render_to_surface(self, surface, x=10, y=10, color=(255, 255, 0)):
        """
        Draw the current FPS on the given surface.
        
        Args:
            surface: The pygame surface to draw on
            x, y: Position to draw the FPS counter
            color: Color of the FPS text
        """
        if not self.initialized:
            self.initialize()
            
        fps_text = f"FPS: {self.fps:.1f}"
        fps_surface = self.font.render(fps_text, True, color)
        surface.blit(fps_surface, (x, y)) 