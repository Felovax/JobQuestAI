# Gjør at testene finner modulene i backend/ (samme som når main.py kjøres)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
