class CollisionManager:
    def __init__(self, tile_width, tile_height, map_width, map_height):
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.map_width = map_width
        self.map_height = map_height
        
        # Collision data - заменить двумерный массив на одномерный для быстрого доступа
        self.collision_map = [False] * (map_width * map_height)
        self.collidable_tiles = {}  # Dictionary to store collidable tile IDs
        self.collision_objects = []  # Store collision objects
        
        # Add spatial partitioning
        self.spatial_grid = {}  # Grid for fast collision object search
        self.grid_cell_size = 32  # Grid cell size (adjustable)
        
        self.debug_grid = False  # Флаг для отображения пространственной сетки
        
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
                    
                    # Handle different object types
                    if 'polygon' in obj:
                        # Convert polygon points to tile coordinates
                        points = []
                        for point in obj['polygon']:
                            px = (x + point['x'] / tile_width)
                            py = (y + point['y'] / tile_height)
                            points.append((px, py))
                        
                        collision_obj = {
                            'type': 'polygon',
                            'points': points
                        }
                        print(f"Added polygon collision object with {len(points)} points")
                        
                    else:
                        # Skip regular objects with zero dimensions
                        if width == 0 or height == 0:
                            continue
                        
                        # Create a rectangle or ellipse collision object
                        collision_obj = {
                            'x': x,
                            'y': y,
                            'width': width,
                            'height': height,
                            'type': 'ellipse' if obj.get('ellipse', False) else 'rectangle'
                        }
                        print(f"Added {collision_obj['type']} collision object at ({x}, {y}) with size ({width}, {height})")
                    
                    self.collision_objects.append(collision_obj)
        
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
                                # Using one-dimensional array
                                self.collision_map[y * self.map_width + x] = True
                                collidable_count += 1

        # Populate spatial grid for collision objects
        self._build_spatial_grid()
        
        print(f"Built collision map with {collidable_count} collidable tiles")
        
        # Debug: Print a small section of the collision map
        print("Collision map sample (10x10 from top-left):")
        for y in range(min(10, self.map_height)):
            row = ""
            for x in range(min(10, self.map_width)):
                row += "X" if self.collision_map[y * self.map_width + x] else "."
            print(row)
    
    def _build_spatial_grid(self):
        """
        Build spatial grid for fast collision object search
        """
        self.spatial_grid = {}
        
        # Add collision objects to spatial grid
        for obj_idx, obj in enumerate(self.collision_objects):
            if obj['type'] == 'polygon':
                # For polygons, calculate bounding box from points
                points = obj['points']
                if not points:
                    continue
                    
                # Find min and max coordinates
                min_x = min(p[0] for p in points)
                max_x = max(p[0] for p in points)
                min_y = min(p[1] for p in points)
                max_y = max(p[1] for p in points)
                
                # Calculate grid cells that this polygon overlaps
                start_x = max(0, int(min_x * self.tile_width // self.grid_cell_size))
                start_y = max(0, int(min_y * self.tile_height // self.grid_cell_size))
                end_x = int(max_x * self.tile_width // self.grid_cell_size) + 1
                end_y = int(max_y * self.tile_height // self.grid_cell_size) + 1
                
            else:
                # For rectangles and ellipses, use their position and size
                start_x = max(0, int(obj['x'] * self.tile_width // self.grid_cell_size))
                start_y = max(0, int(obj['y'] * self.tile_height // self.grid_cell_size))
                end_x = int((obj['x'] + obj['width']) * self.tile_width // self.grid_cell_size) + 1
                end_y = int((obj['y'] + obj['height']) * self.tile_height // self.grid_cell_size) + 1
            
            # Add to all overlapping grid cells
            for grid_y in range(start_y, end_y):
                for grid_x in range(start_x, end_x):
                    cell_key = (grid_x, grid_y)
                    if cell_key not in self.spatial_grid:
                        self.spatial_grid[cell_key] = []
                    self.spatial_grid[cell_key].append(obj_idx)
    
    def is_tile_collidable(self, gid):
        """
        Check if a tile with the given GID is collidable
        """
        # Use the dictionary for a quick lookup
        return gid in self.collidable_tiles
    
    def point_in_polygon(self, x, y, points):
        """
        Check if a point is inside a polygon using ray casting algorithm
        """
        inside = False
        j = len(points) - 1
        
        for i in range(len(points)):
            if (((points[i][1] > y) != (points[j][1] > y)) and
                (x < (points[j][0] - points[i][0]) * (y - points[i][1]) / 
                     (points[j][1] - points[i][1]) + points[i][0])):
                inside = not inside
            j = i
            
        return inside

    def is_position_collidable(self, x, y):
        """
        Check if a position is collidable
        """
        # Convert pixel coordinates to tile coordinates
        tile_x = int(x // self.tile_width)
        tile_y = int(y // self.tile_height)
        
        # Check if the tile is within the map bounds
        if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
            if self.collision_map[tile_y * self.map_width + tile_x]:
                return True
        
        # Convert position to tile coordinates for object collision
        x_tiles = x / self.tile_width
        y_tiles = y / self.tile_height
        
        # Check only objects in current grid cell
        grid_x = int(x // self.grid_cell_size)
        grid_y = int(y // self.grid_cell_size)
        cell_key = (grid_x, grid_y)
        
        if cell_key in self.spatial_grid:
            for obj_idx in self.spatial_grid[cell_key]:
                obj = self.collision_objects[obj_idx]
                
                if obj['type'] == 'polygon':
                    # Check polygon collision
                    if self.point_in_polygon(x_tiles, y_tiles, obj['points']):
                        return True
                        
                else:
                    # Convert object coordinates to pixel coordinates
                    obj_x = obj['x'] * self.tile_width
                    obj_y = obj['y'] * self.tile_height
                    obj_width = obj['width'] * self.tile_width
                    obj_height = obj['height'] * self.tile_height
                    
                    if obj['type'] == 'rectangle':
                        # Check rectangular collision
                        if (obj_x <= x < obj_x + obj_width and 
                            obj_y <= y < obj_y + obj_height):
                            return True
                    else:  # ellipse
                        # Check elliptical collision
                        center_x = obj_x + obj_width / 2
                        center_y = obj_y + obj_height / 2
                        
                        # If width or height is zero, skip this object
                        if obj_width == 0 or obj_height == 0:
                            continue
                            
                        # Calculate normalized distance from center
                        dx = (x - center_x) / (obj_width / 2)
                        dy = (y - center_y) / (obj_height / 2)
                        
                        # Check if point is inside ellipse
                        if (dx * dx + dy * dy) <= 1:
                            return True
        
        return False
    
    def render_debug_to_surface(self, surface, camera_x, camera_y, show_spatial_grid=False):
        """
        Render collision debug information to a surface
        
        Args:
            surface: The surface to render to
            camera_x, camera_y: Camera position offset
            show_spatial_grid: Whether to show the spatial grid
        """
        import pygame
        
        # Calculate the visible area based on the camera position
        start_x = max(0, int(camera_x // self.tile_width))
        start_y = max(0, int(camera_y // self.tile_height))
        end_x = min(self.map_width, start_x + (surface.get_width() // self.tile_width) + 2)
        end_y = min(self.map_height, start_y + (surface.get_height() // self.tile_height) + 2)
        
        # Show collision map
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                index = y * self.map_width + x
                if 0 <= index < len(self.collision_map):
                    if self.collision_map[index]:
                        # Draw a red rectangle for collidable tiles
                        draw_x = x * self.tile_width - camera_x
                        draw_y = y * self.tile_height - camera_y
                        pygame.draw.rect(surface, (255, 0, 0), 
                                        (draw_x, draw_y, self.tile_width, self.tile_height), 1)
        
        # Show collision objects
        for obj in self.collision_objects:
            if obj['type'] == 'polygon':
                # Convert polygon points to screen coordinates
                screen_points = []
                for px, py in obj['points']:
                    screen_x = px * self.tile_width - camera_x
                    screen_y = py * self.tile_height - camera_y
                    screen_points.append((screen_x, screen_y))
                
                # Draw polygon outline in purple
                if len(screen_points) >= 2:
                    pygame.draw.polygon(surface, (255, 0, 255), screen_points, 2)
                
            else:
                # Convert object coordinates to screen coordinates
                obj_x = obj['x'] * self.tile_width - camera_x
                obj_y = obj['y'] * self.tile_height - camera_y
                obj_width = obj['width'] * self.tile_width
                obj_height = obj['height'] * self.tile_height
                
                if obj['type'] == 'rectangle':
                    # Draw a blue rectangle
                    pygame.draw.rect(surface, (0, 0, 255), 
                                   (obj_x, obj_y, obj_width, obj_height), 2)
                else:  # ellipse
                    # Draw a green ellipse
                    pygame.draw.ellipse(surface, (0, 255, 0), 
                                      (obj_x, obj_y, obj_width, obj_height), 2)
        
        # Show spatial grid if enabled
        if show_spatial_grid:
            # Calculate visible grid area
            start_grid_x = max(0, int(camera_x // self.grid_cell_size))
            start_grid_y = max(0, int(camera_y // self.grid_cell_size))
            end_grid_x = int((camera_x + surface.get_width()) // self.grid_cell_size) + 1
            end_grid_y = int((camera_y + surface.get_height()) // self.grid_cell_size) + 1
            
            # Draw grid cells
            for grid_y in range(start_grid_y, end_grid_y):
                for grid_x in range(start_grid_x, end_grid_x):
                    cell_key = (grid_x, grid_y)
                    cell_x = grid_x * self.grid_cell_size - camera_x
                    cell_y = grid_y * self.grid_cell_size - camera_y
                    
                    # Draw cell outline
                    pygame.draw.rect(surface, (255, 255, 0), 
                                   (cell_x, cell_y, self.grid_cell_size, self.grid_cell_size), 1)
                    
                    # If cell contains objects, fill with semi-transparent yellow
                    if cell_key in self.spatial_grid and self.spatial_grid[cell_key]:
                        s = pygame.Surface((self.grid_cell_size, self.grid_cell_size))
                        s.set_alpha(64)
                        s.fill((255, 255, 0))
                        surface.blit(s, (cell_x, cell_y))
