import os
import shlex
import shutil
import time
import uuid

import docker

from app.core.config import settings
from app.core.logger import logger


def get_docker_client(timeout: int = 30, interval: int = 2) -> docker.DockerClient:
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


def run_solution_in_container(
    code: str, language: str, test_cases: list, time_limit: int, memory_limit: int
) -> dict:
    client = get_docker_client()

    logger.info(f"Running solution:\n{code}\n")
    overall_status = "AC"
    max_time_used = 0.0
    results = []

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
    elif language in ("c++", "cpp"):
        image = "gcc:latest"
        file_name = "code.cpp"
        command_template = "g++ /app/{file} -o /app/main && echo {input} | /app/main"
    else:
        return {"status": "RE", "time_used": 0.0, "results": [{"status": "RE", "time_used": 0, "output": "Unsupported language"}]}

    mem_lim = f"{memory_limit}m"

    base_tmp = "/shared_tmp"
    os.makedirs(base_tmp, exist_ok=True)

    for tc in test_cases:
        tc_input = tc.get("input", "")
        expected_output = tc.get("expected_output", "")

        temp_dir = os.path.join(base_tmp, str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)

        container = None
        start_time = time.time()

        try:
            code_file_path = os.path.join(temp_dir, file_name)
            with open(code_file_path, "w", encoding="utf-8") as f:
                f.write(code)

            quoted_input = shlex.quote(tc_input)
            command = ["sh", "-c", command_template.format(input=quoted_input, file=file_name)]

            container = client.containers.run(
                image=image,
                command=command,
                detach=True,
                mem_limit=mem_lim,
                cpu_quota=50000,
                volumes={temp_dir: {"bind": "/app", "mode": "rw"}},
            )
            logger.debug("Created container")

            try:
                wait_result = container.wait(timeout=time_limit)
                exit_code = wait_result.get("StatusCode", 1)
                elapsed = time.time() - start_time
            except Exception:
                elapsed = time.time() - start_time
                try:
                    container.kill()
                except Exception:
                    pass
                exit_code = None

            try:
                logs = container.logs().decode("utf-8", errors="replace")
            except Exception as e:
                logger.error(f"Error reading container logs: {str(e)}")
                logs = ""

            if exit_code is None:
                tc_status = "TLE"
            elif exit_code != 0:
                tc_status = "RE"
            else:
                actual_output = logs.strip()
                tc_status = "AC" if actual_output == expected_output.strip() else "WA"

            results.append({"status": tc_status, "time_used": elapsed, "output": logs})
            logger.info(f"Test case result: {tc_status}, Time used: {elapsed:.2f}s")

            if tc_status == "TLE":
                overall_status = "TLE"
            elif tc_status == "RE" and overall_status != "TLE":
                overall_status = "RE"
            elif tc_status == "WA" and overall_status not in ("TLE", "RE"):
                overall_status = "WA"

            if elapsed > max_time_used:
                max_time_used = elapsed

        except Exception as ex:
            logger.error(f"Error during processing test case: {str(ex)}")
            results.append({"status": "RE", "time_used": 0, "output": None})
            overall_status = "RE"

        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            shutil.rmtree(temp_dir, ignore_errors=True)

    return {"status": overall_status, "time_used": max_time_used, "results": results}
