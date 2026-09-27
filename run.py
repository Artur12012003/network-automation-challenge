"""Ponto de entrada simples: execute ``py run.py`` no Windows."""

from frontend.app import app


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
