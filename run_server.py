"""Launcher script for the Sports Card MCP Server."""
import sys
import os

# Ensure we're running from the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import main

if __name__ == "__main__":
    main()
