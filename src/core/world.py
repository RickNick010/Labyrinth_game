import json
import os
import pygame
from src.core.asset_manager import AssetManager
from src.components.animations import AnimatedTile
from src.components.collision import CollisionManager

class TileMap:
    def __init__(self, map_path):
        self.map_data = None
        self.tileset_images = {}
        self.animated_tiles = {}  # Store animated tiles by gid
        self.tile_width = 0
        self.tile_height = 0
        self.map_width = 0
        self.map_height = 0
        self.layers = []
        self.map_path = map_path
        
        # Create an asset manager
        self.asset_manager = AssetManager()
        
        # Collision manager will be initialized after loading map dimensions
        self.collision_manager = None
        
        self.load_map(map_path)
        
    def load_map(self, map_path):
        # Get the full path to the map file
        full_map_path = self.asset_manager.get_asset_path(map_path)
        self.map_directory = os.path.dirname(full_map_path)
        print(f"Loading map from: {full_map_path}")
        
        # Load the map JSON data
        try:
            with open(full_map_path, 'r') as f:
                self.map_data = json.load(f)
                print('Map loaded successfully')
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading map {full_map_path}: {e}")
            return
            
        # Get basic map properties
        self.tile_width = self.map_data.get('tilewidth', 16)
        self.tile_height = self.map_data.get('tileheight', 16)
        self.map_width = self.map_data.get('width', 0)
        self.map_height = self.map_data.get('height', 0)
        
        # Initialize collision manager
        self.collision_manager = CollisionManager(
            self.tile_width, 
            self.tile_height, 
            self.map_width, 
            self.map_height
        )
        
        # Print map properties for debugging
        print(f"Map dimensions: {self.map_width}x{self.map_height}, Tile size: {self.tile_width}x{self.tile_height}")
        
        # Load tilesets
        for tileset in self.map_data.get('tilesets', []):
            print(f"Found tileset reference: {tileset}")
            self.load_tileset(tileset)
            
        # Process layers
        self.layers = self.map_data.get('layers', [])
        print(f"Loaded {len(self.layers)} layers")
        
        # Extract collision objects from object layers
        self.collision_manager.load_collision_objects(self.layers, self.tile_width, self.tile_height)
        
        # Identify collidable tiles
        self.collision_manager.identify_collidable_tiles(self.tileset_images)

        # Build collision map
        self.collision_manager.build_collision_map(self.layers)
        
    # Delegate collision methods to the collision manager
    def is_tile_collidable(self, gid):
        return self.collision_manager.is_tile_collidable(gid)
    
    def is_position_collidable(self, x, y):
        return self.collision_manager.is_position_collidable(x, y)
        
    def resolve_tileset_path(self, source_path):
        """
        Resolve a tileset source path which might be relative to the map file
        """
        # If it's an absolute path or starts with data/, use it directly
        if source_path.startswith('/') or source_path.startswith('data/'):
            return source_path
            
        # If it's a relative path (e.g., "../tilesets/static/Tiles/Grass.tsj")
        # Resolve it relative to the map directory
        resolved_path = os.path.normpath(os.path.join(self.map_directory, source_path))
        
        # Convert to a path relative to the project root
        base_path = self.asset_manager.base_path
        if resolved_path.startswith(base_path):
            # Make it relative to the project root
            return os.path.relpath(resolved_path, base_path)
        
        # If we can't resolve it relative to the project root, use the original path
        # but try to make it work with our asset structure
        if '../' in source_path:
            # Handle "../tilesets/..." pattern
            parts = source_path.split('/')
            if 'tilesets' in parts:
                # Find the index of 'tilesets'
                tileset_index = parts.index('tilesets')
                # Reconstruct the path starting from 'tilesets'
                return "data/assets/" + '/'.join(parts[tileset_index:])
        
        # Default fallback - prepend data/assets/tilesets/
        return f"data/assets/tilesets/{os.path.basename(source_path)}"
        
    def load_tileset(self, tileset):
        # If the tileset is an external file, load it
        if 'source' in tileset:
            # Get the source path
            source_path = tileset['source']
            
            # Resolve the tileset path
            tileset_path = self.resolve_tileset_path(source_path)
            print(f"Looking for tileset at: {tileset_path}")
            
            # Load the tileset using the asset manager
            tileset_data = self.asset_manager.load_tileset(tileset_path)
            
            if tileset_data:
                # Store the tileset with its firstgid
                tileset_data['firstgid'] = tileset['firstgid']
                
                # Store the original tileset data for property access
                full_path = self.asset_manager.get_asset_path(tileset_path)
                try:
                    with open(full_path, 'r') as f:
                        original_data = json.load(f)
                        tileset_data['original_data'] = original_data
                        
                        # Extract tileset properties
                        if 'properties' in original_data:
                            tileset_data['properties'] = original_data['properties']
                            print(f"Loaded properties for tileset {os.path.basename(tileset_path)}: {original_data['properties']}")
                            
                            # Debug: Print tile properties for Water tileset
                            if 'Water' in tileset_path and 'tiles' in original_data:
                                print(f"Water tileset tiles: {original_data['tiles']}")
                                for tile in original_data['tiles']:
                                    if 'properties' in tile:
                                        print(f"Water tile {tile['id']} properties: {tile['properties']}")
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading original tileset data {full_path}: {e}")
                
                self.tileset_images[tileset['firstgid']] = tileset_data
                print(f"Tileset loaded successfully: {tileset_path}")
                
                # Check for animated tiles in this tileset
                if 'animations' in tileset_data and tileset_data['animations']:
                    for anim_name, anim_data in tileset_data['animations'].items():
                        # Extract the tile ID from the animation name (format: "tile_X")
                        if anim_name.startswith("tile_"):
                            try:
                                tile_id = int(anim_name.split("_")[1])
                                # Calculate the global ID for this tile
                                gid = tileset['firstgid'] + tile_id
                                
                                # Create an animated tile for this GID
                                self.animated_tiles[gid] = AnimatedTile(
                                    self.asset_manager, 
                                    tileset_path, 
                                    tile_id
                                )
                                print(f"Created animated tile for GID {gid}")
                            except (ValueError, IndexError):
                                pass
            else:
                print(f"Failed to load tileset: {tileset_path}")
    
    def get_tile_image(self, gid):
        # Check if this is an animated tile
        if gid in self.animated_tiles:
            return self.animated_tiles[gid].get_frame_image()
            
        # Find the tileset that contains this gid
        for firstgid, tileset in sorted(self.tileset_images.items(), reverse=True):
            if gid >= firstgid:
                # Calculate the local tile id within the tileset
                local_id = gid - firstgid
                
                # Calculate the position of the tile in the tileset image
                columns = tileset['columns']
                tile_x = (local_id % columns) * tileset['tilewidth']
                tile_y = (local_id // columns) * tileset['tileheight']
                
                # Create a surface for the tile
                tile_surface = pygame.Surface((tileset['tilewidth'], tileset['tileheight']), pygame.SRCALPHA)
                
                # Copy the tile from the tileset image
                tile_surface.blit(tileset['image'], (0, 0), 
                                 (tile_x, tile_y, tileset['tilewidth'], tileset['tileheight']))
                
                return tile_surface
        
        return None
    
    def update(self, dt):
        """
        Update all animated tiles
        """
        for animated_tile in self.animated_tiles.values():
            animated_tile.update(dt)
    
    def render(self, screen, camera_x=0, camera_y=0, debug=False):
        # Render each layer
        for layer in self.layers:
            if layer['type'] == 'tilelayer' and layer.get('visible', True):
                data = layer.get('data', [])
                
                # Calculate the visible area based on the camera position
                start_x = max(0, camera_x // self.tile_width)
                start_y = max(0, camera_y // self.tile_height)
                end_x = min(self.map_width, start_x + (screen.get_width() // self.tile_width) + 2)
                end_y = min(self.map_height, start_y + (screen.get_height() // self.tile_height) + 2)
                
                # Render visible tiles
                for y in range(start_y, end_y):
                    for x in range(start_x, end_x):
                        # Get the tile index from the data array
                        index = y * self.map_width + x
                        if index < len(data):
                            gid = data[index]
                            
                            # Skip empty tiles (gid = 0)
                            if gid == 0:
                                continue
                                
                            # Get the tile image
                            tile_image = self.get_tile_image(gid)
                            if tile_image:
                                # Calculate the position to draw the tile
                                draw_x = x * self.tile_width - camera_x
                                draw_y = y * self.tile_height - camera_y
                                
                                # Draw the tile
                                screen.blit(tile_image, (draw_x, draw_y))
        
        # Debug rendering
        if debug:
            self.collision_manager.render_debug(screen, camera_x, camera_y, self.tile_width, self.tile_height)

