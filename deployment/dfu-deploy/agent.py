import boto3

client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

agent_id = '######'
agent_alias_id = '######'
session_id = "######"

input_text = """
Assess the uploaded DFU image.
bucket: dfu-support-images-bkt
img_key: 
user_prompt: what is tghe most important thing should i do
"""

response = client.invoke_agent(
    agentId=agent_id,
    agentAliasId=agent_alias_id,
    sessionId=session_id,
    inputText=input_text
)

completion = ""
for event in response["completion"]:
    if "chunk" in event:
        completion += event["chunk"]["bytes"].decode("utf-8")

print(completion)