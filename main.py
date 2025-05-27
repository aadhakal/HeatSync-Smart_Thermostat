import logging
from kivy import Config

# set window size before any Kivy imports
Config.set('graphics', 'width', '480')
Config.set('graphics', 'height', '320')
Config.set('graphics', 'resizable', '0')

logging.basicConfig(
    filename='thermostat.log',
    level=logging.INFO,
    format='%(Y-%m-%d %H:%M:%S) %(levelname)s: %(message)s'
)

from thermostat import ThermostatApp

if __name__ == "__main__":
    ThermostatApp().run()

