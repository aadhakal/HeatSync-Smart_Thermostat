"""
Smart Thermostat package.
Exposes SensorManager, ThermostatLogic, ThermostatGUI and ThermostatApp
so you can do:

    from thermostat import ThermostatApp
    app = ThermostatApp()
    app.run()
"""

from .sensors       import SensorManager
from .control_logic import ThermostatLogic
from .GUI           import ThermostatGUI, ThermostatApp

__all__ = [
    "SensorManager",
    "ThermostatLogic",
    "ThermostatGUI",
    "ThermostatApp",
]
