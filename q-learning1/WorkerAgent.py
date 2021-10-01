from enum import Enum, auto
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES, Position
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
import sys
import math

class WorkerObjective(Enum):
    GatherFuel = "gather fuel"
    BuildCity = "build city"
    Rest = "rest"

class WorkerAgent:
    def __init__(self, worker_obj, debug):
        self.debug = debug
        self.worker = worker_obj
        self.objective = WorkerObjective.BuildCity
        self.objective_changed = False
        self.mine = None
        self.destination = None
        
    def update(self, worker_obj):
        self.worker = worker_obj
    
    def _find_open_mine(self, resource_type, mines):
        mine = mines.place_in_mine(self.worker, resource_type)
        if mine is not None:
            self.mine = mine
        
    def _get_best_fuel(self, player):
        resource_type = RESOURCE_TYPES.WOOD
        if player.researched_coal():
            resource_type = RESOURCE_TYPES.COAL
        if player.researched_uranium():
            resource_type = RESOURCE_TYPES.URANIUM
            
        return resource_type
    
    def _at_mining_spot(self):
        mining_spot = self.get_mining_spot()
        if mining_spot is None:
            return False
        
        return self.worker.pos == mining_spot
    
    def _update_mining(self, controller):
        if self._at_mining_spot():
            cell = controller.map.get_cell_by_pos(self.worker.pos)
            if not cell.has_resource():
                self.mine.report_resource_depleted(self.worker.pos, self.worker)
                self.mine = None
         
        if self.objective == WorkerObjective.GatherFuel:
            best_fuel = self._get_best_fuel(controller.player)
            if self.mine is not None and self.mine.resource_type != best_fuel:
                self.mine.release_worker(self.worker)
                self._find_open_mine(best_fuel, controller.mines)
                
    def _handle_objective_change(self):
        if self.objective_changed:
            if self.mine != None:
                self.mine.release_worker(self.worker)
                self.mine = None
            self.destination = None
            self.objective_changed = False
            if self.debug:
                print("Worker", self.worker.id, "assigned new objective")
                
    def _handle_mine_assignment(self, controller):
        if self.destination is None and self.mine is None and self.objective != WorkerObjective.Rest:
            resource_type = RESOURCE_TYPES.WOOD
            if self.objective == WorkerObjective.GatherFuel:
                resource_type = self._get_best_fuel(controller.player)
            self._find_open_mine(resource_type, controller.mines)
            if self.debug:
                if self.mine is not None:
                    print("Worker", self.worker.id, "assigned to mining spot", self.get_mining_spot())
                else:
                    print("Unable to place worker", self.worker.id, "in mine")
                
    def _handle_destination_arrival(self):
        if self.destination is not None and self.worker.pos == self.destination:
            self.destination = None  
            if self.debug:
                print("Worker", self.worker.id, "arrived at their destination")
        
    def _handle_destination_assignment(self, controller):
        if self.destination is not None:
            return
        
        if self.objective == WorkerObjective.Rest and not self.on_city_tile(controller.map):
            closest_city_tile = controller.cities.get_nearest_city_tile(self.worker.pos)
            if closest_city_tile is not None:
                self.destination = closest_city_tile.pos
            if self.debug:
                print("Worker", self.worker.id, "destination set to city tile", (self.destination.x, self.destination.y))
            return
            
        if self.worker.get_cargo_space_left() == 0: 
            if self.mine is not None:
                self.mine.release_worker(self.worker)
                self.mine = None

            if self.debug:
                print("Worker", self.worker.id, "is at max cargo")
            if self.objective == WorkerObjective.GatherFuel:
                nearest_city_tile = controller.cities.get_nearest_city_tile(self.worker.pos)
                if nearest_city_tile is not None:
                    self.destination = nearest_city_tile.pos
            elif self.objective == WorkerObjective.BuildCity:
                # nearest_periph = controller.cities.get_nearest_periph_pos(self.worker.pos, controller.map)
                # if nearest_periph is not None:
                #     self.destination = nearest_periph
                # else:
                self.destination = self.find_nearest_empty_tile(self.worker.pos, controller.map)
            if self.debug:
                print("Worker", self.worker.id, "destination changed to", self.destination)
            return
                   
        if not self._at_mining_spot():
            self.destination = self.get_mining_spot()
            if self.debug:
                print("Worker", self.worker.id, "returning to minining spot", self.get_mining_spot())
            return
                
        
    def get_mining_spot(self):
        if self.mine == None:
            return None
        
        tile = self.mine.get_assigned_spot(self.worker)
        if tile is not None:
            return Position(tile[0], tile[1])
        return None
        
    def set_objective(self, objective):
        if self.objective == objective:
            return
        self.objective = objective
        self.objective_changed = True
        if self.debug:
            print("Worker", self.worker.id, "has new objective", self.objective)
        
    def get_step_direction(self, game_map, avoid_city=False):
        direction = self.worker.pos.direction_to(self.destination)
        
        if avoid_city:                     # Get best detour
            alt_dirs = ["n", "s"] if direction in ["e", "w"] else ["e", "w"]
            step = step = self.worker.pos.translate(direction, 1)
            
            cell = game_map.get_cell(step.x, step.y)
            if cell.citytile is None:
                return direction
            
            shortest_dist = float("inf")
            best_dir = None
            for alt_dir in alt_dirs:
                step = self.worker.pos.translate(alt_dir, 1)
                if step.x < 0 or step.x >= game_map.width or step.y < 0 or step.y >= game_map.height:
                    continue
                cell = game_map.get_cell(step.x, step.y)
                dist = step.distance_to(self.destination) 
                if cell.citytile is None and dist < shortest_dist:
                    best_dir = alt_dir
                    
            if best_dir is not None:
                return best_dir
            
            backward_dir = set(["n", "s", "e", "w"]).difference(set([direction] + alt_dirs)).pop()
            return backward_dir
              
        return direction
            
    
    def on_city_tile(self, game_map):
        tile = game_map.get_cell_by_pos(self.worker.pos)
        return tile.citytile is None
    
    def find_nearest_empty_tile(self, loc, game_map):
        if self.tile_is_empty(loc, game_map):
            return loc
        
        searched = set()
        q = [loc]
        
        while len(q) > 0:
            p = q.pop(0)
            searched.add((p.x, p.y))
            
            if self.tile_is_empty(p, game_map):
                return p
            
            for direction in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                neighbor = Position(p.x + direction[0], p.y + direction[1])
                if neighbor.x >= 0 and neighbor.x < game_map.width and neighbor.y >= 0 and neighbor.y < game_map.height and (neighbor.x, neighbor.y) not in searched:
                    q.append(neighbor)
            
            
    def tile_is_empty(self, pos, game_map):
        cell = game_map.get_cell(pos.x, pos.y)
        return cell.citytile is None and not cell.has_resource()
    
    def get_action(self, controller, steps):
        self._update_mining(controller)
        
        if not self.worker.can_act():
            return None, (self.worker.pos.x, self.worker.pos.y)
        
        self._handle_objective_change()
        self._handle_mine_assignment(controller)
        self._handle_destination_arrival()
        
        if self.destination is None and self.objective == WorkerObjective.BuildCity and self.worker.can_build(controller.map):
            if self.debug:
                print("Worker", self.worker.id, "building city tile at", self.worker.pos)
            return self.worker.build_city(), (self.worker.pos.x, self.worker.pos.y)
        
        self._handle_destination_assignment(controller)
                
        if self.destination is not None:
            avoid_city = self.objective == WorkerObjective.BuildCity and self.worker.get_cargo_space_left() == 0
            step_dir = self.get_step_direction(controller.map, avoid_city)
            if self.debug:
                print("Worker", self.worker.id, "step direction:", step_dir)
            # step_dir = self.worker.pos.direction_to(self.destination)
            step = self.worker.pos.translate(step_dir, 1)
            return self.worker.move(step_dir), (step.x, step.y)
        
        return None, (self.worker.pos.x, self.worker.pos.y)
    
class Workers:
    def __init__(self, worker_list, debug):
        self.debug = debug
        self.workers = {}                              # Maps worker ids to WorkerAgent objs
        self.task_proportions = [0.5, 0.5, 0.0]
        
        for worker in worker_list:
            self.workers[worker.id] = WorkerAgent(worker, self.debug)
            
        if self.debug:
            print("Workers object initialized")

        self._reassign_objectives()
            
    def _reassign_objectives(self):
        num_city_builders = math.ceil(self.task_proportions[0] * len(self.workers))
        num_fuel_gatherers = math.ceil(self.task_proportions[1] * len(self.workers))
        worker_ids = self.workers.keys()
        
        for i, worker_id in enumerate(worker_ids):
            if i < num_city_builders:
                self.workers[worker_id].set_objective(WorkerObjective.BuildCity)
                continue
            if i < num_city_builders + num_fuel_gatherers:
                self.workers[worker_id].set_objective(WorkerObjective.GatherFuel)
                continue
            self.workers[worker_id].set_objective(WorkerObjective.Rest)

    # Converts directions to degrees
    def _to_degrees(self, direction):
        directions = ["w", "s", "e", "n"]
        return 90 * directions.index(direction)

    # Converts degrees to directions
    def _to_dir(self, degrees):
        directions = ["w", "s", "e", "n"]
        return directions[int((degrees % 360) / 90)]
        

    # Returns the direction 90 degrees * times clockwise of direction
    def _rotate_dir(self, direction, times):
        return self._to_dir(self._to_degrees(direction) + 90 * times)
        
    def update(self, worker_list):
        if self.debug:
            print("Updating workers object")
           
        # Remove workers that were lost last turn
        lost_workers = set(self.workers.keys()).difference(set([worker.id for worker in worker_list]))
        for lost_worker in lost_workers:
            self.workers.pop(lost_worker)
            
        for worker in worker_list:
            if worker.id in self.workers:
                self.workers[worker.id].update(worker)
                continue
                
            self.workers[worker.id] = WorkerAgent(worker, self.debug)
            self._reassign_objectives()
            if self.debug:
                print("Worker added")
                
    def update_task_proportions(self, proportions):
        self.task_proportions = proportions
        self._reassign_objectives()
            
            
    def get_actions(self, controller):
        actions = []
        steps = set()
        
        for worker in self.workers.values():
            action, step = worker.get_action(controller, steps)
            steps.add(step)
            if action is not None:
                actions.append(action)
                
        return actions
