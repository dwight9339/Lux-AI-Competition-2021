from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position

class Mine:
    def __init__(self, game_state, resource_tile_set, resource_type, debug):
        self.resource_type = resource_type
        self.resource_tiles = resource_tile_set
        self.assigned_workers = {}                                      # Maps worker IDs to assigned worker_tile
        #self.available_resources = 0
        #self.cart_loc = self.get_cart_loc()
        #self.available_work_tiles = len(self.worker_tiles)              # Number of available worker tiles
        self.debug = debug
    
    def _find_cart_loc(self):
        # Find and return the best location to park the cart
        pass
    
    def _get_open_worker_tile(self, worker_pos):
        available_tiles = list(filter(lambda tile: tile not in self.assigned_workers.values(), self.resource_tiles))
        available_tiles = sorted(available_tiles, key=lambda tile: Position(tile[0], tile[1]).distance_to(worker_pos))
        return available_tiles[0]
    
    def get_resource_tiles(self):
        return self.resource_tiles
    
    def worker_assigned(self, worker_id):                               # Checks if a given worker is assigned to mine
        return worker_id in self.assigned_workers
    
    def get_dist(self, loc):                                            # Returns the shortest distance between loc and all spots in mine
        shortest_dist = float("inf")
        
        for tile in self.resource_tiles:
            tile_pos = Position(tile[0], tile[1])
            dist = tile_pos.distance_to(loc)
            if dist < shortest_dist:
                shortest_dist = dist
                
        return shortest_dist
    
    def has_opening(self):                                              # Checks if there are any available spots in mine
        return len(self.resource_tiles) > len(self.assigned_workers)
    
    def assign_worker(self, worker):
        self.assigned_workers[worker.id] = self._get_open_worker_tile(worker.pos)
        
    def release_worker(self, worker):
        self.assigned_workers.pop(worker.id)
        
    def get_assigned_spot(self, worker):
        return self.assigned_workers[worker.id]
    
    def report_resource_depleted(self, pos, assigned_worker):
        self.resource_tiles.remove((pos.x, pos.y))
        self.release_worker(assigned_worker)

    
class Mines:
    def __init__(self, game_state, debug):
        self.mines = []
        self.debug = debug
        
        self._build_mines(game_state)
        
    def _is_valid_tile(self, game_state, x, y, w, h, resource_type, searched):
        if x < 0 or x >= w or y < 0 or y >= h or (x, y) in searched:
            return False
        
        tile = game_state.map.get_cell(x, y)
        if not tile.has_resource() or tile.resource.type != resource_type:
            return False
        
        return True
    
      # This version of the method gathers resource tiles as well as surrounding tiles
#     def _get_resource_cluster(self, game_state, x, y, w, h, resource_type, cluster_tiles=set(), border_tiles=set(), searched=set()):
#         # Given x, y of a starting tile, search game map to find tiles of resource cluster
#         searched.add((x, y))
#         tile = game_state.map.get_cell(x, y)
        
#         if not tile.has_resource():                             # Add tile to border set and make no recursive calls
#             border_tiles.add((x, y))
#             return cluster_tiles, border_tiles, searched
        
#         cluster_tiles.add((x, y))
        
#         for direction in [(1, 0), (0, 1), (-1, 0), (0, -1)]:  # Call function recursively on surrounding tiles
#             new_x, new_y = x + direction[0], y + direction[1]
#             if self._is_valid_tile(game_state, new_x, new_y, w, h, resource_type, searched):
#                 new_cluster_tiles, new_border_tiles, new_searched = self._get_resource_cluster(game_state, new_x, new_y, w, h, resource_type, cluster_tiles, border_tiles, searched)
#                 cluster_tiles = cluster_tiles.union(new_cluster_tiles)
#                 border_tiles = border_tiles.union(new_border_tiles)
#                 searched = searched.union(new_searched)
            
#         return cluster_tiles, border_tiles, searched    
        
    def _get_resource_cluster(self, game_state, x, y, w, h, resource_type, cluster_tiles=set(), searched=set()):
        # Given x, y of a starting tile, search game map to find tiles of resource cluster
        searched.add((x, y))
        tile = game_state.map.get_cell(x, y)
        
        if not tile.has_resource():                             # Add tile to border set and make no recursive calls
            return cluster_tiles, searched
        
        cluster_tiles.add((x, y))
        
        for direction in [(1, 0), (0, 1), (-1, 0), (0, -1)]:  # Call function recursively on surrounding tiles
            new_x, new_y = x + direction[0], y + direction[1]
            if self._is_valid_tile(game_state, new_x, new_y, w, h, resource_type, searched):
                new_cluster_tiles, new_searched = self._get_resource_cluster(game_state, new_x, new_y, w, h, resource_type, cluster_tiles, searched)
                cluster_tiles = cluster_tiles.union(new_cluster_tiles)
                searched = searched.union(new_searched)
            
        return cluster_tiles, searched
        
    def _build_mines(self, game_state): 
        # Iterate over map to find clusters of resource tiles
        w, h = game_state.map.width, game_state.map.height
        searched = set()
        clusters = []
        resource_types = []
        
        for x in range(w):
            for y in range(h):
                if (x, y) in searched:
                    continue
                tile = game_state.map.get_cell(x, y)
                if tile.has_resource():
                    resource_types.append(tile.resource.type)
                    cluster, new_searched = self._get_resource_cluster(game_state, x, y, w, h, tile.resource.type, set(), set())
                    searched = searched.union(new_searched)
                    clusters.append(cluster)
        
        # ToDo: Merge mines of same resource type that share borders
        
        # Build Mine objs from clusters and borders
        for cluster, resource_type in zip(clusters, resource_types):
            self.mines.append(Mine(game_state, cluster, resource_type, self.debug))
        
        if self.debug:
            print("Clusters:", clusters)
#             for cluster in clusters:
#                 for tile in cluster:
#                     self.actions.append(annotate.circle(tile[0], tile[1]))

#             for border in borders:
#                 for tile in border:
#                     self.actions.append(annotate.x(tile[0], tile[1]))
                    
    def update(self, game_state):
        # Check mines to see if they need updated
        for mine in self.mines:
            needs_update = mine.update_mine(game_state)
            
            if needs_update:
                # Find viable cell from mine to seed cluster search
                mine_tiles = mine.get_resource_tiles()
                new_cluster = None
                new_border = None
                
                for tile in mine_tiles:
                    cell = game_state.map.get_cell(tile[0], tile[1])
                
                    if cell.has_resource():
                        new_cluster, new_border, searched = self._get_resource_cluster(game_state, tile[0], tile[1], gamestate.map.width, gamestate.map.height, cell.resource.type, set(), set())
                        break
                
                self.mines.remove(mine)
                
                if new_cluster is not None:
                    self.mines.append(Mine(game_state, new_cluster, new_border, self.debug))
    
    def get_closest_mine(self, loc, resource_type):
        closest_mine = None
        shortest_dist = float("inf")
        
        for mine in self.mines:
            if mine.resource_type != resource_type:
                continue
            for tile in mine.resource_tiles:
                tile_pos = Position(tile[0], tile[1])
                dist = tile_pos.distance_to(loc)
                
                if dist < shortest_dist:
                    shortest_dist = dist
                    closest_mine = mine
                    
        return closest_mine
    
    def place_in_mine(self, worker, resource_type):
        sorted_mines = sorted([mine for mine in self.mines if mine.resource_type == resource_type], key=lambda mine: mine.get_dist(worker.pos))
        
        for mine in sorted_mines:
            if mine.has_opening():
                mine.assign_worker(worker)
                return mine 
            
        return None
