import sys
import math
from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from components.Package.src.utils.response import build_response
from components.Package.src.models.PackageModel import PackageModel


# Sizin custom import'larınız: build_response fonksiyonunu burada varsayıyoruz.
# Eğer bu fonksiyon dışarıdan geliyorsa, burada import edilmelidir.
# from components.Package.src.utils.response import build_response
# (Yorum satırı olarak bıraktım, kendi ortamınıza göre düzenleyin)

# Varsayım: build_response fonksiyonunuzun tanımı (Bu kısım normalde başka bir dosyada olur.)
# Eğer OnDetection içinde değilse, bu kısım kaldırılıp import edilmelidir.
class MotionDetector(Component):

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data))

        self.detections= self.request.get_param("inputDetections")
        print(f"Motion Detection Input Detections: {self.detections}")
        self.motion_threshold = self.request.get_param("ConfigMotionThreshold")
        print(f"Motion Detection Threshold: {self.motion_threshold}")
        self.stationary_frames_limit = self.request.get_param("ConfigStationaryFrames")
        print(f"Motion Detection Stationary Frames Limit: {self.stationary_frames_limit}")

        self.previous_centers = self.bootstrap.get("previous_centers")
        self.stationary_counters= self.bootstrap.get("stationary_counters")

    @staticmethod
    def bootstrap(config: dict) -> dict:
        """Kareler arasında durumu korumak için kullanılır."""
        return {
            "previous_centers": {},
            "stationary_counters": {}
        }

    def calculate_center(self, bbox: Dict[str, float]) -> tuple:
        """Sınır kutusunun merkez koordinatlarını hesaplar."""
        center_x = bbox["left"] + bbox["width"] / 2
        center_y = bbox["top"] + bbox["height"] / 2
        return (center_x, center_y)

    def process_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Algılamaları işler, hareket durumunu ekler ve bir sonraki kare için durumu günceller."""
        if not detections:
            # Algılama yoksa durumu sıfırla
            self.bootstrap["previous_centers"] = {}
            self.bootstrap["stationary_counters"] = {}
            return []

        current_centers: Dict[int, tuple] = {}
        new_stationary_counters: Dict[int, int] = {}
        processed_detections: List[Dict[str, Any]] = []

        for detection in detections:
            bbox = detection.get("boundingBox")
            tracker_id = detection.get("trackerID")

            motion_status = "BİLİNMİYOR"

            if bbox and tracker_id is not None:
                current_center = self.calculate_center(bbox)
                current_centers[tracker_id] = current_center

                prev_center = self.previous_centers.get(tracker_id)
                current_counter = self.stationary_counters.get(tracker_id, 0)

                # Sadece önceki karede de mevcutsa ve bu bir başlangıç karesi değilse hesapla
                if prev_center is not None:
                    distance = math.sqrt(
                        (current_center[0] - prev_center[0]) ** 2 +
                        (current_center[1] - prev_center[1]) ** 2
                    )

                    if distance > self.motion_threshold:
                        # HAREKET ETTİ: Sayacı sıfırla ve durumu güncelle
                        motion_status = "HAREKET EDİYOR"
                        new_stationary_counters[tracker_id] = 0
                    else:
                        # HAREKET ETMEDİ (Eşiğin altında): Sayacı artır
                        current_counter += 1
                        new_stationary_counters[tracker_id] = current_counter

                        if current_counter >= self.stationary_frames_limit:
                            # Sabit kalma limitine ulaşıldı
                            motion_status = "DURUYOR"
                        else:
                            # Limit henüz aşılmadı, önceki durumu koru (bu sayacın ne zaman sıfırlandığına bağlı)
                            # Basitlik için, limit aşılana kadar "BİLİNMİYOR" veya "HAREKET EDİYOR" (önceki durum ne ise) diyebiliriz.
                            # Ancak burada amacımız nihai durumu belirlemek:
                            motion_status = "YAVAŞ HAREKET/GÖZLENİYOR"  # Veya Sadece "HAREKET EDİYOR" olarak bırakıp, sadece limit aşılınca DURUYOR de.
                            # En basit çözüm: Limit aşılana kadar "HAREKET EDİYOR" say.
                            motion_status = "HAREKET EDİYOR"

                else:
                    # Yeni algılama veya bootstrap kaybı: Başlangıçta hareket ediyor say
                    motion_status = "HAREKET EDİYOR"
                    new_stationary_counters[tracker_id] = 0

            # Algılama verisine hareket durumunu ekle
            detection["motionStatus"] = motion_status
            processed_detections.append(detection)

        # Bootstrap verisini güncelle
        self.bootstrap["previous_centers"] = current_centers
        self.bootstrap["stationary_counters"] = new_stationary_counters

        return processed_detections

    def run(self):
        # 1. Algılamaları işleyip hareket durumunu ekle ve durumu güncelle
        processed_detections = self.process_detections(self.detections)

        # 2. KRİTİK ADIM: İşlenmiş veriyi context objesine atama
        self.motion_detections = processed_detections

        # 3. Özel build_response_detect fonksiyonunu kullanarak paket modelini oluştur
        packageModel = build_response(context=self)

        # 4. Güncellenmiş bootstrap verisini çıktı paketine ekle
        packageModel["bootstrap"] = self.bootstrap

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()