"""Web server - just runs the Flask app from api.py"""
import os
import sys

# Ensure game dir is in path
game_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(game_dir))

from api import app

if __name__ == "__main__":
    print("三国文字Roguelike Web UI")
    print("Open http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)