import os
import json
import pygame

class AssetManager:
    """
    Handles loading and managing game assets like images, tilesets, and maps.
    """
    def __init__(self):
        self.base_path = self._find_base_path()
        self.images = {}
        self.tilesets = {}
        self.animations = {}
        
    def _find_base_path(self):
        """
        Find the base path of the project to correctly resolve asset paths.
        """
        # Start with the current directory
        current_dir = os.getcwd()
        
        # Check if we're in the project root (has data/assets directory)
        if os.path.exists(os.path.join(current_dir, 'data', 'assets')):
            return current_dir
        
        # Check if we're in the src directory
        if os.path.basename(current_dir) == 'src' and os.path.exists(os.path.join(current_dir, '..', 'data', 'assets')):
            return os.path.abspath(os.path.join(current_dir, '..'))
            
        # Default to current directory if we can't determine
        print(f"Warning: Could not determine project base path. Using {current_dir}")
        return current_dir
    
    def get_asset_path(self, relative_path):
        """
        Convert a relative asset path to an absolute path.
        """
        return os.path.normpath(os.path.join(self.base_path, relative_path))
    
    def load_image(self, path):
        """
        Load an image from the given path.
        """
        if path in self.images:
            return self.images[path]
            
        full_path = self.get_asset_path(path)
        
        if not os.path.exists(full_path):
            print(f"Error: Image not found at {full_path}")
            # Return a placeholder image (small colored surface)
            surface = pygame.Surface((16, 16))
            surface.fill((255, 0, 255))  # Magenta for missing textures
            self.images[path] = surface
            return surface
            
        try:
            image = pygame.image.load(full_path).convert_alpha()
            self.images[path] = image
            return image
        except pygame.error as e:
            print(f"Error loading image {full_path}: {e}")
            surface = pygame.Surface((16, 16))
            surface.fill((255, 0, 255))  # Magenta for missing textures
            self.images[path] = surface
            return surface
    
    def load_tileset(self, tileset_path):
        """
        Load a tileset from the given path.
        """
        if tileset_path in self.tilesets:
            return self.tilesets[tileset_path]
            
        full_path = self.get_asset_path(tileset_path)
        
        if not os.path.exists(full_path):
            print(f"Error: Tileset not found at {full_path}")
            return None
            
        try:
            with open(full_path, 'r') as f:
                tileset_data = json.load(f)
                
            # Get the image path from the tileset data
            image_path = tileset_data.get('image', '')
            
            # Handle the path format in the tileset file
            if image_path.startswith('static/'):
                image_path = image_path.replace('static/', 'data/assets/tilesets/static/')
            elif image_path.startswith('animated/'):
                image_path = image_path.replace('animated/', 'data/assets/tilesets/animated/')
            elif not image_path.startswith('/') and not image_path.startswith('data/'):
                # Handle relative paths within the same directory as the tileset
                tileset_dir = os.path.dirname(full_path)
                image_path = os.path.join(tileset_dir, image_path)
            
            # Load the tileset image
            tileset_image = self.load_image(image_path)
            
            # Create the tileset object
            tileset = {
                'image': tileset_image,
                'columns': tileset_data.get('columns', 1),
                'tilecount': tileset_data.get('tilecount', 1),
                'tilewidth': tileset_data.get('tilewidth', 16),
                'tileheight': tileset_data.get('tileheight', 16),
                'firstgid': 1,  # Default, will be overridden when used in a map
                'animations': {},  # Will store animation data
                'tiles': tileset_data.get('tiles', [])  # Store the original tile data
            }
            
            # Process animation data if present
            if 'tiles' in tileset_data:
                for tile_info in tileset_data['tiles']:
                    tile_id = tile_info.get('id', 0)
                    
                    # Check if this tile has animation data
                    if 'animation' in tile_info:
                        # Extract animation frames and durations
                        frames = []
                        durations = []
                        
                        for frame in tile_info['animation']:
                            frames.append(frame.get('tileid', 0))
                            durations.append(frame.get('duration', 100) / 1000.0)  # Convert to seconds
                        
                        # Store the animation data
                        animation_name = f"tile_{tile_id}"
                        tileset['animations'][animation_name] = {
                            'frames': frames,
                            'durations': durations,
                            'total_duration': sum(durations)
                        }
                        
                        print(f"Loaded animation '{animation_name}' with {len(frames)} frames")
            
            self.tilesets[tileset_path] = tileset
            return tileset
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading tileset {full_path}: {e}")
            return None
    
    def get_animation(self, tileset_path, animation_name=None):
        """
        Get animation data from a tileset.
        If animation_name is None, returns the first animation found.
        """
        tileset = self.load_tileset(tileset_path)
        if not tileset or not tileset.get('animations'):
            return None
            
        animations = tileset['animations']
        
        # If no specific animation requested, return the first one
        if animation_name is None and animations:
            return next(iter(animations.values()))
            
        # Return the requested animation if it exists
        return animations.get(animation_name)
    
    def create_animation_frames(self, tileset_path, animation_name=None):
        """
        Create a list of frame surfaces for an animation.
        Returns a tuple of (frames, durations)
        """
        tileset = self.load_tileset(tileset_path)
        if not tileset:
            return [], []
            
        # Get the animation data
        animation = self.get_animation(tileset_path, animation_name)
        if not animation:
            # If no animation found, create a single frame from the first tile
            frame = pygame.Surface((tileset['tilewidth'], tileset['tileheight']), pygame.SRCALPHA)
            frame.blit(tileset['image'], (0, 0), 
                      (0, 0, tileset['tilewidth'], tileset['tileheight']))
            return [frame], [1.0]
            
        # Create a surface for each frame
        frames = []
        for frame_id in animation['frames']:
            # Calculate the position in the tileset
            col = frame_id % tileset['columns']
            row = frame_id // tileset['columns']
            
            # Calculate the pixel position
            x = col * tileset['tilewidth']
            y = row * tileset['tileheight']
            
            # Create a surface for this frame
            frame = pygame.Surface((tileset['tilewidth'], tileset['tileheight']), pygame.SRCALPHA)
            frame.blit(tileset['image'], (0, 0), 
                      (x, y, tileset['tilewidth'], tileset['tileheight']))
            
            frames.append(frame)
            
        return frames, animation['durations'] 