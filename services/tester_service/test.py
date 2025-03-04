import docker
import os

docker_host = os.environ.get("DOCKER_HOST", "tcp://localhost:2375")
client = docker.DockerClient(base_url=docker_host)

container = client.containers.create(
    image="python:3.9-slim",
    command='python -u -c "import sys; data = sys.stdin.read(); print(\'Output:\', data)"',
    tty=False,
    stdin_open=True,
)
container.start()

# Прикрепляемся к контейнеру для отправки ввода
sock = container.attach_socket(params={'stdin': 1, 'stdout': 1, 'stream': 1})
sock._sock.setblocking(True)

input_data = "Привет из удаленного Docker Engine!\n"
sock._sock.sendall(input_data.encode('utf-8'))
sock._sock.shutdown(1)

container.wait()
logs = container.logs(stdout=True, stderr=True)
print("Логи контейнера:")
print(logs.decode('utf-8'))

container.remove()
