import sagemaker
from sagemaker.pytorch import PyTorchModel
import boto3

# Create a session
session = boto3.Session()

# Get the region
region = session.region_name

# Print the region
print(f"Current AWS Region:: {region}")

# Create a SageMaker session
sagemaker_session = sagemaker.Session()

# execution Role
role = "arn:aws:iam::########:role/service-role/AmazonSageMaker-ExecutionRole-20241127T222751"

model = PyTorchModel(
    entry_point="inference.py",
    source_dir="code/",
    role=role,
    framework_version="2.0",
    py_version="py310",
    model_data="s3:bucket-uri",
    env={
        "SUPPORT_BUCKET": "dfu-support-images-bkt",
        "SUPPORT_PREFIX": "Severity/"
    }
)

predictor = model.deploy(
    endpoint_name="dfu-classification-endpoint",
    instance_type="ml.m5.large",
    initial_instance_count=1
)

print("Endpoint deployed:", predictor.endpoint_name)
