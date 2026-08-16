import sys
import os

# Add application path to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
