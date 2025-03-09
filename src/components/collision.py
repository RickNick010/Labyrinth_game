class CollisionManager:
    def __init__(self, tile_width, tile_height, map_width, map_height):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.map_width = map_width
        self.map_height = map_height
        
        # Collision data
        self.collision_map = [[False for _ in range(map_width)] for _ in range(map_height)]
        self.collidable_tiles = {}  # Dictionary to store collidable tile IDs
        self.collision_objects = []  # Store collision objects
        
    def identify_collidable_tiles(self, tilesets):
        """
        Identify all collidable tiles and store them in a dictionary for quick lookup
        """
        print("Starting to identify collidable tiles...")
        
        for firstgid, tileset in tilesets.items():
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
    
    def load_collision_objects(self, layers, tile_width, tile_height):
        """
        Load collision objects from object layers in the map
        """
        print("Loading collision objects...")
        
        for layer in layers:
            if layer['type'] == 'objectgroup' and 'collision' in layer['name'].lower():
                print(f"Found collision layer: {layer['name']}")
                
                for obj in layer.get('objects', []):
                    # Convert object coordinates to tile coordinates
                    x = obj.get('x', 0) / tile_width
                    y = obj.get('y', 0) / tile_height
                    width = obj.get('width', 0) / tile_width
                    height = obj.get('height', 0) / tile_height
                    
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
    
    def build_collision_map(self, layers):
        """
        Build a 2D collision map based on tile properties and collision objects
        """
        print("Building collision map...")
        collidable_count = 0
        
        # First, add collidable tiles to the collision map
        for layer in layers:
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
    
    def render_debug(self, screen, camera_x, camera_y, tile_width, tile_height):
        """
        Render collision debug information
        """
        import pygame
        
        # Calculate the visible area based on the camera position
        start_x = max(0, camera_x // tile_width)
        start_y = max(0, camera_y // tile_height)
        end_x = min(self.map_width, start_x + (screen.get_width() // tile_width) + 2)
        end_y = min(self.map_height, start_y + (screen.get_height() // tile_height) + 2)
        
        # Show collision map
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if 0 <= y < len(self.collision_map) and 0 <= x < len(self.collision_map[y]):
                    if self.collision_map[y][x]:
                        # Draw a red rectangle for collidable tiles
                        draw_x = x * tile_width - camera_x
                        draw_y = y * tile_height - camera_y
                        pygame.draw.rect(screen, (255, 0, 0, 128), 
                                        (draw_x, draw_y, tile_width, tile_height), 1)
        
        # Show collision objects
        for obj in self.collision_objects:
            # Convert object coordinates to pixel coordinates
            obj_x = obj['x'] * tile_width - camera_x
            obj_y = obj['y'] * tile_height - camera_y
            obj_width = obj['width'] * tile_width
            obj_height = obj['height'] * tile_height
            
            # Draw a blue rectangle for collision objects
            pygame.draw.rect(screen, (0, 0, 255), 
                            (obj_x, obj_y, obj_width, obj_height), 2)
