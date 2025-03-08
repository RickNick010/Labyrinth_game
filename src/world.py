import json
import os
import pygame
from src.asset_manager import AssetManager
from src.animated_tile import AnimatedTile

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
        
        # Collision data
        self.collision_map = []  # 2D array to store collision information
        self.collidable_tiles = {}  # Dictionary to store collidable tile IDs
        
        # Create an asset manager
        self.asset_manager = AssetManager()
        
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
        
        # Initialize collision map
        self.collision_map = [[False for _ in range(self.map_width)] for _ in range(self.map_height)]
        
        # Collision objects from object layers
        self.collision_objects = []
        
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
        self.load_collision_objects()
        
        # Identify collidable tiles
        self.identify_collidable_tiles()
        
        # Debug: Find water tiles in the map
        self.debug_find_tile_in_map(78)  # GID for Water tile 0
        self.debug_find_tile_in_map(79)  # GID for Water tile 1
        
        # Build collision map
        self.build_collision_map()
        
    def identify_collidable_tiles(self):
        """
        Identify all collidable tiles and store them in a dictionary for quick lookup
        """
        print("Starting to identify collidable tiles...")
        
        for firstgid, tileset in self.tileset_images.items():
            tileset_name = tileset.get('original_data', {}).get('name', 'Unknown')
            print(f"Checking tileset {tileset_name} (firstgid: {firstgid})")
            
            # Check if the entire tileset is collidable
            tileset_collidable = False
            if 'properties' in tileset:
                for prop in tileset['properties']:
                    if prop.get('name') == 'collidable':
                        print(f"Tileset {tileset_name} has collidable property: {prop.get('value')}")
                        if prop.get('value', 'false').lower() == 'true':
                            tileset_collidable = True
                            break
            
            # If the entire tileset is collidable, add all its tiles
            if tileset_collidable:
                for i in range(tileset.get('tilecount', 0)):
                    gid = firstgid + i
                    self.collidable_tiles[gid] = True
                print(f"Added {tileset.get('tilecount', 0)} collidable tiles from tileset {tileset_name}")
            
            # Check for individual collidable tiles
            if 'original_data' in tileset and 'tiles' in tileset['original_data']:
                print(f"Checking individual tiles in {tileset_name}...")
                for tile_info in tileset['original_data']['tiles']:
                    tile_id = tile_info.get('id', 0)
                    if 'properties' in tile_info:
                        for prop in tile_info['properties']:
                            if prop.get('name') == 'collidable':
                                print(f"Tile {tile_id} in {tileset_name} has collidable: {prop.get('value')}")
                                if prop.get('value', 'false').lower() == 'true':
                                    gid = firstgid + tile_id
                                    self.collidable_tiles[gid] = True
                                    print(f"Added collidable tile GID {gid} from {tileset_name}")
                                    
                                    # Special case for Water tileset - make all tiles collidable
                                    if tileset_name == "Water":
                                        for i in range(tileset.get('tilecount', 0)):
                                            gid = firstgid + i
                                            self.collidable_tiles[gid] = True
                                        print(f"Added all {tileset.get('tilecount', 0)} Water tiles as collidable (GIDs {firstgid}-{firstgid+tileset.get('tilecount', 0)-1})")
        
        print(f"Identified {len(self.collidable_tiles)} collidable tile IDs: {sorted(self.collidable_tiles.keys())}")
        
    def build_collision_map(self):
        """
        Build a 2D collision map based on tile properties and collision objects
        """
        print("Building collision map...")
        collidable_count = 0
        
        # First, add collidable tiles to the collision map
        for layer in self.layers:
            if layer['type'] == 'tilelayer' and layer.get('visible', True):
                layer_name = layer.get('name', 'Unnamed Layer')
                print(f"Processing layer: {layer_name}")
                data = layer.get('data', [])
                
                for y in range(self.map_height):
                    for x in range(self.map_width):
                        # Get the tile index from the data array
                        index = y * self.map_width + x
                        if index < len(data):
                            gid = data[index]
                            
                            # Skip empty tiles (gid = 0)
                            if gid == 0:
                                continue
                                
                            # Check if this tile is collidable using our dictionary
                            if gid in self.collidable_tiles:
                                self.collision_map[y][x] = True
                                collidable_count += 1
                                print(f"Added collidable tile at ({x}, {y}) with GID {gid}")
        
        # Then, add collision objects to the collision map
        for obj in self.collision_objects:
            # Convert float coordinates to integers for the collision map
            start_x = max(0, int(obj['x']))
            start_y = max(0, int(obj['y']))
            end_x = min(self.map_width, int(obj['x'] + obj['width']) + 1)
            end_y = min(self.map_height, int(obj['y'] + obj['height']) + 1)
            
            # Mark all tiles covered by this object as collidable
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    if 0 <= x < self.map_width and 0 <= y < self.map_height:
                        self.collision_map[y][x] = True
                        collidable_count += 1
        
        print(f"Built collision map with {collidable_count} collidable tiles")
        
        # Debug: Print a small section of the collision map
        print("Collision map sample (10x10 from top-left):")
        for y in range(min(10, self.map_height)):
            row = ""
            for x in range(min(10, self.map_width)):
                row += "X" if self.collision_map[y][x] else "."
            print(row)
    
    def is_tile_collidable(self, gid):
        """
        Check if a tile with the given GID is collidable
        """
        # Use the dictionary for a quick lookup
        return gid in self.collidable_tiles
    
    def is_position_collidable(self, x, y):
        """
        Check if a position is collidable
        """
        # Convert pixel coordinates to tile coordinates
        tile_x = int(x // self.tile_width)
        tile_y = int(y // self.tile_height)
        
        # Check if the tile is within the map bounds
        if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
            # Check the collision map
            if self.collision_map[tile_y][tile_x]:
                return True
        
        # Check collision with objects (for more precise collision)
        for obj in self.collision_objects:
            # Convert object coordinates to pixel coordinates
            obj_x = obj['x'] * self.tile_width
            obj_y = obj['y'] * self.tile_height
            obj_width = obj['width'] * self.tile_width
            obj_height = obj['height'] * self.tile_height
            
            # Check if the point is inside the object
            if (obj_x <= x < obj_x + obj_width and 
                obj_y <= y < obj_y + obj_height):
                return True
        
        return False
    
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
            # Show collision map
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    if 0 <= y < len(self.collision_map) and 0 <= x < len(self.collision_map[y]):
                        if self.collision_map[y][x]:
                            # Draw a red rectangle for collidable tiles
                            draw_x = x * self.tile_width - camera_x
                            draw_y = y * self.tile_height - camera_y
                            pygame.draw.rect(screen, (255, 0, 0, 128), 
                                            (draw_x, draw_y, self.tile_width, self.tile_height), 1)
            
            # Show collision objects
            for obj in self.collision_objects:
                # Convert object coordinates to pixel coordinates
                obj_x = obj['x'] * self.tile_width - camera_x
                obj_y = obj['y'] * self.tile_height - camera_y
                obj_width = obj['width'] * self.tile_width
                obj_height = obj['height'] * self.tile_height
                
                # Draw a blue rectangle for collision objects
                pygame.draw.rect(screen, (0, 0, 255), 
                                (obj_x, obj_y, obj_width, obj_height), 2)

    def debug_find_tile_in_map(self, target_gid):
        """
        Debug method to find all instances of a specific tile GID in the map
        """
        print(f"Searching for tile with GID {target_gid} in the map...")
        found_count = 0
        
        for layer in self.layers:
            if layer['type'] == 'tilelayer':
                layer_name = layer.get('name', 'Unnamed Layer')
                data = layer.get('data', [])
                
                for y in range(self.map_height):
                    for x in range(self.map_width):
                        index = y * self.map_width + x
                        if index < len(data) and data[index] == target_gid:
                            print(f"Found GID {target_gid} at position ({x}, {y}) in layer '{layer_name}'")
                            found_count += 1
        
        print(f"Found {found_count} instances of GID {target_gid}")

    def load_collision_objects(self):
        """
        Load collision objects from object layers in the map
        """
        print("Loading collision objects...")
        
        for layer in self.layers:
            if layer['type'] == 'objectgroup' and 'collision' in layer['name'].lower():
                print(f"Found collision layer: {layer['name']}")
                
                for obj in layer.get('objects', []):
                    # Convert object coordinates to tile coordinates
                    x = obj.get('x', 0) / self.tile_width
                    y = obj.get('y', 0) / self.tile_height
                    width = obj.get('width', 0) / self.tile_width
                    height = obj.get('height', 0) / self.tile_height
                    
                    # Create a collision rectangle
                    collision_rect = {
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    }
                    
                    self.collision_objects.append(collision_rect)
                    print(f"Added collision object at ({x}, {y}) with size ({width}, {height})")
        
        print(f"Loaded {len(self.collision_objects)} collision objects")
