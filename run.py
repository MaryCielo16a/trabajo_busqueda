#!/usr/bin/env python3
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the CLI
from cli.main import main

if __name__ == "__main__":
    main()
