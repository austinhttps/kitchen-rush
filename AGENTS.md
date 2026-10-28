# Project workflow

Run the dependency-free server in a container when Docker is available:
`docker build -t kitchen-rush .` then `docker run --rm -p 8000:8000 kitchen-rush`.
If Docker is unavailable, the installed Python 3.12 runtime can run `python server.py` without installing packages.
Validate with `python -m unittest discover -s tests` and `python -m compileall game.py server.py`.
Keep code modules under 300 lines. Room state is authoritative on the server and stored in memory.
