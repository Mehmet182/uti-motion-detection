
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

class ConfigStationaryFrames(Config):
    """
    Bir nesnenin "DURUYOR" olarak işaretlenmesi için kaç kare boyunca hareketsiz kalması gerektiğini belirler.
    Düşük değer: Hızlı karar verir (yanılma payı artar). Yüksek değer: Emin olmadan duruyor demez.
    """
    name: Literal["configStationaryFrames"] = "configStationaryFrames"
    value: int = Field(ge=1, le=100, default=5)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Stationary Frames Limit"


class ConfigPosMoveThreshold(Config):
    """
    Bir nesnenin hareket ediyor sayılması için bir önceki kareden kaç piksel uzağa gitmesi gerektiğini belirler.
    Görüntü titremelerini hareket sanmamak için kullanılır.
    """
    name: Literal["configPosMoveThreshold"] = "configPosMoveThreshold"
    value: float = Field(ge=0.0, le=500.0, default=10.0)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Movement Threshold (px)"


class ConfigSizeChangeSensitivity(Config):
    """
    Nesnenin boyutundaki (genişlik/yükseklik) değişimi algılama hassasiyeti (0.0 - 1.0).
    0.05 değeri %5'lik bir büyümeyi/küçülmeyi "ŞEKİL DEĞİŞİMİ" olarak algılar.
    """
    name: Literal["configSizeChangeSensitivity"] = "configSizeChangeSensitivity"
    value: float = Field(ge=0.01, le=1.0, default=0.05)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"

    class Config:
        title = "Size Change Sensitivity"



class MotionDetectionInputs(Inputs):
    inputDetections: InputDetections


class MotionDetectionConfigs(Configs):
    configPosMoveThreshold:ConfigPosMoveThreshold
    configSizeChangeSensitivity:ConfigSizeChangeSensitivity
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
