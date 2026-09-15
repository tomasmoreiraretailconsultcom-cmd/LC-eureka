python -m venv .venv

.venv\Scripts\activate.bat

pip install -r requirements.txt

jupyter execute LC_model_v0_2_0.ipynb

streamlit run ui.py
