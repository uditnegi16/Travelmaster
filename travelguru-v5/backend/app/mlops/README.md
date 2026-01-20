python -m venc venv.venv\scripts\activate
pip install -r requirements.txt
 cd/frontend -----streamlit - streamlit run app.py
 cd mlops---backend mlops: uvicorn api.main:app --reload --port 8000
 cd agent folder------uvicorn main:app --reload --port 9000