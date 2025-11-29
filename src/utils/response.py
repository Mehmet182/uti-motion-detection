
from sdks.novavision.src.helper.package import PackageHelper
from components.MotionDetection.src.models.PackageModel import PackageModel, PackageConfigs, ConfigExecutor, MotionDetectionOutputs, MotionDetectionResponse, MotionDetectionExecutor, OutputDetections


def build_response(context):
    outputDetections = OutputDetections(value=context.motion_detections)
    motionDetectionOutputs = MotionDetectionOutputs(outputDetections=outputDetections)
    motionDetectionResponse = MotionDetectionResponse(outputs=motionDetectionOutputs)
    motionDetectionExecutor = MotionDetectionExecutor(value=motionDetectionResponse)
    executor = ConfigExecutor(value=motionDetectionExecutor)
    packageConfigs = PackageConfigs(executor=executor)
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    return packageModel