import sys
import os

# SDK yollarını ekleyerek LoggerManager'ın bulunmasını garantiye alıyoruz
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

from sdks.novavision.src.base.logger import LoggerManager


class Memory:
    """
    Frame'ler arasında veri sürekliliğini sağlamak için kullanılan statik hafıza sınıfı.
    NovaVision SDK her frame'de component'i yeniden başlatsa bile bu sınıf silinmez.
    """

    # Program çalıştığı sürece hafızada kalacak veriler
    _state = {
        "previous_centers": {},  # {trackerID: [x, y]}
        "stationary_counters": {}  # {trackerID: int}
    }

    # Standart logging yerine sistemin LoggerManager'ını başlatıyoruz
    _logger = LoggerManager()

    @staticmethod
    def get_state():
        """Mevcut hafızayı döndürür."""
        return Memory._state

    @staticmethod
    def update_state(previous_centers: dict, stationary_counters: dict):
        """Hafızayı yeni verilerle günceller."""
        Memory._state["previous_centers"] = previous_centers
        Memory._state["stationary_counters"] = stationary_counters

    @staticmethod
    def reset_state():
        """Hafızayı sıfırlar (Gerekirse kullanılır)."""
        Memory._state = {
            "previous_centers": {},
            "stationary_counters": {}
        }
        # LoggerManager üzerinden info logu atıyoruz
        Memory._logger.info("Motion Detection Memory Reset")