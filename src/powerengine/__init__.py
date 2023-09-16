from __future__ import annotations
from abc import ABC, abstractmethod
import time
import uuid
import typing
import pprint
import pickle
import os
import importlib
import json

class BlockType:
    """A holding class which lists the block types (namespace, id)"""
    WIRE = ("default", "wire")
    LEVER = ("default", "lever")
    POWER = ("default", "power")
    DELAYER = ("default", "delayer")
    AIR = ("default", "air")


class Block(ABC):
    """An abstract base class for Blocks"""
    id: BlockType

    def __init__(self, engine: Engine, state: dict, coords: tuple):
        self.state = state
        self.coords = coords
        self.last_updated = engine.tick-1
        self.gid = str(uuid.uuid4())
        self.update(engine)

    @abstractmethod
    def update(self, engine: Engine):
        """A method used to update the block state every tick

        Args:
            engine (Engine): The engine instance
        """
        ...

    def __eq__(self, __value: object) -> bool:
        return (type(self) is type(__value)) and (self.gid == __value.gid)

    def __repr__(self):
        return self.__class__.__name__+"(coords="+str(self.coords)+", state="+str(self.state)+", last_updated="+str(self.last_updated)+")"

    def __hash__(self) -> int:
        return hash(self.gid)


class Engine:
    """The primary engine which stores the blocks and executes block updates"""
    SPEED: typing.Annotated[int, "The number of ticks per second"] = 20
    VERSION: typing.Annotated[tuple, "The version of the engine"] = (1, 0, 0)

    def __init__(self, load_plugins: bool = True):
        """The constructor

        Args:
            load_plugins (bool, optional): Whether to load plugins from plugins/ (from the module's directory not the current directory). Defaults to True.
        """
        self.tick: int = 1
        self.blocks: dict[tuple[int], Block] = {}
        self.update_buffer: set = set()
        if load_plugins:
            Engine.load_plugins()

    @classmethod
    def load_plugins(self):
        for i in os.listdir(os.path.dirname(__file__)+'/plugins'):
            if not os.path.isdir(os.path.dirname(__file__)+'/plugins/'+i):
                continue
            if not os.path.isfile(os.path.dirname(__file__)+'/plugins/'+i+'/manifest.json'):
                continue
            with open(os.path.dirname(__file__)+'/plugins/'+i+'/manifest.json', 'r') as f:
                manifest = json.load(f)
            for x in manifest['blockTypes']:
                setattr(BlockType, x, tuple(manifest['blockTypes'][x]))
            module = importlib.import_module('.'+i, __name__+'.plugins')
            for i in dir(module):
                if i.startswith('__'):
                    continue
                globals()[i] = getattr(module, i)

    @classmethod
    def load(self, file: str, load_plugins: bool = True):
        """Loads an engine from a save file

        Args:
            file (str): The file to load the engine from
            load_plugins (bool, optional): Whether to load plugins from plugins/ (from the module's directory not the current directory). Defaults to True.

        Raises:
            Exception: Raised if file is loaded from higher version
        """
        if load_plugins:
            Engine.load_plugins()
        with open(file, 'rb') as f:
            data = pickle.load(f)
            version = data[0]
            if version > Engine.VERSION:
                raise Exception("Unknown version!")
            engine = Engine(load_plugins=False)
            engine.blocks, engine.tick = data[1:]

    def save(self, file: str):
        """Saves an engine to a save file

        Args:
            file (str): The file to save the engine to
        """
        with open(file, 'wb') as f:
            pickle.dump((Engine.VERSION, self.blocks, self.tick), f)

    def tick_ahead(self):
        """Executes a single tick"""
        lst = self.blocks.values()
        while True:
            lst = filter(lambda x: x.last_updated != self.tick, lst)
            try:
                self.update_buffer = set([next(lst)])
            except:
                break
            while self.update_buffer:
                self.update_buffer.pop().update(self)
        self.tick += 1

    def run(self, ticks: int = -1, output=True, ignore_speed=False):
        """Executes a certain (or infinite) number of ticks

        Args:
            ticks (int, optional): The number of ticks to execute. Defaults to -1.
            output (bool, optional): Outputs the blocks to stdout. Defaults to True.
            ignore_speed (bool, optional): Executes the ticks without maintaining the speed in Engine.SPEED. Defaults to False.
        """
        while ticks:
            start = time.time()
            self.tick_ahead()
            if output:
                pprint.pprint(self.blocks)
                print()
            end = time.time()
            if not ignore_speed:
                time.sleep(max(1/Engine.SPEED - (end-start), 0))
            ticks -= 1

    def get_block(self, coords: tuple[int]) -> Block:
        """Get the block at a certain set of coordinates

        Args:
            coords (tuple[int]): The coordinates of the block

        Returns:
            Block: The block at the given coordinates (or air if no block is present)
        """
        return self.blocks.get(coords, Air(self, {}, coords))

    def add_blocks(self, blocks: list[Block]):
        """Adds a list of blocks to the world

        Args:
            blocks (list[Block]): The list of blocks to add
        """

        self.blocks.update({i.coords: i for i in blocks})

    def schedule_update(self, block: Block):
        """Schedules a block update

        Args:
            block (Block): The block to be updated
        """
        self.update_buffer.add(block)


class Utils:
    """A class with utilities"""
    @classmethod
    def get_surrounding_block(self, coords: tuple[int], direction: typing.Optional[typing.Union[list[str], str]] = None) -> tuple[tuple[int]]:
        """The function to get the coordinates(s) in a particular direction(s) ('north', 'south', 'east' or 'west') adjacent to the given coordinates

        Args:
            coords (tuple): The coordinates 
            direction (typing.Optional[typing.Union[list[str], str]], optional): Either an iterable or a string (a particular direction(s)) which returns respective coordinates in the given directions, or None which returns in coordinates for all the directions. Defaults to None.

        Returns:
            tuple[tuple[int]]: A tuple of coordinates
        """
        if type(direction or ['north', 'south', 'east', 'west']) is list:
            return tuple(self.__get_surrounding_blocks(coords, direction or ['north', 'south', 'east', 'west']))
        return self.__get_surrounding_block(coords, direction)

    @classmethod
    def __get_surrounding_block(self, coords, direction: str) -> tuple[tuple[int]]:
        return ({
            'north': (coords[0]+1, coords[1], coords[2]),
            'south': (coords[0]-1, coords[1], coords[2]),
            'west': (coords[0], coords[1], coords[2]+1),
            'east': (coords[0], coords[1], coords[2]-1),
        }[direction],)

    @classmethod
    def __get_surrounding_blocks(self, coords, directions: list[str] = None):
        for i in (directions or ['north', 'south', 'east', 'west']):
            yield {
                'north': (coords[0]+1, coords[1], coords[2]),
                'south': (coords[0]-1, coords[1], coords[2]),
                'west': (coords[0], coords[1], coords[2]+1),
                'east': (coords[0], coords[1], coords[2]-1),
            }[i]


class Air(Block):
    """A class for the air block"""
    id = BlockType.AIR

    def update(self, engine: Engine):
        pass


class Wire(Block):
    """A class for the wire block used to transmit power"""
    id = BlockType.WIRE

    def update(self, engine: Engine):
        self.state['signal'] = 0
        for i in Utils.get_surrounding_block(self.coords, self.state['facing']):
            block = engine.get_block(i)
            if block.last_updated <= self.last_updated and block.id != BlockType.AIR:
                engine.schedule_update(block)
            if block.state.get('facing') and ((type(block.state['facing']) is str and self.coords not in list(Utils.get_surrounding_block(block.coords, [{'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}[block.state['facing']]]))) or (type(block.state['facing']) is list and self.coords not in list(Utils.get_surrounding_block(block.coords, block.state['facing'])))):
                continue
            self.state['signal'] = max(block.state.get(
                'signal', 0)-1, self.state['signal'])

        self.last_updated = engine.tick


class Power(Block):
    """A class for the power block used to generate power"""
    id = BlockType.POWER

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state['signal'] = 16

    def update(self, engine: Engine):
        for i in Utils.get_surrounding_block(self.coords):
            block = engine.get_block(i)
            if block.last_updated != engine.tick and block.id != BlockType.AIR:
                engine.schedule_update(block)

        self.last_updated = engine.tick


class Delayer(Block):
    """A class for the delayer block used to send a delayed signal

    Requires 'facing' (string) and 'delay' (int) in block state
    """
    id = BlockType.DELAYER

    def update(self, engine: Engine):
        input_coords = Utils.get_surrounding_block(
            self.coords, self.state['facing'])[0]

        output_coords = Utils.get_surrounding_block(self.coords, {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east'
        }[self.state['facing']])[0]

        input_block, output_block = engine.get_block(
            input_coords), engine.get_block(output_coords)
        if (input_block.state.get('facing') and self.coords not in Utils.get_surrounding_block(input_block.state['facing'])) or (output_block.state.get('facing') and self.coords not in Utils.get_surrounding_block(output_block.state['facing'])):
            return
        if input_block.state.get('signal'):
            self.state['timer'] = max(self.state.get(
                'timer')-1 if self.state.get('timer') else self.state['delay'], 0)
            if not self.state['timer']:
                self.state['signal'] = 16
        else:
            try:
                del self.state['timer']
            except:
                pass
            self.state['signal'] = 0
        if input_block.last_updated != engine.tick and input_block.id != BlockType.AIR:
            engine.schedule_update(input_block)
        if output_block.last_updated != engine.tick and output_block.id != BlockType.AIR:
            engine.schedule_update(output_block)
        self.last_updated = engine.tick


if not os.path.isdir(os.path.dirname(__file__)+'/plugins'):
    os.mkdir(os.path.dirname(__file__)+'/plugins')
