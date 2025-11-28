import sys
import os
import math


sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from components.MotionDetection.src.utils.response import build_response
from components.MotionDetection.src.models.PackageModel import PackageModel


class MotionDetector(Component):

    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data))
        print("Initialized Motion Detection Executor")
        print(f"self.request.model: {self.request.model}")



        self.detections= self.request.get_param("inputDetections")
        print(f"Motion Detection Input Detections: {self.detections}")
        self.motion_threshold = self.request.get_param("ConfigMotionThreshold")
        print(f"Motion Detection Threshold: {self.motion_threshold}")
        self.stationary_frames_limit = self.request.get_param("ConfigStationaryFrames")
        print(f"Motion Detection Stationary Frames Limit: {self.stationary_frames_limit}")

    @staticmethod
    def bootstrap(config: dict) -> dict:

        return {}

    def run(self):

        self.motion_detections =  self.detections

        packageModel = build_response(context=self)

        return packageModel


if "__main__" == __name__:
    Executor(sys.argv[1]).run()