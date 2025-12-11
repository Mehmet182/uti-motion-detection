import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))
from sdks.novavision.src.base.logger import LoggerManager

class Memory:
    # Veri Yapısı:
    # {
    #   "history_state": {
    #       tracker_id: { "center": [x,y], "dims": [w,h], "counter": int }
    #   }
    # }
    _state = {
        "history_state": {}
    }

    _logger = LoggerManager()

    @staticmethod
    def get_state():
        return Memory._state

    @staticmethod
    def update_state(new_state_data: dict):
        for key, value in new_state_data.items():
            Memory._state[key] = value

    @staticmethod
    def reset_state():
        Memory._state = {"history_state": {}}
        # Memory._logger.info("Memory Resetlendi")