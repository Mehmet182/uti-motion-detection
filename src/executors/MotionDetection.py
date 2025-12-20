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
from components.MotionDetection.src.classes.memory import Memory



class MotionDetection(Component):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)

        self.logger = LoggerManager()
        self.request.model = PackageModel(**(self.request.data))
        self.detections = self.request.get_param("inputDetections")
        self.motion_threshold =self.request.get_param("ConfigPosMoveThreshold")
        self.stationary_frames_limit = self.request.get_param("ConfigStationaryFrames")
        self.size_sensitivity = self.request.get_param("ConfigSizeChangeSensitivity")
        self.history_state = Memory.get_state().get("history_state", {})
        self.stats = {"moving": 0, "stationary": 0, "calculating": 0, "shape_change": 0, "total": 0}

    @staticmethod
    def bootstrap(config: dict) -> dict:
        return {}

    def calculate_center(self, bbox: Dict[str, float]) -> list:
        center_x = bbox["left"] + bbox["width"] / 2
        center_y = bbox["top"] + bbox["height"] / 2
        return [round(center_x, 2), round(center_y, 2)]

    def process_detections(self) -> List[Dict[str, Any]]:
        if not self.detections:
            # Kimse yoksa hafızayı temizle (Opsiyonel, ID çakışmasını önler)
            if len(self.history_state) > 0:
                self.logger.info("👀 Görüntüde kimse yok. Hafıza temizleniyor.")
                Memory.reset_state()
            return []

        next_state = {}
        processed_detections = []

        # İstatistik sayaçları
        c_mov = 0
        c_stat = 0
        c_calc = 0
        c_shape = 0

        # self.logger.info(f"--- 🏁 ANALİZ BAŞLIYOR (Eşik: {self.motion_threshold}px) ---")

        for detection in self.detections:
            bbox = detection.get("boundingBox")
            tracker_id = str(detection.get("trackerID")) if detection.get("trackerID") is not None else None

            # Varsayılan değerler
            motion_status = "HESAPLANIYOR"
            detail_msg = "Veri Toplanıyor"

            if bbox and tracker_id:
                # Şu anki veriler
                current_center = self.calculate_center(bbox)
                current_w = bbox["width"]
                current_h = bbox["height"]

                # Geçmiş verisi var mı?
                prev_data = self.history_state.get(tracker_id)

                if prev_data:
                    prev_center = prev_data["center"]
                    prev_w = prev_data["dims"][0]
                    prev_h = prev_data["dims"][1]
                    stationary_counter = prev_data["counter"]

                    # 1. Mesafe Hesabı (Yürüme)
                    distance = math.sqrt(
                        (current_center[0] - prev_center[0]) ** 2 +
                        (current_center[1] - prev_center[1]) ** 2
                    )

                    # 2. Boyut Değişimi Hesabı (Eğilme/Kalkma)
                    diff_w = abs(current_w - prev_w) / prev_w if prev_w > 0 else 0
                    diff_h = abs(current_h - prev_h) / prev_h if prev_h > 0 else 0
                    is_size_changed = (diff_w > self.size_sensitivity) or (diff_h > self.size_sensitivity)

                    # --- KARAR MANTIĞI ---

                    if distance > self.motion_threshold:
                        # HAREKET: Konum değişti
                        motion_status = "HAREKETLİ"
                        detail_msg = f"Hız: {int(distance)}px"
                        stationary_counter = 0  # Hareket ettiği an sayacı sıfırla
                        c_mov += 1

                    elif is_size_changed:
                        # ŞEKİL DEĞİŞİMİ: Konum sabit ama boyut değişti
                        motion_status = "ŞEKİL DEĞİŞTİRİYOR"
                        detail_msg = f"Değişim: %{int(max(diff_w, diff_h) * 100)}"
                        stationary_counter = 0  # Şekil değiştirirken de hareketli sayılır
                        c_shape += 1

                    else:
                        # DURMA EĞİLİMİ: Hareket yok, boyut değişimi yok
                        stationary_counter += 1

                        if stationary_counter >= self.stationary_frames_limit:
                            motion_status = "DURUYOR"
                            detail_msg = f"Süre: {stationary_counter} kare"
                            c_stat += 1
                        else:
                            motion_status = "HESAPLANIYOR"
                            detail_msg = f"Analiz: {stationary_counter}/{self.stationary_frames_limit}"
                            c_calc += 1

                    # Bir sonraki kare için veriyi hazırla
                    next_state[tracker_id] = {
                        "center": current_center,
                        "dims": [current_w, current_h],
                        "counter": stationary_counter
                    }

                else:
                    # YENİ NESNE (İlk defa görüldü)
                    motion_status = "HESAPLANIYOR"
                    detail_msg = "Yeni Giriş"
                    c_calc += 1

                    next_state[tracker_id] = {
                        "center": current_center,
                        "dims": [current_w, current_h],
                        "counter": 0
                    }

            detection["motionStatus"] = motion_status
            detection["motionDetail"] = detail_msg
            processed_detections.append(detection)

        # İstatistikler
        self.stats = {
            "moving": c_mov,
            "stationary": c_stat,
            "calculating": c_calc,
            "shape_change": c_shape,
            "total": len(processed_detections)
        }

        # Güncel state'i kaydet (Sadece ekranda olanları tutar, çıkanlar silinir)
        self.history_state = next_state

        return processed_detections

    def run(self):
        processed_result = self.process_detections()
        self.motion_detections = processed_result
        packageModel = build_response(context=self)

        # Memory güncelle
        Memory.update_state({"history_state": self.history_state})
        packageModel.bootstrap = {}

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()