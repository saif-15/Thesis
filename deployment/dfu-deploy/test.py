import boto3
import json

runtime = boto3.client("sagemaker-runtime")

response = runtime.invoke_endpoint(
    EndpointName="dfu-classification-endpoint",
    ContentType="application/json",
    Body=json.dumps({
        "bucket": "dfu-support-images-bkt",
        "img_key": "Testing/test.jpg"
    })
)

print(response["Body"].read().decode())