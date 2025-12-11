import sys
import os
import math
import cv2
import numpy as np
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

        # --- CONFIG PARAMETRELERİ ---
        # Eğer config gelmezse varsayılan değerleri kullanır
        self.history_frame_count = self.request.get_param("ConfigHistoryFrameCount")
        self.size_sensitivity =self.request.get_param("ConfigSizeChangeSensitivity")
        self.internal_sensitivity = self.request.get_param("ConfigInternalMotionSensitivity")
        self.pos_move_threshold = self.request.get_param("ConfigPosMoveThreshold")
        self.roi_resize_dim = self.request.get_param("ConfigResizedRoiSize")

        # Hafızayı Çek
        current_state = Memory.get_state()
        # track_history yapısı: { "tracker_id": [ {"roi": np.array, "bbox": [cx, cy, w, h]}, ... ] }
        self.track_history = current_state.get("track_history", {})

        self.stats = {"walking": 0, "shape_change": 0, "internal_motion": 0, "stationary": 0, "analyzing": 0}

    @staticmethod
    def bootstrap(config: dict) -> dict:
        return {}

    def get_frame_image(self):
        """
        Request içindeki görüntüyü OpenCV formatına (numpy array) çevirir.
        SDK yapınıza göre burayı düzenlemeniz gerekebilir.
        """
        try:
            # ÖRNEK SENARYO: Görüntü self.request.image içerisinde numpy array olarak geliyorsa:
            if hasattr(self.request, 'image') and self.request.image is not None:
                return self.request.image

            # ÖRNEK SENARYO 2: self.request.frame varsa
            if hasattr(self.request, 'frame') and self.request.frame is not None:
                return self.request.frame

            # Eğer görüntü yoksa None döner (Sadece koordinat analizi yapılır)
            return None
        except Exception as e:
            self.logger.error(f"Görüntü alınırken hata: {e}")
            return None

    def preprocess_roi(self, frame, bbox):
        """ROI'yi kesip, gri yapıp, standart boyuta getirir."""
        if frame is None:
            return None

        x, y, w, h = int(bbox["left"]), int(bbox["top"]), int(bbox["width"]), int(bbox["height"])

        # Sınır kontrolleri
        img_h, img_w = frame.shape[:2]
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(img_w, x + w), min(img_h, y + h)

        if x2 <= x1 or y2 <= y1:
            return None

        roi = frame[y1:y2, x1:x2]

        try:
            roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # Gürültü azaltma
            roi_gray = cv2.GaussianBlur(roi_gray, (21, 21), 0)
            roi_resized = cv2.resize(roi_gray, (self.roi_resize_dim, self.roi_resize_dim))
            return roi_resized
        except Exception as e:
            # ROI çok küçükse hata verebilir
            return None

    def process_detections(self) -> List[Dict[str, Any]]:
        if not self.detections:
            if len(self.track_history) > 0:
                self.logger.info("👀 Görüntüde kimse yok. Hafıza temizleniyor.")
                Memory.reset_state()
            return []

        frame = self.get_frame_image()
        if frame is None:
            self.logger.warning(
                "⚠️ Frame görüntüsü alınamadı! Sadece koordinat analizi yapılabilir (Pixel analizi devre dışı).")

        current_ids = []
        processed_detections = []

        # İstatistikler
        c_walk = 0
        c_shape = 0
        c_internal = 0
        c_stat = 0
        c_analysing = 0

        for detection in self.detections:
            bbox = detection.get("boundingBox")
            tracker_id = str(detection.get("trackerID")) if detection.get("trackerID") is not None else None

            if not tracker_id or not bbox:
                processed_detections.append(detection)
                continue

            current_ids.append(tracker_id)

            # --- VERİ HAZIRLIĞI ---
            cx = bbox["left"] + bbox["width"] / 2
            cy = bbox["top"] + bbox["height"] / 2
            w = bbox["width"]
            h = bbox["height"]

            # ROI İşleme (Frame varsa)
            current_roi = self.preprocess_roi(frame, bbox)

            current_data = {
                "bbox": [cx, cy, w, h],
                "roi": current_roi  # Frame yoksa None olur
            }

            # Geçmişi Yükle veya Oluştur
            if tracker_id not in self.track_history:
                self.track_history[tracker_id] = []

            history_list = self.track_history[tracker_id]
            history_list.append(current_data)

            # Geçmiş listesi boyutunu koru
            if len(history_list) > self.history_frame_count:
                history_list.pop(0)  # En eskiyi sil

            # --- ANALİZ MANTIĞI ---
            motion_status = "ANALİZ EDİLİYOR"
            detail_msg = f"Veri Toplanıyor ({len(history_list)}/{self.history_frame_count})"
            motion_type = "analyzing"

            # Yeterli geçmiş varsa kıyasla
            if len(history_list) == self.history_frame_count:
                old_data = history_list[0]
                old_bbox = old_data["bbox"]
                old_roi = old_data["roi"]

                old_cx, old_cy, old_w, old_h = old_bbox

                # 1. Mesafe Farkı (Yürüme)
                dist = math.sqrt((cx - old_cx) ** 2 + (cy - old_cy) ** 2)

                # 2. Boyut Farkı (Şekil Değiştirme)
                diff_w = abs(w - old_w) / old_w if old_w > 0 else 0
                diff_h = abs(h - old_h) / old_h if old_h > 0 else 0

                # 3. İç Piksel Farkı (İç Hareket) - Sadece ROI varsa
                pixel_change_ratio = 0.0
                if current_roi is not None and old_roi is not None:
                    try:
                        pixel_diff = cv2.absdiff(current_roi, old_roi)
                        _, pixel_thresh = cv2.threshold(pixel_diff, 20, 255, cv2.THRESH_BINARY)
                        pixel_change_ratio = np.count_nonzero(pixel_thresh) / pixel_thresh.size
                    except:
                        pixel_change_ratio = 0.0

                # --- KARAR AĞACI ---
                if dist > self.pos_move_threshold:
                    motion_status = "YÜRÜYOR / İERLİYOR"
                    detail_msg = f"Mesafe: {int(dist)}px"
                    motion_type = "walking"
                    c_walk += 1

                elif diff_w > self.size_sensitivity or diff_h > self.size_sensitivity:
                    motion_status = "ŞEKİL DEĞİŞTİRİYOR"
                    detail_msg = f"Boyut: %{int(max(diff_w, diff_h) * 100)}"
                    motion_type = "shape_change"
                    c_shape += 1

                elif pixel_change_ratio > self.internal_sensitivity:
                    motion_status = "DURDUĞU YERDE HAREKETLİ"
                    detail_msg = f"Yoğunluk: %{int(pixel_change_ratio * 100)}"
                    motion_type = "internal_motion"
                    c_internal += 1

                else:
                    motion_status = "SABİT / DURUYOR"
                    detail_msg = "Hareket Algılanmadı"
                    motion_type = "stationary"
                    c_stat += 1
            else:
                c_analysing += 1

            # Loglama
            # self.logger.info(f"ID:{tracker_id} | {motion_status} | {detail_msg}")

            # Sonuçları detection objesine ekle
            detection["motionStatus"] = motion_status
            detection["motionDetail"] = detail_msg
            detection["motionType"] = motion_type
            processed_detections.append(detection)

        # Temizlik: Ekranda olmayan ID'leri hafızadan sil
        keys_to_remove = [k for k in self.track_history if k not in current_ids]
        for k in keys_to_remove:
            del self.track_history[k]

        self.stats = {
            "walking": c_walk,
            "shape_change": c_shape,
            "internal_motion": c_internal,
            "stationary": c_stat,
            "analyzing": c_analysing
        }

        return processed_detections

    def run(self):
        processed_result = self.process_detections()
        self.motion_detections = processed_result
        packageModel = build_response(context=self)

        # Memory güncelle
        Memory.update_state({"track_history": self.track_history})
        packageModel.bootstrap = {}

        self.logger.info(
            f"📊 ÖZET: 🚶 {self.stats['walking']} | 📐 {self.stats['shape_change']} | 👋 {self.stats['internal_motion']} | 🛑 {self.stats['stationary']}")

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()