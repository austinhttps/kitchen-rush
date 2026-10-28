FROM python:3.12-slim
WORKDIR /app
COPY server.py game.py modes.py bots.py navigation.py physics.py config.py rooms.py round_control.py chaos.py host_controls.py public_state.py presence.py vip.py service.py kitchen_layout.py outcomes.py dining.py ./
COPY public ./public
EXPOSE 8000
CMD ["python", "server.py"]
