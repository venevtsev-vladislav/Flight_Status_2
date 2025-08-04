#!/bin/bash

# Flight Status Bot - Deployment Script
# Usage: ./deploy.sh [platform]

set -e

PLATFORM=${1:-railway}

echo "🚀 Deploying Flight Status Bot to $PLATFORM..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy env.example to .env and fill in your environment variables"
    exit 1
fi

# Check required environment variables
source .env
required_vars=("BOT_TOKEN" "SUPABASE_URL" "SUPABASE_ANON_KEY" "AERODATABOX_API_KEY")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file"
        exit 1
    fi
done

echo "✅ Environment variables checked"

case $PLATFORM in
    "railway")
        echo "📦 Deploying to Railway..."
        if command -v railway &> /dev/null; then
            railway login
            railway up
        else
            echo "⚠️  Railway CLI not found. Please install it first:"
            echo "npm install -g @railway/cli"
            echo "Or deploy manually through Railway dashboard"
        fi
        ;;
    
    "render")
        echo "📦 Deploying to Render..."
        echo "Please deploy manually through Render dashboard:"
        echo "1. Go to https://render.com"
        echo "2. Connect your GitHub repository"
        echo "3. Create new Web Service"
        echo "4. Set build command: pip install -r requirements.txt"
        echo "5. Set start command: python run.py"
        echo "6. Add environment variables"
        ;;
    
    "heroku")
        echo "📦 Deploying to Heroku..."
        if command -v heroku &> /dev/null; then
            # Check if Heroku app exists
            if ! heroku apps:info &> /dev/null; then
                echo "Creating new Heroku app..."
                heroku create
            fi
            
            # Set environment variables
            echo "Setting environment variables..."
            heroku config:set BOT_TOKEN="$BOT_TOKEN"
            heroku config:set SUPABASE_URL="$SUPABASE_URL"
            heroku config:set SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY"
            heroku config:set AERODATABOX_API_KEY="$AERODATABOX_API_KEY"
            
            if [ ! -z "$AMPLITUDE_API_KEY" ]; then
                heroku config:set AMPLITUDE_API_KEY="$AMPLITUDE_API_KEY"
            fi
            if [ ! -z "$AMPLITUDE_SECRET_KEY" ]; then
                heroku config:set AMPLITUDE_SECRET_KEY="$AMPLITUDE_SECRET_KEY"
            fi
            if [ ! -z "$AMPLITUDE_PROJECT_ID" ]; then
                heroku config:set AMPLITUDE_PROJECT_ID="$AMPLITUDE_PROJECT_ID"
            fi
            
            # Deploy
            git add .
            git commit -m "Deploy to Heroku"
            git push heroku main
        else
            echo "⚠️  Heroku CLI not found. Please install it first:"
            echo "https://devcenter.heroku.com/articles/heroku-cli"
        fi
        ;;
    
    "docker")
        echo "📦 Building and running with Docker..."
        docker build -t flight-status-bot .
        docker run -d --name flight-status-bot --env-file .env flight-status-bot
        echo "✅ Bot is running in Docker container"
        ;;
    
    "docker-compose")
        echo "📦 Running with Docker Compose..."
        docker-compose up -d --build
        echo "✅ Bot is running with Docker Compose"
        ;;
    
    *)
        echo "❌ Unknown platform: $PLATFORM"
        echo "Available platforms: railway, render, heroku, docker, docker-compose"
        exit 1
        ;;
esac

echo "🎉 Deployment completed!"
echo "Check the logs to ensure the bot is running correctly" 