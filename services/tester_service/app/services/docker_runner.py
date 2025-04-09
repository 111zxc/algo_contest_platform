import os
import shlex
import shutil
import time
import uuid

import docker

from app.core.config import settings
from app.core.logger import logger


def get_docker_client(timeout=30, interval=2):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client = docker.DockerClient(base_url=settings.DOCKER_HOST)
            client.version()
            print("Got docker client")
            return client
        except Exception as e:
            print("Waiting for dind to be ready...", e)
            time.sleep(interval)
    raise Exception("Timed out waiting for Docker daemon")


client = get_docker_client()


def run_solution_in_container(
    code: str, language: str, test_cases: list, time_limit: int
):
    """
    Запускает код решения для каждого тесткейса с учетом языка программирования и возвращает общий результат.

    Для каждого языка выбирается свой Docker-образ, расширение файла и команда запуска.
    Тестовый ввод подается через echo.
    """
    logger.info(f"Running solution:\n{code}\n")
    overall_status = "AC"
    max_time_used = 0.0
    results = []

    lang = language.lower()
    if lang == "python":
        image = "python:3.12-slim"
        file_name = "code.py"
        command_template = "echo {input} | python /app/{file}"
    elif lang == "java":
        image = "openjdk:17-slim"
        file_name = "Main.java"
        command_template = "javac /app/{file} && echo {input} | java -cp /app Main"
    elif lang == "javascript":
        image = "node:18-slim"
        file_name = "code.js"
        command_template = "echo {input} | node /app/{file}"
    elif lang == "c++" or lang == "cpp":
        image = "gcc:latest"
        file_name = "code.cpp"
        command_template = "g++ /app/{file} -o /app/main && echo {input} | /app/main"
        command_template = "dotnet new console --output /app && cp /app/{file} /app/Program.cs && dotnet run --project /app"
    else:
        image = "python:3.12-slim"
        file_name = "code.py"
        command_template = "echo {input} | python /app/{file}"

    base_tmp = "/shared_tmp"
    os.makedirs(base_tmp, exist_ok=True)

    for tc in test_cases:
        tc_input = tc.get("input", "")
        expected_output = tc.get("expected_output", "")
        logger.debug("Test case:")
        logger.debug("Input:", repr(tc_input))
        logger.debug("Expected Output:", repr(expected_output))

        temp_dir = os.path.join(base_tmp, str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        try:
            code_file_path = os.path.join(temp_dir, file_name)
            with open(code_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            quoted_input = shlex.quote(tc_input)
            command = [
                "sh",
                "-c",
                command_template.format(input=quoted_input, file=file_name),
            ]

            container = client.containers.run(
                image=image,
                command=command,
                detach=True,
                mem_limit="256m",
                cpu_quota=50000,
                volumes={
                    temp_dir: {"bind": "/app", "mode": "rw"},
                },
            )

            start_time = time.time()
            tc_status = None
            while container.status != "exited":
                container.reload()
                elapsed = time.time() - start_time
                if elapsed > time_limit:
                    container.kill()
                    container.remove()
                    tc_status = "TLE"
                    results.append(
                        {
                            "status": tc_status,
                            "time_used": elapsed,
                            "output": None,
                        }
                    )
                    overall_status = "TLE"
                    logger.info("Test case result: TLE")
                    break
                time.sleep(0.5)
            else:
                elapsed = time.time() - start_time
                logs = container.logs().decode("utf-8")
                exit_code = container.wait()["StatusCode"]
                container.remove()

                logger.debug("Container logs:")
                logger.debug(logs)
                if exit_code != 0:
                    tc_status = "RE"
                else:
                    actual_output = logs.strip()
                    if actual_output == expected_output.strip():
                        tc_status = "AC"
                    else:
                        tc_status = "WA"

                results.append(
                    {
                        "status": tc_status,
                        "time_used": elapsed,
                        "output": logs,
                    }
                )
                logger.debug("Test case result:", tc_status, "Time used:", elapsed)

                if tc_status == "TLE":
                    overall_status = "TLE"
                elif tc_status == "RE" and overall_status not in ["TLE"]:
                    overall_status = "RE"
                elif tc_status == "WA" and overall_status not in ["TLE", "RE"]:
                    overall_status = "WA"

                if elapsed > max_time_used:
                    max_time_used = elapsed
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return {"status": overall_status, "time_used": max_time_used, "results": results}
