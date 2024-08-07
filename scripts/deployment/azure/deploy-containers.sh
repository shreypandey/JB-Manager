#!/bin/bash

if [ $# -lt 3 ]; then
    echo "Usage: $0 Resource_group Preferred_region Identifier"
    exit 1
fi

export RESOURCE_GROUP=$1
export PREFERRED_REGION=$2
export IDENTIFIER=$3

export CONTAINER_APP_ENVIRONMENT_NAME=jb-managerenv-$IDENTIFIER
export container_app_environment_workload_profile_name=envwp-$IDENTIFIER

# create ContainerApp Environment, Workload Profile and Container App
error_message=$(az containerapp env create \
-n $CONTAINER_APP_ENVIRONMENT_NAME \
-g $RESOURCE_GROUP \
--location $PREFERRED_REGION \
--enable-workload-profiles )

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo "Error: $error_message"
    exit 1
fi

# setting Container App Environment Variables
export AZURE_SPEECH_KEY=$AZURE_SPEECH_KEY
export AZURE_SPEECH_REGION=$AZURE_SPEECH_REGION
export AZURE_TRANSLATION_KEY=$AZURE_TRANSLATION_KEY
export AZURE_TRANSLATION_RESOURCE_LOCATION=$AZURE_TRANSLATION_RESOURCE_LOCATION

export AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
export OPENAI_API_KEY=$OPENAI_API_KEY
export OPENAI_API_TYPE=azure
export OPENAI_EMBEDDINGS_DEPLOYMENT=$OPENAI_EMBEDDINGS_DEPLOYMENT

export KAFKA_BROKER=$KAFKA_BROKER
export KAFKA_PRODUCER_USERNAME=$KAFKA_PRODUCER_USERNAME
export KAFKA_PRODUCER_PASSWORD=$KAFKA_PRODUCER_PASSWORD
export KAFKA_CONSUMER_USERNAME=$KAFKA_CONSUMER_USERNAME
export KAFKA_CONSUMER_PASSWORD=$KAFKA_CONSUMER_PASSWORD
export KAFKA_USE_SASL=true

export POSTGRES_DATABASE_HOST=$POSTGRES_DATABASE_HOST
export POSTGRES_DATABASE_NAME=$POSTGRES_DATABASE_NAME
export POSTGRES_DATABASE_USERNAME=$POSTGRES_DATABASE_USERNAME
export POSTGRES_DATABASE_PASSWORD=$POSTGRES_DATABASE_PASSWORD
export POSTGRES_DATABASE_PORT=5432

export STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL
export STORAGE_AUDIOFILES_CONTAINER=$STORAGE_AUDIOFILES_CONTAINER
export STORAGE_ACCOUNT_KEY=$STORAGE_ACCOUNT_KEY

# environment variables for container apps
export container_registry_name=docker.io
export jb_manager_app=opennyaiin/jugalbandi-manager
export api_container_app_name=api
export channel_container_app_name=channel
export flow_container_app_name=flow
export indexer_container_app_name=indexer
export language_container_app_name=language
export retriever_container_app_name=retriever
export container_version=1.0.0
export container_target_port=8000

echo "Creating API Container App" "\n"

# create Container App
container_app_fqdn=$(az containerapp create \
--name $language_container_app_name \
--resource-group $rg_name \
--image $container_registry_name/$jb_manager_app:$language_container_app_name-$container_version \
--environment $CONTAINER_APP_ENVIRONMENT_NAME \
--cpu 0.5 \
--memory 1Gi \
--min-replicas 1 \
--max-replicas 1 \
--workload-profile-name "Consumption" \
--env-vars "POSTGRES_DATABASE_NAME=$POSTGRES_DATABASE_NAME" "POSTGRES_DATABASE_USERNAME=$POSTGRES_DATABASE_USERNAME" "POSTGRES_DATABASE_PASSWORD=$POSTGRES_DATABASE_PASSWORD" "POSTGRES_DATABASE_HOST=$POSTGRES_DATABASE_HOST" "POSTGRES_DATABASE_PORT=$POSTGRES_DATABASE_PORT" "KAFKA_BROKER=$KAFKA_BROKER" "KAFKA_USE_SASL=$KAFKA_USE_SASL" "KAFKA_PRODUCER_USERNAME=$KAFKA_PRODUCER_USERNAME" "KAFKA_PRODUCER_PASSWORD=$KAFKA_PRODUCER_PASSWORD" "KAFKA_FLOW_TOPIC=$KAFKA_FLOW_TOPIC" "KAFKA_CHANNEL_TOPIC=$KAFKA_CHANNEL_TOPIC" "KAFKA_LANGUAGE_TOPIC=$KAFKA_LANGUAGE_TOPIC" "KAFKA_CONSUMER_USERNAME=$KAFKA_CONSUMER_USERNAME" "KAFKA_CONSUMER_PASSWORD=$KAFKA_CONSUMER_PASSWORD" "BHASHINI_USER_ID=$BHASHINI_USER_ID" "BHASHINI_API_KEY=$BHASHINI_API_KEY" "BHASHINI_PIPELINE_ID=$BHASHINI_PIPELINE_ID" "AZURE_SPEECH_KEY=$AZURE_SPEECH_KEY" "AZURE_SPEECH_REGION=$AZURE_SPEECH_REGION" "AZURE_TRANSLATION_KEY=$AZURE_TRANSLATION_KEY" "AZURE_TRANSLATION_RESOURCE_LOCATION=$AZURE_TRANSLATION_RESOURCE_LOCATION" "STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL" "STORAGE_ACCOUNT_KEY=$STORAGE_ACCOUNT_KEY" "STORAGE_AUDIOFILES_CONTAINER=$STORAGE_AUDIOFILES_CONTAINER")

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo "Error: $container_app_fqdn"
    exit 1
fi

container_app_fqdn=$(az containerapp create \
--name $flow_container_app_name \
--resource-group $rg_name \
--image $container_registry_name/$jb_manager_app:$flow_container_app_name-$container_version \
--environment $CONTAINER_APP_ENVIRONMENT_NAME \
--cpu 0.5 \
--memory 1Gi \
--min-replicas 1 \
--max-replicas 1 \
--workload-profile-name "Consumption" \
--env-vars "POSTGRES_DATABASE_NAME=$POSTGRES_DATABASE_NAME" "POSTGRES_DATABASE_USERNAME=$POSTGRES_DATABASE_USERNAME" "POSTGRES_DATABASE_PASSWORD=$POSTGRES_DATABASE_PASSWORD" "POSTGRES_DATABASE_HOST=$POSTGRES_DATABASE_HOST" "POSTGRES_DATABASE_PORT=$POSTGRES_DATABASE_PORT" "KAFKA_BROKER=$KAFKA_BROKER" "KAFKA_USE_SASL=$KAFKA_USE_SASL" "KAFKA_PRODUCER_USERNAME=$KAFKA_PRODUCER_USERNAME" "KAFKA_PRODUCER_PASSWORD=$KAFKA_PRODUCER_PASSWORD" "KAFKA_FLOW_TOPIC=$KAFKA_FLOW_TOPIC" "KAFKA_CHANNEL_TOPIC=$KAFKA_CHANNEL_TOPIC" "KAFKA_RETRIEVER_TOPIC=$KAFKA_RETRIEVER_TOPIC" "KAFKA_LANGUAGE_TOPIC=$KAFKA_LANGUAGE_TOPIC" "KAFKA_CONSUMER_USERNAME=$KAFKA_CONSUMER_USERNAME" "KAFKA_CONSUMER_PASSWORD=$KAFKA_CONSUMER_PASSWORD" "STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL" "STORAGE_ACCOUNT_KEY=$STORAGE_ACCOUNT_KEY" "STORAGE_AUDIOFILES_CONTAINER=$STORAGE_AUDIOFILES_CONTAINER" "ENCRYPTION_KEY=$ENCRYPTION_KEY")

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo "Error: $container_app_fqdn"
    exit 1
fi

container_app_fqdn=$(az containerapp create \
--name $channel_container_app_name \
--resource-group $rg_name \
--image $container_registry_name/$jb_manager_app:$channel_container_app_name-$container_version \
--environment $CONTAINER_APP_ENVIRONMENT_NAME \
--cpu 0.5 \
--memory 1Gi \
--min-replicas 1 \
--max-replicas 1 \
--workload-profile-name "Consumption" \
--env-vars "POSTGRES_DATABASE_NAME=$POSTGRES_DATABASE_NAME" "POSTGRES_DATABASE_USERNAME=$POSTGRES_DATABASE_USERNAME" "POSTGRES_DATABASE_PASSWORD=$POSTGRES_DATABASE_PASSWORD" "POSTGRES_DATABASE_HOST=$POSTGRES_DATABASE_HOST" "POSTGRES_DATABASE_PORT=$POSTGRES_DATABASE_PORT" "KAFKA_BROKER=$KAFKA_BROKER" "KAFKA_USE_SASL=$KAFKA_USE_SASL" "KAFKA_PRODUCER_USERNAME=$KAFKA_PRODUCER_USERNAME" "KAFKA_PRODUCER_PASSWORD=$KAFKA_PRODUCER_PASSWORD" "KAFKA_LANGUAGE_TOPIC=$KAFKA_LANGUAGE_TOPIC" "KAFKA_FLOW_TOPIC=$KAFKA_FLOW_TOPIC" "KAFKA_CHANNEL_TOPIC=$KAFKA_CHANNEL_TOPIC" "KAFKA_CONSUMER_USERNAME=$KAFKA_CONSUMER_USERNAME" "KAFKA_CONSUMER_PASSWORD=$KAFKA_CONSUMER_PASSWORD" "STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL" "STORAGE_ACCOUNT_KEY=$STORAGE_ACCOUNT_KEY" "STORAGE_AUDIOFILES_CONTAINER=$STORAGE_AUDIOFILES_CONTAINER" "ENCRYPTION_KEY=$ENCRYPTION_KEY" "WA_API_HOST=$WA_API_HOST")

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo "Error: $container_app_fqdn"
    exit 1
fi

container_app_fqdn=$(az containerapp create \
--name $api_container_app_name \
--resource-group $rg_name \
--image $container_registry_name/$jb_manager_app:$api_container_app_name-$container_version \
--environment $CONTAINER_APP_ENVIRONMENT_NAME \
--ingres external \
--target-port $container_target_port \
--cpu 0.5 \
--memory 1Gi \
--min-replicas 1 \
--max-replicas 2 \
--workload-profile-name "Consumption" \
--scale-rule-name http-rule \
--scale-rule-http-concurrency 50 \
--env-vars "POSTGRES_DATABASE_NAME=$POSTGRES_DATABASE_NAME" "POSTGRES_DATABASE_USERNAME=$POSTGRES_DATABASE_USERNAME" "POSTGRES_DATABASE_PASSWORD=$POSTGRES_DATABASE_PASSWORD" "POSTGRES_DATABASE_HOST=$POSTGRES_DATABASE_HOST" "POSTGRES_DATABASE_PORT=$POSTGRES_DATABASE_PORT" "KAFKA_BROKER=$KAFKA_BROKER" "KAFKA_USE_SASL=$KAFKA_USE_SASL" "KAFKA_PRODUCER_USERNAME=$KAFKA_PRODUCER_USERNAME" "KAFKA_PRODUCER_PASSWORD=$KAFKA_PRODUCER_PASSWORD" "KAFKA_CHANNEL_TOPIC=$KAFKA_CHANNEL_TOPIC" "KAFKA_FLOW_TOPIC=$KAFKA_FLOW_TOPIC" "STORAGE_ACCOUNT_URL=$STORAGE_ACCOUNT_URL" "STORAGE_ACCOUNT_KEY=$STORAGE_ACCOUNT_KEY" "STORAGE_AUDIOFILES_CONTAINER=$STORAGE_AUDIOFILES_CONTAINER" "ENCRYPTION_KEY=$ENCRYPTION_KEY" "WA_API_HOST=$WA_API_HOST" \
--query properties.configuration.ingress.fqdn)

# Check if the command was successful
if [ $? -ne 0 ]; then
    echo "Error: $container_app_fqdn"
    exit 1
fi

echo "Container App FQDN " + $container_app_fqdn

# Write output to the file
echo "Output File Path: $AZ_SCRIPTS_OUTPUT_PATH"
echo '{"result": {"API FQDN": '$container_app_fqdn'}}' > $AZ_SCRIPTS_OUTPUT_PATH
cat $AZ_SCRIPTS_OUTPUT_PATH
