# Download NPM dependencies
npm install 

# Init Amplify app
amplify init --providers "{\"awscloudformation\":"{\"configLevel\":\"project\"\,\"useProfile\":true\,\"profileName\":\"amplify-admin\"}"}" --yes

# Retrieve API & User pool details
userPoolStackName="customgpt-webapp-userpool"
apiStackName="customgpt-webapp-api"

userPoolId=$(aws cloudformation describe-stacks --stack-name "$userPoolStackName" --output 'text' --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue')
userClientPoolId=$(aws cloudformation describe-stacks --stack-name "$userPoolStackName" --output 'text' --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue')
echo "{\"version\":1,\"userPoolId\":\"$userPoolId\",\"webClientId\":\"$userClientPoolId\",\"nativeClientId\":\"$userClientPoolId\"}" > authconfig.importauth.json
apiEndpoint=$(aws cloudformation describe-stacks --stack-name "$apiStackName" --output 'text' --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue')
echo "{\"apiName\":\"customgpt-webapp-api\",\"apiEndpoint\":\"$apiEndpoint\"}" > src/custom.configuration.json

# Add Auth to Amplify app
cat authconfig.importauth.json | jq -c | amplify import auth --headless

# Build project
npm run build

# Push Amplify app
amplify push --yes