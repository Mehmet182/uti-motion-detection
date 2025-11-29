
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


class ConfigMotionThreshold(Config):
    name: Literal["configMotionThreshold"] = "configMotionThreshold"
    value: int = Field(ge=0, le=100 , default=20)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Motion Threshold"

class ConfigStationaryFrames(Config):
    name: Literal["configStationaryFrames"] = "configStationaryFrames"
    value: int = Field(ge=1, le=100,default=5)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Stationary Frames"

class MotionDetectionInputs(Inputs):
    inputDetection: InputDetections


class MotionDetectionConfigs(Configs):
    configMotionThreshold:ConfigMotionThreshold
    configStationaryFrames:ConfigStationaryFrames


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


class MotionDetectionExecutor(Config):
    name: Literal["MotionDetectionExecutor"] = "MotionDetectionExecutor"
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
    value: Union[MotionDetectionExecutor]
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
