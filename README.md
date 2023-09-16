# PowerEngine: A library which calculates signals and electricity.
## Installation
```sh
python -m pip install powerengine
# OR
python -m pip install git+https://github.com/AaravMalani/powerengine
```
## Usage
```py
from powerengine import Engine
engine = Engine()
engine.add_blocks([
    Power(engine, {}, (0, 0, 0)),
    Wire(engine, {'facing': None}, (0, 0, 1)),
    Wire(engine, {'facing': None}, (0, 0, 2)),
    Delayer(engine, {'facing': 'east', 'delay': 5}, (0, 0, 3)),
    Wire(engine, {'facing': None}, (0, 0, 4)),
])
engine.run(3, ignore_speed=True, output=False) 
```
## Plugin Structure
Each plugin is a directory in the `installation/path/plugins` directory.


It contains a `manifest.json` JSON file with the following fields.
| Field             | Type                            | Description                                                                                                                                |
| ----------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| name              | `string`                        | Plugin name                                                                                                                                |
| version           | `string`                        | Plugin version                                                                                                                             |
| author (optional) | `string` or `array[string]`     | The author of the plugin                                                                                                                   |
| blockTypes        | `object[string, array[string]]` | An object of the screaming snake case version of the name to the block types defined (each block type being an array of `[namespace, id]`) |

A plugin is a Python module (it has an `__init__.py`)

An example plugin would be

`main.py`
```py
import powerengine
class PizzaBlock(powerengine.Block):
    id = ('pizzamod', 'pizzablock')
    def update(self, engine : powerengine.Engine):
        self.state['facing'] = {
            'north': 'south',
            'east': 'west',
            'south': 'north',
            'west': 'east'
        }[self.state['facing']]
```

`__init__.py`
```py
from .main import PizzaBlock
```

`manifest.json`
```json
{
    "name": "Pizza Mod",
    "version": "1.0.0",
    "blockTypes": {"PIZZA_BLOCK": ["pizzamod", "pizzablock"]}
}
```