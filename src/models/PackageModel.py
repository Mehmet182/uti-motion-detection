
from pydantic import Field, validator
from typing import List, Optional, Union, Literal
from sdks.novavision.src.base.model import Detection,Package, Image, Inputs, Configs, Outputs, Response, Request, Output, Input, Config


class InputDetections(Input):
    name: Literal["inputDetections"] = "inputDetections"
    value: List[Detection]
    type: str = "list"

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
    value: List[Detection]
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

class MotionInputs(Inputs):
    inputDetection: InputDetections


class MotionConfigs(Configs):
    configMotionThreshold:ConfigMotionThreshold
    configStationaryFrames:ConfigStationaryFrames


class MotionOutputs(Outputs):
    outputDetections: OutputDetections


class MotionRequest(Request):
    inputs: Optional[MotionInputs]
    configs: MotionConfigs

    class Config:
        json_schema_extra = {
            "target": "configs"
        }


class MotionResponse(Response):
    outputs: MotionOutputs


class MotionExecutor(Config):
    name: Literal["Motion"] = "Motion"
    value: Union[MotionRequest, MotionResponse]
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
    value: Union[MotionExecutor]
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
