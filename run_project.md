py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python -m pip install -r frontend\requirements.txt


cd "C:\Users\HP\OneDrive - Higher Education Commission\Desktop\Final Year Project\FYP1"
.\.venv\Scripts\Activate.ps1
cd backend
$env:DEBUG = "True"          # local development: no SECRET_KEY needed
$env:ADMIN_TOKEN = "choose-one"  # optional: the password the Train page asks for
python manage.py runserver 8000


cd "C:\Users\HP\OneDrive - Higher Education Commission\Desktop\Final Year Project\FYP1"
.\.venv\Scripts\Activate.ps1
cd frontend
python app.py