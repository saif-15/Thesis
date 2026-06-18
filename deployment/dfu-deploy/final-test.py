import boto3
import json

# Initialize a boto3 client for Lambda
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Define the payload to send to Lambda
payload = {
    "body" : {
    "session_id": "user-001",
    "img_key": "",
    "user_prompt": "what is the severity ? what are the causes?"
    }
}

# Call the Lambda function directly
response = lambda_client.invoke(
    FunctionName='dfu-proxy-api',  # Replace with your Lambda function name
    InvocationType='RequestResponse',  # For synchronous invocation
    Payload=json.dumps(payload)  # Convert the dictionary to JSON string
)

# Read the response from the Lambda function
response_payload = json.loads(response['Payload'].read().decode('utf-8'))

# Print the response from Lambda
print(response_payload)