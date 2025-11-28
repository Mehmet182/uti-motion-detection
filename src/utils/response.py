
from sdks.novavision.src.helper.package import PackageHelper
from components.Package.src.models.PackageModel import PackageModel, PackageConfigs, ConfigExecutor, MotionOutputs, MotionResponse, MotionExecutor, OutputImage


def build_response(context):
    OotputDetections = OutputDetections(value=context.motion_detections)
    Outputs = MotionOutputs(OotputDetections=OotputDetections)
    motionResponse = MotionResponse(outputs=Outputs)
    motionExecutor = MotionExecutor(value=motionResponse)
    executor = ConfigExecutor(value=motionExecutor)
    packageConfigs = PackageConfigs(executor=executor)
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    return packageModel