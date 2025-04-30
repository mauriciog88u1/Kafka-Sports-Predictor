#!/bin/bash

# Set project ID and service name
PROJECT_ID="bet365-fastapi-demo"
SERVICE_NAME="bet365-predictor-api"
REGION="us-central1"
REPOSITORY="bet365-backend"

# Set the project
gcloud config set project $PROJECT_ID

# Build and push the Docker image
echo "Building and pushing Docker image..."
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE_NAME \
  --project=$PROJECT_ID

# Deploy to Cloud Run with all environment variables
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="KAFKA_BOOTSTRAP=pkc-n3603.us-central1.gcp.confluent.cloud:9092" \
  --set-env-vars="SPORTSDB_API_KEY=638861" \
  --set-env-vars="KAFKA_SECURITY_PROTOCOL=SASL_SSL" \
  --set-env-vars="KAFKA_SASL_MECHANISM=PLAIN" \
  --set-env-vars="KAFKA_USERNAME=RIVTERCF6O6NO5M5" \
  --set-env-vars="KAFKA_PASSWORD=26SV6blptYtNsyh2wFzdMRsRadlp/cSZcchcmvsSEXd58jvF4P8pS2vCVouHXrCG" \
  --set-env-vars="KAFKA_GROUP_ID=bet365-predictor" \
  --set-env-vars="KAFKA_TOPIC=match_predictions" \
  --set-env-vars="KAFKA_PRODUCER_ACKS=all" \
  --set-env-vars="KAFKA_PRODUCER_RETRIES=3" \
  --set-env-vars="KAFKA_PRODUCER_BATCH_SIZE=16384" \
  --set-env-vars="KAFKA_PRODUCER_LINGER_MS=1" \
  --set-env-vars="KAFKA_PRODUCER_BUFFER_MEMORY=33554432" \
  --set-env-vars="KAFKA_CONSUMER_AUTO_OFFSET_RESET=latest" \
  --set-env-vars="KAFKA_CONSUMER_ENABLE_AUTO_COMMIT=false" \
  --set-env-vars="KAFKA_CONSUMER_MAX_POLL_RECORDS=500"

echo "Deployment complete!" 