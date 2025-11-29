import sys
import os
import math
from typing import List, Dict, Any, Union

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from components.MotionDetection.src.utils.response import build_response
from components.MotionDetection.src.models.PackageModel import PackageModel


class MotionDetection(Component):

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data))
        print("Initialized Motion Detection Executor")

        self.detections= self.request.get_param("inputDetections")
        print(f"Motion Detection Input Detections: {self.detections}")
        self.motion_threshold = self.request.get_param("ConfigMotionThreshold")
        print(f"Motion Detection Threshold: {self.motion_threshold}")
        self.stationary_frames_limit = self.request.get_param("ConfigStationaryFrames")
        print(f"Motion Detection Stationary Frames Limit: {self.stationary_frames_limit}")

    @staticmethod
    def bootstrap(config: dict) -> dict:
        """Kareler arasında durumu korumak için başlangıç durumunu döndürür."""
        return {
            "previous_centers": {},
            "stationary_counters": {}
        }

    def calculate_center(self, bbox: Dict[str, float]) -> tuple:
        """Sınır kutusunun merkez koordinatlarını (x, y) hesaplar."""
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

        current_centers: Dict[Union[int, str], tuple] = {}
        new_stationary_counters: Dict[Union[int, str], int] = {}
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

                # Hareket tespiti sadece önceki karede de mevcutsa yapılır
                if prev_center is not None:
                    # Öklid mesafesi hesaplama
                    distance = math.sqrt(
                        (current_center[0] - prev_center[0]) ** 2 +
                        (current_center[1] - prev_center[1]) ** 2
                    )

                    if distance > self.motion_threshold:
                        # HAREKET ETTİ: Eşik aşıldı
                        motion_status = "HAREKET EDİYOR"
                        new_stationary_counters[tracker_id] = 0  # Sayacı sıfırla
                    else:
                        # HAREKET ETMEDİ (Eşiğin altında): Sabit kalma sayacını artır
                        current_counter += 1
                        new_stationary_counters[tracker_id] = current_counter

                        if current_counter >= self.stationary_frames_limit:
                            # Sabit kalma limitine ulaşıldı
                            motion_status = "DURUYOR"
                        else:
                            # Limit aşılmadı, teknik olarak hareket etmiyor ama limit aşılmadığı için
                            # genellikle akışın devam ettiğini belirtmek için "HAREKET EDİYOR" denir.
                            motion_status = "HAREKET EDİYOR"

                else:
                    # Yeni algılama: Başlangıçta hareket ediyor say (İlk karesi)
                    motion_status = "HAREKET EDİYOR"
                    new_stationary_counters[tracker_id] = 0

            # Algılama verisine hareket durumunu ekle
            detection["motionStatus"] = motion_status
            processed_detections.append(detection)

        # Bootstrap verisini güncelle (bir sonraki kare için durumu kaydet)
        self.bootstrap["previous_centers"] = current_centers
        self.bootstrap["stationary_counters"] = new_stationary_counters

        return processed_detections

    def run(self):
        # 1. Algılamaları işle ve motionStatus alanını ekle
        processed_detections = self.process_detections(self.detections)

        # 2. KRİTİK ADIM: İşlenmiş veriyi context objesinin beklenen çıktı alanına atama
        # build_response, context.motion_detections'tan çekecek.
        self.motion_detections = processed_detections

        # 3. Özel build_response fonksiyonunu kullanarak nihai paket modelini oluştur
        packageModel = build_response(context=self)

        # 4. Güncellenmiş bootstrap verisini çıktı paketine ekle
        # Bu, durumun bir sonraki frame'e aktarılmasını sağlar.
        packageModel["bootstrap"] = self.bootstrap

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()
