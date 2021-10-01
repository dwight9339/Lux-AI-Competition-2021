from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
import sys

class Mine:
    def __init__(self, id, resource_tile_set, resource_type, debug):
        self.id = id
        self.resource_type = resource_type
        self.resource_tiles = resource_tile_set
        self.assigned_workers = set()
        self.spot_assignments = {}
        self.debug = debug
    
    def update(self, game_map):
        depleted = []

        for tile in self.resource_tiles:
            cell = game_map.get_cell(tile[0], tile[1])
            if not cell.has_resource():
                depleted.append(tile)
        
        for tile in depleted:
            self.resource_tiles.remove(tile)
    
    def get_open_worker_tile(self, worker):
        available_tiles = list(filter(lambda tile: tile not in self.spot_assignments.values(), self.resource_tiles))
        if self.debug:
            print("Searching for open mining spot in", self.id, "for worker", worker.id, file=sys.stderr)
            print(self.id, "avaiable mining spots:", available_tiles, file=sys.stderr)
        if len(available_tiles) == 0:
            return None
        available_tiles = sorted(available_tiles, key=lambda tile: Position(tile[0], tile[1]).distance_to(worker.pos))
        self.spot_assignments[worker.id] = available_tiles[0]
        return available_tiles[0]
    
    def worker_assigned(self, worker):                               # Checks if a given worker is assigned to mine
        return worker in self.assigned_workers

    def is_depleted(self):
        return len(self.resource_tiles) == 0
    
    def get_dist(self, loc):                                            # Returns the shortest distance between loc and all spots in mine
        shortest_dist = float("inf")
        
        for tile in self.resource_tiles:
            tile_pos = Position(tile[0], tile[1])
            dist = tile_pos.distance_to(loc)
            if dist < shortest_dist:
                shortest_dist = dist
                
        return shortest_dist
    
    def has_opening(self):                                              # Checks if there are any available spots in mine
        return len(self.resource_tiles) > len(self.assigned_workers) and not self.is_depleted()
    
    def assign_worker(self, worker):
        self.assigned_workers.add(worker.id)
        
    def release_worker(self, worker):
        self.assigned_workers.remove(worker.id)
        
    def get_mining_spot(self, worker):
        if worker.id in self.spot_assignments:
            return self.spot_assignments[worker.id]
        mining_spot = self.get_open_worker_tile(worker)
        if mining_spot is None:
            return None
        self.spot_assignments[worker.id] = mining_spot
        return mining_spot

    def leave_mining_spot(self, worker):
        if worker.id in self.spot_assignments:
            self.spot_assignments.pop(worker.id)
    
    def report_resource_depleted(self, pos, assigned_worker):
        self.resource_tiles.remove((pos.x, pos.y))

    
class Mines:
    def __init__(self, game_state, debug):
        self.mines = []
        self.debug = debug
        self.best_fuel = RESOURCE_TYPES.WOOD
        self._build_mines(game_state)

    def update(self, player):
        self.best_fuel = self._get_best_fuel(player)

    def _get_best_fuel(self, player):
        resource_type = RESOURCE_TYPES.WOOD
        if player.researched_coal():
            resource_type = RESOURCE_TYPES.COAL
        if player.researched_uranium():
            resource_type = RESOURCE_TYPES.URANIUM
            
        return resource_type
        
    def _is_valid_tile(self, game_state, x, y, w, h, resource_type, searched):
        if x < 0 or x >= w or y < 0 or y >= h or (x, y) in searched:
            return False
        
        tile = game_state.map.get_cell(x, y)
        if not tile.has_resource() or tile.resource.type != resource_type:
            return False
        
        return True 
        
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
        
        # Build Mine objs from clusters
        id = 0
        for cluster, resource_type in zip(clusters, resource_types):
            self.mines.append(Mine("mine_" + str(id), cluster, resource_type, self.debug))
            id += 1
        
        if self.debug:
            print("Clusters:", clusters, file=sys.stderr)
                    
    
    def get_closest_mine(self, loc, resource_type):
        viable_mines = [mine for mine in self.mines if not mine.is_depleted and mine.resource_type == resource_type]
        if len(viable_mines) == 0:
            return None
        viable_mines = sorted(viable_mines, key=lambda mine: mine.get_dist(loc))
        return viable_mines[0]
    
    def place_in_mine(self, worker):
        sorted_mines = sorted([mine for mine in self.mines if mine.resource_type == self.best_fuel], key=lambda mine: mine.get_dist(worker.pos))
        
        for mine in sorted_mines:
            if mine.has_opening():
                mine.assign_worker(worker)
                return mine 
            
        return None
