#!/bin/bash
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   SecureAI — Setup Script                ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Backend
echo "→ Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt --quiet
cp -n .env.example .env 2>/dev/null || true
# Generate real random secrets on first setup (never ship placeholder secrets)
if ! grep -q "^SECRET_KEY=" .env; then
  echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env
  echo "JWT_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" >> .env
  echo "✓ Generated random SECRET_KEY / JWT_SECRET_KEY in backend/.env"
fi
echo "✓ Backend ready"

# Frontend
cd ../frontend
echo "→ Installing frontend dependencies..."
npm install --silent
echo "✓ Frontend ready"

cd ..
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Setup complete!                        ║"
echo "║                                          ║"
echo "║   1. (Optional) add AI key to backend/.env║"
echo "║   2. Run: ./run.sh                       ║"
echo "╚══════════════════════════════════════════╝"
echo ""
