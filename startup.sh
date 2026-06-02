#!/bin/bash

# Install logging monitor. The monitor will automatically pick up logs sent to
# syslog.
curl -s "https://storage.googleapis.com/signals-agents/logging/google-fluentd-install.sh" | bash
service google-fluentd restart &

# Install dependencies from apt
apt-get update
apt-get install -yq ca-certificates git build-essential supervisor psmisc \
  software-properties-common curl gnupg

# Install Python 3.11
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -yq python3.11 python3.11-venv python3.11-dev

# Install Node.js 20
mkdir -p /opt/nodejs
curl https://nodejs.org/dist/v20.19.0/node-v20.19.0-linux-x64.tar.gz \
  | tar xvzf - -C /opt/nodejs --strip-components=1
ln -sf /opt/nodejs/bin/node /usr/bin/node
ln -sf /opt/nodejs/bin/npm /usr/bin/npm

# Get the application source code from the Google Cloud Storage bucket.
mkdir /tom-tat-benh-an
gsutil -m cp -r gs://[YOUR_BUCKET]/tom-tat-benh-an/* /tom-tat-benh-an/

# Write the .env file from GCE instance metadata (set these at VM creation time
# under --metadata GOOGLE_API_KEY=...).
METADATA_URL="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
GOOGLE_API_KEY=$(curl -sf "${METADATA_URL}/GOOGLE_API_KEY" -H "Metadata-Flavor: Google")

cat > /tom-tat-benh-an/backend/.env << EOF
GOOGLE_API_KEY=${GOOGLE_API_KEY}
CHROMA_PATH=./chroma_data
CSV_PATH=./data/sample.csv

# LiteLLM Router — summary group (both models are load-balanced)
SUMMARY_MODEL_1=gemini-2.5-flash-lite
SUMMARY_MODEL_2=gemini-2.5-flash

# LiteLLM Router — chat group (both models are load-balanced)
CHAT_MODEL_1=gemini-2.5-flash-lite
CHAT_MODEL_2=gemini-2.5-flash

# Evaluation judge (unchanged — direct Gemini API)
GEMINI_JUDGE_MODEL=gemini-2.5-flash
JUDGE_MAX_WAIT=900
EOF

# Set up Python virtual environment and install backend dependencies.
python3.11 -m venv /tom-tat-benh-an/backend/.venv
/tom-tat-benh-an/backend/.venv/bin/pip install --upgrade pip -q
/tom-tat-benh-an/backend/.venv/bin/pip install --no-cache-dir \
  -r /tom-tat-benh-an/backend/requirements.txt

# Install frontend npm dependencies.
cd /tom-tat-benh-an/frontend
npm install

# Create an appuser. The application will run as this user.
useradd -m -d /home/appuser appuser
chown -R appuser:appuser /tom-tat-benh-an

# Configure supervisor to run the FastAPI backend.
cat > /etc/supervisor/conf.d/backend.conf << EOF
[program:backend]
directory=/tom-tat-benh-an/backend
command=/tom-tat-benh-an/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
autostart=true
autorestart=true
user=appuser
environment=HOME="/home/appuser",USER="appuser"
stdout_logfile=syslog
stderr_logfile=syslog
EOF

# Configure supervisor to run the Vite frontend.
cat > /etc/supervisor/conf.d/frontend.conf << EOF
[program:frontend]
directory=/tom-tat-benh-an/frontend
command=npm run dev -- --host
autostart=true
autorestart=true
user=appuser
environment=HOME="/home/appuser",USER="appuser",NODE_ENV="development"
stdout_logfile=syslog
stderr_logfile=syslog
EOF

supervisorctl reread
supervisorctl update
