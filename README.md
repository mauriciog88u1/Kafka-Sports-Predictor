# Bet365 Match Prediction Demo

## Demo Site
Visit the live demo at [mauric10.com/bet365](https://mauric10.com/bet365)

## Project Overview
This is a demo application to predict the winner of football games. It consists of:
- A FastAPI backend deployed on Google Cloud Run  
- A Kafka-based asynchronous processing flow  
- A React frontend for selecting teams and viewing predictions  

## What I Did
- Designed and implemented REST API endpoints (`/matches`, `/predict`, `/prediction/{id}`) in FastAPI  
- Generated deterministic `match_id` hashes for consistent correlation and caching  
- Configured Kafka producer in the API and consumer in a separate service for prediction processing  
- Developed a simple heuristic-based prediction algorithm with home advantage and round adjustments  
- Built a React UI with separate “Send Prediction” and “Get Prediction” actions  
- Deployed both services (API and consumer) on Google Cloud Run with secure environment variable management  

## Website Functionality
- **League & Team Selection**: Users select a league and team to fetch upcoming matches  
- **Send Prediction**: Clicking “Send Prediction” enqueues match data to Kafka  
- **Get Prediction**: Clicking “Get Prediction” polls the API until the prediction is ready  
- **Result Display**: Final prediction is displayed dynamically on the page  

## Backend Flow
1. UI selects a match and clicks **Send Prediction**  
2. Frontend sends match payload (with `idEvent`) to FastAPI `POST /predict`  
3. FastAPI:  
   - Computes deterministic `match_id` from `idEvent` using MD5  
   - Fetches and updates match data via multiple external API calls  
   - Stores a placeholder in an in-memory map under `match_id`  
   - Produces the updated data to Kafka topic `match_updates`  
4. Consumer service:  
   - Continuously polls the `match_updates` topic  
   - Deserializes each message and extracts `match_id`  
   - Runs the `predict()` model on the match data  
   - Sends the prediction result back to FastAPI via `PUT /prediction/{match_id}`  
5. FastAPI updates its in-memory map with the final prediction  
6. UI clicks **Get Prediction**, frontend calls `GET /prediction/{match_id}` and displays the prediction  

## What I Would Do Differently Next Time
- Use a Random Forest algorithm with proper train/test splits for real machine learning  
- Integrate a database (e.g., PostgreSQL ) for persistent storage  
- Implement real-time event updates via WebSockets or Server-Sent Events instead of polling  
- Add authentication headers for secure API endpoints  
- Set up GitHub–GCP integrations for CI/CD and automated deployments  
- Refactor code to follow clean code principles and improve maintainability  
- Increase test coverage with unit, integration, and end-to-end tests  
