
from pydantic import Field
from typing import List, Optional, Union, Literal
from sdks.novavision.src.base.model import Detection,Package, Inputs, Configs, Outputs, Response, Request, Output, Input, Config


class InputDetections(Input):
    name: Literal["inputDetections"] = "inputDetections"
    value: List
    type: Literal["list"] = "list"

    class Config:
        title = "Detections"

class Detection(Detection):
    imgUID: Optional[str] = None
    trackerID: Optional[Union[List, int]] = None
    UUID: Optional[str] = ""
    source: Optional[str] = ""
    motionStatus: Optional[str] = None # Sizin eklediğiniz alan

class OutputDetections(Output):
    name: Literal["outputDetections"] = "outputDetections"
    value: list[Detection]
    type: Literal["list"] = "list"

    class Config:
        title = "Detections"

# Not: Base 'Config' sınıfının projenizde zaten tanımlı olduğu varsayılmıştır.

class ConfigHistoryFrameCount(Config):
    """
    Determines how many frames back the current frame is compared against.
    Higher values (e.g., 15) detect slower movements but increase lag; lower values (e.g., 2) detect only fast movements.
    """
    name: Literal["configHistoryFrameCount"] = "configHistoryFrameCount"
    value: int = Field(ge=2, le=50, default=10)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "History Frame Count"


class ConfigSizeChangeSensitivity(Config):
    """
    Sensitivity threshold (0.0 - 1.0) for detecting changes in the object's width or height (e.g., sitting down, standing up).
    0.05 means a 5% change triggers detection.
    """
    name: Literal["configSizeChangeSensitivity"] = "configSizeChangeSensitivity"
    value: float = Field(ge=0.01, le=1.0, default=0.05)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Size Change Sensitivity"


class ConfigInternalMotionSensitivity(Config):
    """
    Sensitivity threshold (0.0 - 1.0) for detecting pixel-level changes inside the object's bounding box (e.g., waving hands while standing still).
    """
    name: Literal["configInternalMotionSensitivity"] = "configInternalMotionSensitivity"
    value: float = Field(ge=0.01, le=1.0, default=0.03)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Internal Motion Sensitivity"


class ConfigPosMoveThreshold(Config):
    """
    The minimum distance (in pixels) the object's center must move to be classified as "WALKING".
    """
    name: Literal["configPosMoveThreshold"] = "configPosMoveThreshold"
    value: float = Field(ge=0.0, le=500.0, default=10.0)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Position Move Threshold (px)"


class ConfigResizedRoiSize(Config):
    """
    The resolution (N x N pixels) to which the object image is resized for internal analysis.
    Lower values correspond to higher performance but less detail.
    """
    name: Literal["configResizedRoiSize"] = "configResizedRoiSize"
    value: int = Field(ge=10, le=500, default=100)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Resized ROI Size"




class MotionDetectionInputs(Inputs):
    inputDetections: InputDetections


class MotionDetectionConfigs(Configs):
    configResizedRoiSize:ConfigResizedRoiSize
    configPosMoveThreshold:ConfigPosMoveThreshold
    configInternalMotionSensitivity:ConfigInternalMotionSensitivity
    configSizeChangeSensitivity:ConfigSizeChangeSensitivity
    configHistoryFrameCount:ConfigHistoryFrameCount

class MotionDetectionOutputs(Outputs):
    outputDetections: OutputDetections


class MotionDetectionRequest(Request):
    inputs: Optional[MotionDetectionInputs]
    configs: MotionDetectionConfigs

    class Config:
        json_schema_extra = {
            "target": "configs"
        }


class MotionDetectionResponse(Response):
    outputs: MotionDetectionOutputs


class MotionDetection(Config):
    name: Literal["MotionDetection"] = "MotionDetection"
    value: Union[MotionDetectionRequest, MotionDetectionResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"

    class Config:
        title = "Motion"
        json_schema_extra = {
            "target": {
                "value": 0
            }
        }


class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"
    value: Union[MotionDetection]
    type: Literal["executor"] = "executor"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"

    class Config:
        title = "Task"
        json_schema_extra = {
            "target": "value"
        }

class PackageConfigs(Configs):
    executor: ConfigExecutor


class PackageModel(Package):
    configs: PackageConfigs
    type: Literal["component"] = "component"
    name: Literal["MotionDetection"] = "MotionDetection"
