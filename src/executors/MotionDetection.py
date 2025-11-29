import sys
import os
import math
from typing import List, Dict, Any

# SDK Yolları
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

# SDK Importları
from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from sdks.novavision.src.base.logger import LoggerManager
from components.MotionDetection.src.utils.response import build_response
from components.MotionDetection.src.models.PackageModel import PackageModel

# --- MEMORY IMPORT ---
try:
    from components.MotionDetection.src.classes.memory import Memory
except ImportError:
    import src.classes.memory as Memory


class MotionDetection(Component):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.logger = LoggerManager()
        self.request.model = PackageModel(**(self.request.data))
        self.detections = self.request.get_param("inputDetections")

        self.motion_threshold = float(self.request.get_param("ConfigMotionThreshold") or 20.0)
        self.stationary_frames_limit = int(self.request.get_param("ConfigStationaryFrames") or 5)

        current_state = Memory.get_state()
        self.previous_centers = current_state.get("previous_centers", {})
        self.stationary_counters = current_state.get("stationary_counters", {})

        self.stats = {"moving": 0, "stationary": 0, "calculating": 0, "total": 0}

    @staticmethod
    def bootstrap(config: dict) -> dict:
        return {}

    def calculate_center(self, bbox: Dict[str, float]) -> list:
        center_x = bbox["left"] + bbox["width"] / 2
        center_y = bbox["top"] + bbox["height"] / 2
        return [round(center_x, 2), round(center_y, 2)]

    def process_detections(self) -> List[Dict[str, Any]]:

        if not self.detections:
            if len(self.previous_centers) > 0:
                self.logger.info("👀 Görüntüde kimse yok. Hafıza temizleniyor.")
                Memory.reset_state()
            self.previous_centers = {}
            self.stationary_counters = {}
            return []

        next_centers = {}
        next_counters = {}
        processed_detections = []

        # İstatistik sayaçları
        c_mov = 0
        c_stat = 0
        c_calc = 0

        self.logger.info(f"--- 🏁 FRAME BAŞLIYOR (Eşik: {self.motion_threshold}px) ---")

        for detection in self.detections:
            bbox = detection.get("boundingBox")
            tracker_id = detection.get("trackerID")

            if tracker_id is not None:
                tracker_id = str(tracker_id)

            motion_status = "HESAPLANIYOR"  # Varsayılan durumu nötr yapıyoruz
            debug_msg = ""

            if bbox and tracker_id:
                current_center = self.calculate_center(bbox)
                next_centers[tracker_id] = current_center

                prev_center = self.previous_centers.get(tracker_id)
                current_counter = self.stationary_counters.get(tracker_id, 0)

                if prev_center:
                    # Mesafe Hesabı
                    distance = math.sqrt(
                        (current_center[0] - prev_center[0]) ** 2 +
                        (current_center[1] - prev_center[1]) ** 2
                    )
                    distance = round(distance, 2)

                    if distance > self.motion_threshold:
                        # --- DURUM 1: NET HAREKET ---
                        motion_status = "HAREKET EDİYOR"
                        next_counters[tracker_id] = 0
                        c_mov += 1
                        debug_msg = f"🏃 HAREKETLİ | Fark: {distance}px"
                    else:
                        # --- DURUM 2: HAREKETSİZLİK VEYA AZ HAREKET ---
                        current_counter += 1
                        next_counters[tracker_id] = current_counter

                        if current_counter >= self.stationary_frames_limit:
                            # Limit doldu, artık kesinlikle duruyor diyebiliriz
                            motion_status = "DURUYOR"
                            c_stat += 1
                            debug_msg = f"🛑 DURUYOR   | Sayac: {current_counter}"
                        else:
                            # Limit dolmadı, hala analiz ediyoruz.
                            # ESKİ KOD: buraya "HAREKET EDİYOR" diyordu (Hata buydu).
                            # YENİ KOD: "HESAPLANIYOR" diyoruz.
                            motion_status = "HESAPLANIYOR"
                            c_calc += 1
                            debug_msg = f"⏳ ANALİZ    | Sayac: {current_counter}/{self.stationary_frames_limit}"

                    self.logger.info(f"   🆔 ID:{tracker_id} | Fark: {distance}px | Durum: {motion_status}")

                else:
                    # --- DURUM 3: YENİ GİRİŞ ---
                    # ESKİ KOD: "HAREKET EDİYOR" diyordu.
                    # YENİ KOD: "HESAPLANIYOR" diyoruz. İlk karede yargılamıyoruz.
                    motion_status = "HESAPLANIYOR"
                    next_counters[tracker_id] = 0
                    c_calc += 1
                    self.logger.info(f"   🆕 ID:{tracker_id} | Yeni Nesne | Durum: HESAPLANIYOR")

            detection["motionStatus"] = motion_status
            processed_detections.append(detection)

        # İstatistikler
        self.stats = {"moving": c_mov, "stationary": c_stat, "calculating": c_calc, "total": len(processed_detections)}

        # Güncelleme
        self.previous_centers = next_centers
        self.stationary_counters = next_counters

        return processed_detections

    def run(self):
        processed_result = self.process_detections()
        self.motion_detections = processed_result
        packageModel = build_response(context=self)

        Memory.update_state(self.previous_centers, self.stationary_counters)
        packageModel.bootstrap = {}

        if self.stats["total"] > 0:
            self.logger.info(
                f"📊 ÖZET: Toplam: {self.stats['total']} | "
                f"🏃 Hareketli: {self.stats['moving']} | "
                f"🛑 Duran: {self.stats['stationary']} | "
                f"⏳ Hesaplanan: {self.stats['calculating']}"
            )

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()