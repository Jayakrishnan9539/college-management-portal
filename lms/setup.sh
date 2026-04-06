#!/bin/bash
# ─── LMS Quick Setup Script ────────────────────────────────────────────────────
# Run this from the project root: bash setup.sh

echo "🎓 Setting up Landmine Soft LMS..."

# ── Backend setup
echo ""
echo "📦 Installing Python dependencies..."
cd backend
python -m venv venv
source venv/bin/activate 2>/dev/null || venv\Scripts\activate
pip install -r requirements.txt

echo ""
echo "⚙️  Setting up .env file..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ .env created — please edit it with your MySQL credentials before continuing."
  echo "   Then re-run: python manage.py migrate"
else
  echo "   .env already exists."
fi

echo ""
echo "🗄️  Running database migrations..."
python manage.py makemigrations users courses attendance marks fees announcements
python manage.py migrate

echo ""
echo "✅ Backend setup complete!"
echo "   Start with: cd backend && source venv/bin/activate && python manage.py runserver"

# ── Frontend setup
echo ""
echo "📦 Installing Node.js dependencies..."
cd ../frontend
npm install

echo ""
echo "✅ Frontend setup complete!"
echo "   Start with: cd frontend && npm start"

echo ""
echo "─────────────────────────────────────────────────────"
echo "🚀 LMS is ready!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   Swagger:  http://localhost:8000/swagger/"
echo "─────────────────────────────────────────────────────"
