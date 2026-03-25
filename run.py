"""Streamlit launcher with UTF-8 encoding."""
import os, sys
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
from streamlit.web.cli import main
sys.argv = ['streamlit', 'run', 'app.py', '--server.port', '8501', '--server.headless', 'true', '--server.address', '0.0.0.0']
main()
