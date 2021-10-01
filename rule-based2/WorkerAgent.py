from lux.game_map import RESOURCE_TYPES, Position
import math
import sys

class WorkerAgent:
    def __init__(self, worker_obj, mines, debug):
        self.debug = debug
        self.worker = worker_obj
        self.mine = self._find_open_mine(mines)
        self.destination = None
        self.resting = False
        
    def update(self, worker_obj):
        self.worker = worker_obj
    
    def _find_open_mine(self, mines):
        mine = mines.place_in_mine(self.worker)
        if mine is not None:
            if self.debug:
                print("Worker", self.worker.id, "assigned to", mine.id, file=sys.stderr)
        return mine
        
    def get_mining_spot(self):
        if self.mine == None:
            return None
        
        tile = self.mine.get_mining_spot(self.worker)
        if tile is None:
            return None
        return Position(tile[0], tile[1])    

    def leave_mining_spot(self):
        self.mine.leave_mining_spot(self.worker)     
    
    def find_nearest_empty_tile(self, game_map):
        if self.tile_is_empty(self.worker.pos, game_map):
            return self.worker.pos
        
        searched = set()
        q = [self.worker.pos]
        
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
    
    def get_action(self, controller):
        if self.resting or not self.worker.can_act():
            return None, None

        if self.destination is not None and self.worker.pos == self.destination:
            self.destination = None

        if self.destination is not None:
            direction = self.worker.pos.direction_to(self.destination)
            step = self.worker.pos.translate(direction, 1)
            return self.worker.move(direction), (step.x, step.y)

        # Build city tile and stay put
        if self.worker.can_build(controller.map):
            if self.debug:
                print("Worker", self.worker.id, "building city at", self.worker.pos, file=sys.stderr)
            self.resting = True
            return self.worker.build_city(), None

        # If no resources, gather resources
        if self.worker.get_cargo_space_left() > 0:
            if self.mine.is_depleted():
                self.mine = self._find_open_mine(controller.mines)
            if self.debug:
                print("Worker", self.worker.id, "searching for mining spot", file=sys.stderr)
            mining_spot = self.get_mining_spot()
            if mining_spot is None:
                return None, None
            self.destination = mining_spot
            direction = self.worker.pos.direction_to(self.destination)
            step = self.worker.pos.translate(direction, 1)
            return self.worker.move(direction), (step.x, step.y)

        # If has resources, find nearest empty tile and go to it
        if self.worker.get_cargo_space_left() == 0:
            self.leave_mining_spot()
            self.destination = self.find_nearest_empty_tile(controller.map)
            direction = self.worker.pos.direction_to(self.destination)
            step = self.worker.pos.translate(direction, 1)
            return self.worker.move(direction), (step.x, step.y)
    
class Workers:
    def __init__(self, worker_list, mines, debug):
        self.debug = debug
        self.workers = {}                              # Maps worker ids to WorkerAgent objs
        self.task_proportions = [0.8, 0.2, 0.0]
        
        for worker in worker_list:
            self.workers[worker.id] = WorkerAgent(worker, mines, self.debug)
            
        if self.debug:
            print("Workers object initialized", file=sys.stderr)
            
        
    def update(self, mines, worker_list):
        if self.debug:
            print("Updating workers object", file=sys.stderr)
           
        # Remove workers that were lost last turn
        lost_workers = set(self.workers.keys()).difference(set([worker.id for worker in worker_list]))
        for lost_worker in lost_workers:
            self.workers.pop(lost_worker)
            
        for worker in worker_list:
            if worker.id in self.workers:
                self.workers[worker.id].update(worker)
                continue
                
            self.workers[worker.id] = WorkerAgent(worker, mines, self.debug)
            if self.debug:
                print("Worker added", file=sys.stderr)            
            
    def get_actions(self, controller):
        actions = []
        steps = set()
        
        for worker in self.workers.values():
            action, step = worker.get_action(controller)
            if step is not None:
                if step in steps: # If another worker is already moving to that spot, don't do anything
                    continue
                steps.add(step)
            if action != None:
                actions.append(action)
                
        return actions
