from lux.game_map import Cell, RESOURCE_TYPES, Position

class CityWrapper:
    def __init__(self, city_obj, debug):
        self.city = city_obj
        self.debug = debug
    
    def get_nearest_periph_pos(self, loc, game_map):
        if self.debug:
            print("Searching for city build location")
        # Return periphery tile obj closest to loc (Only works if loc is not inside city)
        
        # Sort tiles in city according to distance from loc
        sorted_tiles = sorted(self.city.citytiles, key=lambda tile: tile.pos.distance_to(loc))

        for tile in sorted_tiles:
            for direction in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                neighbor = Position(tile.pos.x + direction[0], tile.pos.y + direction[1])
                if neighbor.x >= 0 and neighbor.x < game_map.width and neighbor.y >= 0 and neighbor.y < game_map.height:
                    cell = game_map.get_cell(neighbor.x, neighbor.y)
                    if cell.citytile == None and not cell.has_resource():
                        return neighbor
                    
        return None
    
    def get_nearest_city_tile(self, loc):
        # Return city tile closest to loc
        shortest_dist = float("inf")
        closest = None
        for tile in self.city.citytiles:
            dist = tile.pos.distance_to(loc)
            if dist < shortest_dist:
                shortest_dist = dist
                closest = tile
        return closest
    
    def get_actions(self, controller, workers_needed):
        actions = []
        workers_built = 0
        for tile in self.city.citytiles:
            if tile.can_act():
                if workers_needed - workers_built > 0:
                    actions.append(tile.build_worker())
                    workers_built += 1
                    if self.debug:
                        print("City tile", tile.pos, "creating new worker.")
                    continue
                actions.append(tile.research())
        return actions, workers_built
    
class CitiesWrapper:
    def __init__(self, cities_list, debug):
        self.cities = [CityWrapper(city, debug) for city in cities_list]
        self.debug = debug
        
    def update(self, cities_list):
        self.cities = [CityWrapper(city, self.debug) for city in cities_list]
    
    def get_nearest_city(self, loc):
        # Return CityWrapper obj closest to loc
        shortest_dist = float("inf")
        closest = None
        
        for city in self.cities:
            dist = city.get_nearest_city_tile(loc).pos.distance_to(loc)
            if dist < shortest_dist:
                shortest_dist = dist
                closest = city
                
        return closest
    
    def get_nearest_city_tile(self, loc):
        # Return CityTile obj closest to loc
        shortest_dist = float("inf")
        closest = None
        
        for city in self.cities:
            tile = city.get_nearest_city_tile(loc)
            dist = tile.pos.distance_to(loc)
            if dist < shortest_dist:
                shortest_dist = dist
                closest = tile
                
        return closest
    
    def get_nearest_periph_pos(self, loc, game_map):
        sorted_cities = sorted(self.cities, key=lambda city: city.get_nearest_city_tile(loc).pos.distance_to(loc))
        
        for city in sorted_cities:
            periph = city.get_nearest_periph_pos(loc, game_map)
            if periph is not None:
                return periph
            
        return None
    
    def get_actions(self, controller):
        actions = []
        workers_needed = max(controller.state.num_city_tiles - controller.state.num_workers, 0)
        
        for city in self.cities:
            city_actions, workers_built = city.get_actions(controller, workers_needed)
            actions += city_actions
            workers_needed -= workers_built
            
        return actions
