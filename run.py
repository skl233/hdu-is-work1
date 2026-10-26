"""Entry point for local runs: python run.py"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=False in every environment (Flask debugger leaks source and console).
    app.run(host="127.0.0.1", port=5000, debug=False)
