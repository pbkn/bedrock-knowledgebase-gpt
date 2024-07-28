import boto3
import json
import logging
import os
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SOURCE_TYPE = "BEDROCK_KNOWLEDGEBASE"

modelArn = os.environ["BedrockModelNameArn"]
knowledgeBaseId = os.environ["KnowledgeBaseId"]
client = boto3.client("bedrock-agent-runtime")
# Initialize a Cognito Identity Provider client
cognito_client = boto3.client('cognito-idp')

def get_user_role(user_pool_id, user_id):

    try:
        # Get user details
        response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=user_id
        )

        # Extract custom:Role attribute
        for attribute in response['UserAttributes']:
            if attribute['Name'] == 'custom:Role':
                return attribute['Value']

        return "all"

    except cognito_client.exceptions.UserNotFoundException:
        return f"User with ID {user_id} not found in user pool {user_pool_id}."
        return None
    except Exception as e:
        return f"An error occurred: {str(e)}"

def retrieve_generate_knowledgebase(event):
    eventArgs = json.loads(event["body"])
    prompt = eventArgs["prompt"]
    user_id = eventArgs["userId"]
    role = get_user_role("us-east-1_8tfokqPKb", str(user_id))
    print(f"The role of the user is: {role}")
    sessionId = eventArgs["conversationId"] if "conversationId" in eventArgs else None

    bedrock_response = {}
    if sessionId:
        print(str(knowledgeBaseId), str(modelArn))
        input = {"text": prompt}
        bedrock_response = client.retrieve_and_generate(
            input={"text": prompt},
            sessionId=str(sessionId),
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": str(knowledgeBaseId),
                    "modelArn": str(modelArn),
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                           "numberOfResults": 5,
                           "overrideSearchType": "SEMANTIC",
                           "filter": {
                               "orAll": [
                                   {
                                        "equals": {
                                            "key": "role",
                                            "value": role
                                        }
                                   },
                                   {
                                       "equals": {
                                           "key": "role",
                                           "value": "all"
                                       }
                                   }
                               ]
                           }
                        }
                    }
                }
            }
        )
    else:
        bedrock_response = client.retrieve_and_generate(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": str(knowledgeBaseId),
                    "modelArn": str(modelArn),
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {
                           "numberOfResults": 5,
                           "overrideSearchType": "SEMANTIC",
                           "filter": {
                               "orAll": [
                                   {
                                        "equals": {
                                            "key": "role",
                                            "value": role
                                        }
                                   },
                                   {
                                       "equals": {
                                           "key": "role",
                                           "value": "all"
                                       }
                                   }
                               ]
                           }
                        }
                    }
                }
            }
        )

    timestamp = bedrock_response["ResponseMetadata"]["HTTPHeaders"]["date"]
    epochTimestampInt = int(
        time.mktime(time.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %Z"))
    )
    epochTimestamp = str(epochTimestampInt)

    response = {}
    response["type"] = SOURCE_TYPE
    response["conversationId"] = bedrock_response["sessionId"]
    response["systemMessageId"] = bedrock_response["sessionId"]
    response["systemMessage"] = bedrock_response["output"]["text"]
    response["epochTimeStamp"] = epochTimestamp
    response["sourceAttributions"] = bedrock_response["citations"]

    restApiResponse = json.dumps(response)
    return restApiResponse


def handler(event, context):
    try:
        logger.info(f"received event: {event}")
        response = retrieve_generate_knowledgebase(event)
        logger.info(response)
        return {
            "statusCode": 200,
            "body": response,
            "headers": {
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
        }
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": str(e)}),
            "headers": {
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            },
        }
