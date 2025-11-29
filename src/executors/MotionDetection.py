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
        self.motion_threshold = self.request.get_param("configMotionThreshold")
        print(f"Motion Detection Threshold: {self.motion_threshold}")
        self.stationary_frames_limit = self.request.get_param("configStationaryFrames")
        print(f"Motion Detection Stationary Frames Limit: {self.stationary_frames_limit}")

        self.previous_centers = self.bootstrap.get("previous_centers", {})
        print(f"Motion Detection Previous Centers: {self.previous_centers}")
        self.stationary_counters = self.bootstrap.get("stationary_counters", {})
        print(f"Motion Detection Stationary Counters: {self.stationary_counters}")

    @staticmethod
    def bootstrap(config: dict) -> dict:
        """Başlangıç durumu."""
        return {
            "previous_centers": {},
            "stationary_counters": {}
        }

    def calculate_center(self, bbox: Dict[str, float]) -> tuple:
        """Merkez hesaplama."""
        center_x = bbox["left"] + bbox["width"] / 2
        center_y = bbox["top"] + bbox["height"] / 2
        return (center_x, center_y)

    # BU FONKSIYON SINIFIN İÇİNDE OLMALI (GİRİNTİYE DİKKAT)
    def process_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Algılamaları işler."""
        if not detections:
            self.previous_centers = {}
            self.stationary_counters = {}
            return []

        next_centers = {}
        next_counters = {}
        processed_detections = []

        for detection in detections:
            bbox = detection.get("boundingBox")
            tracker_id = detection.get("trackerID")

            if tracker_id is not None:
                tracker_id = str(tracker_id)

            motion_status = "BİLİNMİYOR"

            if bbox and tracker_id:
                current_center = self.calculate_center(bbox)

                # Gelecek kare için kaydet
                next_centers[tracker_id] = current_center

                # Önceki verileri al
                prev_center = self.previous_centers.get(tracker_id)
                current_counter = self.stationary_counters.get(tracker_id, 0)

                if prev_center:
                    prev_x, prev_y = prev_center if isinstance(prev_center, (list, tuple)) else (0, 0)

                    distance = math.sqrt(
                        (current_center[0] - prev_x) ** 2 +
                        (current_center[1] - prev_y) ** 2
                    )

                    if distance > float(self.motion_threshold):
                        motion_status = "HAREKET EDİYOR"
                        next_counters[tracker_id] = 0
                    else:
                        current_counter += 1
                        next_counters[tracker_id] = current_counter

                        if current_counter >= int(self.stationary_frames_limit):
                            motion_status = "DURUYOR"
                        else:
                            motion_status = "HAREKET EDİYOR"
                else:
                    motion_status = "HAREKET EDİYOR"
                    next_counters[tracker_id] = 0

            detection["motionStatus"] = motion_status
            processed_detections.append(detection)

        # Durumu güncelle
        self.previous_centers = next_centers
        self.stationary_counters = next_counters

        return processed_detections

    def run(self):
        # 1. İşlem
        # Hata burada alınıyordu, çünkü yukarıdaki fonksiyon bulunamıyordu.
        print(f"Hafızadaki Takip Sayısı: {len(self.previous_centers)}")
        processed_detections = self.process_detections(self.detections)

        # 2. Atama
        self.motion_detections = processed_detections
        print(f"Processed Motion Detections: {self.motion_detections}")

        # 3. Yanıt Oluşturma
        packageModel = build_response(context=self)

        # 4. Bootstrap (Serialization hatasını önleyen düzeltme)
        packageModel.bootstrap = {
            "previous_centers": self.previous_centers,
            "stationary_counters": self.stationary_counters
        }

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()