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
    # track_history: { tracker_id: [ {bbox:..., roi:...}, ... ] }
    _state = {
        "track_history": {}
    }

    _logger = LoggerManager()

    @staticmethod
    def get_state():
        """Mevcut hafızayı döndürür."""
        return Memory._state

    @staticmethod
    def update_state(new_state_data: dict):
        """
        Hafızayı yeni verilerle günceller (Merge mantığı veya overwrite).
        """
        for key, value in new_state_data.items():
            Memory._state[key] = value

    @staticmethod
    def reset_state():
        """Hafızayı sıfırlar."""
        Memory._state = {
            "track_history": {}
        }
        # Memory._logger.info("Motion Detection Memory Reset")