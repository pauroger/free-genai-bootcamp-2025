# Backend API
backend: cd lang-portal/backend-flask && ../../venv/bin/python app.py

# Frontend web interface
frontend: cd lang-portal/frontend-react && . ~/.nvm/nvm.sh && nvm use node && npm run dev -- --open

# Practice apps
writing-practice: cd writing-practice && ../venv/bin/python -m streamlit run app.py --server.headless=true
vocabulary-practice: cd vocabulary-practice && ../gradio_env/bin/python app.py
listening-practice: cd listening-comp && ../venv/bin/python -m streamlit run frontend/main.py --server.port=8502 --server.headless=true
singing-practice: cd song-agent && ../venv/bin/python -m streamlit run app.py --server.headless=true
speaking-practice: cd speaking-practice && ../gradio_env/bin/python app.py
