import os
import shlex
import shutil
import time
import uuid

import docker

from app.core.config import settings
from app.core.logger import logger


def get_docker_client(timeout: int = 30, interval: int = 2) -> docker.DockerClient:
    """
    Подключается к docker клиенту. Просто depends в compose не хватает.

    Args:
        timeout (int): количество секунд ожидания
        interval (int): интервал в секундах между попытками

    Returns:
        docker.DockerClient: инстанц докер клиента
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            client = docker.DockerClient(base_url=settings.DOCKER_HOST)
            client.version()
            logger.info("Got docker client")
            return client
        except Exception as e:
            logger.debug(f"Waiting for dind to be ready...{str(e)}")
            time.sleep(interval)
    raise Exception("Timed out waiting for Docker daemon")


client = get_docker_client()


def run_solution_in_container(
    code: str, language: str, test_cases: list, time_limit: int, memory_limit: int
) -> dict:
    """
    Запускает код решения для каждого тест-кейса с учетом ЯП и ограничений и возвращает общий результат.

    Для каждого ЯП выбирается свой Docker-образ, расширение файла и команда запуска.
    Input тест-кейса подается в stdin контейнера через echo.

    Args:
        code (str): код решения
        language (str): ЯП (python/java/javascript/c++/cpp) решения
        test_cases (dict[str, str]): данные тест-кейса; входные данные - "input", выходные - "expected_output"
        time_limit (int): ограничение по времени выполнения в секундах
        memory_limit (int): ограничение по памтяи в Мб
    """
    logger.info(f"Running solution:\n{code}\n")
    overall_status = "AC"
    max_time_used = 0.0
    results = []

    # Выбор образа, расширения файла и команды запуска в соответствии с поданным ЯП
    if language == "python":
        image = "python:3.12-slim"
        file_name = "code.py"
        command_template = "echo {input} | python /app/{file}"
    elif language == "java":
        image = "openjdk:17-slim"
        file_name = "Main.java"
        command_template = "javac /app/{file} && echo {input} | java -cp /app Main"
    elif language == "javascript":
        image = "node:18-slim"
        file_name = "code.js"
        command_template = "echo {input} | node /app/{file}"
    elif language == "c++" or language == "cpp":
        image = "gcc:latest"
        file_name = "code.cpp"
        command_template = "g++ /app/{file} -o /app/main && echo {input} | /app/main"
    mem_lim = f"{memory_limit}m"

    # Базовая директория для хранения файлов с кодом решения
    base_tmp = "/shared_tmp"
    os.makedirs(base_tmp, exist_ok=True)

    for tc in test_cases:
        tc_input = tc.get("input", "")
        expected_output = tc.get("expected_output", "")

        temp_dir = os.path.join(base_tmp, str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        try:
            code_file_path = os.path.join(temp_dir, file_name)
            with open(code_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Полная отформатированная версия команды запуска
            quoted_input = shlex.quote(tc_input)
            command = [
                "sh",
                "-c",
                command_template.format(input=quoted_input, file=file_name),
            ]

            # Запуск докер контейнера
            container = client.containers.run(
                image=image,
                command=command,
                detach=True,
                mem_limit=mem_lim,
                cpu_quota=50000,
                volumes={
                    temp_dir: {"bind": "/app", "mode": "rw"},
                },
            )
            logger.debug("Created container")

            start_time = time.time()
            tc_status = None
            while container.status != "exited":
                container.reload()
                elapsed = time.time() - start_time
                logger.debug(f"Elapsed: {elapsed:.2f}s, Time limit: {time_limit:.2f}s")
                if elapsed > time_limit:
                    try:
                        container.kill()
                    except Exception as e:
                        logger.error(f"Error killing container: {str(e)}")
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
                    print("Test case result: TLE")
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
                logger.info(
                    f"Test case result: {tc_status}, Time used:  {elapsed:.2f}s"
                )

                if tc_status == "TLE":
                    overall_status = "TLE"
                elif tc_status == "RE" and overall_status not in ["TLE"]:
                    overall_status = "RE"
                elif tc_status == "WA" and overall_status not in ["TLE", "RE"]:
                    overall_status = "WA"

                if elapsed > max_time_used:
                    max_time_used = elapsed
        except Exception as ex:
            logger.error(f"Error during processing test case: {str(ex)}")
            results.append(
                {
                    "status": "RE",
                    "time_used": 0,
                    "output": None,
                }
            )
            overall_status = "RE"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return {"status": overall_status, "time_used": max_time_used, "results": results}
