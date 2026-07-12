#!/bin/bash

echo "Starting Fastapi backend on port 8000..."
uvicorn model.api:app --host 0.0.0.0 --port 8000 &

sleep 3

echo "Starting streamlit frontend on port 8501..."
streamlit run model/app.py --server.port 8501 --server.address 0.0.0.0