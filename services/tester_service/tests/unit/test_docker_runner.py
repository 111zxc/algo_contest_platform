import builtins
from unittest.mock import MagicMock, mock_open
import pytest

import app.services.docker_runner as docker_runner


class DummySettings:
    DOCKER_HOST = "tcp://docker:2375"


class DummySpec:
    def __init__(self, image="img", file_name="main.py", command_template="python {file} << 'EOF'\n{input}\nEOF"):
        self.image = image
        self.file_name = file_name
        self.command_template = command_template


def test_get_docker_client_success_first_try(logger_mock, monkeypatch):
    monkeypatch.setattr(docker_runner, "logger", logger_mock)
    monkeypatch.setattr(docker_runner, "settings", DummySettings)

    client = MagicMock()
    client.version.return_value = {"ok": True}

    docker_mod = MagicMock()
    docker_mod.DockerClient.return_value = client
    monkeypatch.setattr(docker_runner, "docker", docker_mod)

    res = docker_runner.get_docker_client(timeout=1, interval=0)
    assert res is client
    logger_mock.info.assert_called_once()


def test_get_docker_client_times_out(logger_mock, monkeypatch):
    monkeypatch.setattr(docker_runner, "logger", logger_mock)
    monkeypatch.setattr(docker_runner, "settings", DummySettings)

    docker_mod = MagicMock()
    docker_mod.DockerClient.side_effect = Exception("not ready")
    monkeypatch.setattr(docker_runner, "docker", docker_mod)

    t = {"now": 0.0}
    def fake_time():
        t["now"] += 1.0
        return t["now"]

    monkeypatch.setattr(docker_runner.time, "time", fake_time)
    monkeypatch.setattr(docker_runner.time, "sleep", lambda *_: None)

    with pytest.raises(Exception, match="Timed out waiting for Docker daemon"):
        docker_runner.get_docker_client(timeout=2, interval=0)


def test_run_solution_unsupported_language_returns_RE(logger_mock, monkeypatch):
    monkeypatch.setattr(docker_runner, "logger", logger_mock)
    monkeypatch.setattr(docker_runner, "get_docker_client", lambda: MagicMock())
    monkeypatch.setattr(docker_runner, "get_language", lambda lang: None)

    res = docker_runner.run_solution_in_container(
        code="print(1)",
        language="brainfuck",
        test_cases=[{"input": "", "expected_output": "1"}],
        time_limit=1,
        memory_limit=128,
    )
    assert res["status"] == "RE"
    assert "Unsupported language" in res["results"][0]["output"]


def test_run_solution_single_tc_AC(logger_mock, monkeypatch, tmp_path):
    monkeypatch.setattr(docker_runner, "logger", logger_mock)
    monkeypatch.setattr(docker_runner, "get_language", lambda lang: DummySpec())
    monkeypatch.setattr(docker_runner.uuid, "uuid4", lambda: "fixed-uuid")

    # перенаправляем /shared_tmp -> tmp_path/shared_tmp
    real_join = docker_runner.os.path.join
    def fake_join(*parts):
        if parts and parts[0] == "/shared_tmp":
            parts = (str(tmp_path / "shared_tmp"),) + tuple(parts[1:])
        return real_join(*parts)

    monkeypatch.setattr(docker_runner.os.path, "join", fake_join)
    monkeypatch.setattr(docker_runner.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(docker_runner.shutil, "rmtree", lambda *a, **k: None)

    times = iter([10.0, 10.5])
    monkeypatch.setattr(docker_runner.time, "time", lambda: next(times))

    # контейнер: exit 0, не OOM, logs == expected_output
    container = MagicMock()
    container.wait.return_value = {"StatusCode": 0}
    container.attrs = {"State": {"OOMKilled": False, "ExitCode": 0}}
    container.logs.return_value = b"OK\n"

    client = MagicMock()
    client.containers.run.return_value = container
    monkeypatch.setattr(docker_runner, "get_docker_client", lambda: client)

    m = mock_open()
    monkeypatch.setattr(builtins, "open", m)

    res = docker_runner.run_solution_in_container(
        code="print('OK')",
        language="python",
        test_cases=[{"input": "", "expected_output": "OK"}],
        time_limit=1,
        memory_limit=128,
    )

    assert res["status"] == "AC"
    assert res["time_used"] == 0.5
    assert res["results"][0]["status"] == "AC"
    container.remove.assert_called_once()


def test_run_solution_TLE_when_wait_raises(logger_mock, monkeypatch, tmp_path):
    monkeypatch.setattr(docker_runner, "logger", logger_mock)
    monkeypatch.setattr(docker_runner, "get_language", lambda lang: DummySpec())
    monkeypatch.setattr(docker_runner.uuid, "uuid4", lambda: "fixed-uuid")

    real_join = docker_runner.os.path.join
    def fake_join(*parts):
        if parts and parts[0] == "/shared_tmp":
            parts = (str(tmp_path / "shared_tmp"),) + tuple(parts[1:])
        return real_join(*parts)

    monkeypatch.setattr(docker_runner.os.path, "join", fake_join)
    monkeypatch.setattr(docker_runner.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(docker_runner.shutil, "rmtree", lambda *a, **k: None)

    times = iter([10.0, 12.0])
    monkeypatch.setattr(docker_runner.time, "time", lambda: next(times))

    container = MagicMock()
    container.wait.side_effect = Exception("timeout")
    container.kill.return_value = None
    container.attrs = {"State": {"OOMKilled": False, "ExitCode": None}}
    container.logs.return_value = b""

    client = MagicMock()
    client.containers.run.return_value = container
    monkeypatch.setattr(docker_runner, "get_docker_client", lambda: client)

    m = mock_open()
    monkeypatch.setattr(builtins, "open", m)

    res = docker_runner.run_solution_in_container(
        code="",
        language="python",
        test_cases=[{"input": "", "expected_output": ""}],
        time_limit=1,
        memory_limit=128,
    )
    assert res["status"] == "TLE"
    assert res["results"][0]["status"] == "TLE"


def test_run_solution_MLE_when_oom_killed(logger_mock, monkeypatch, tmp_path):
    monkeypatch.setattr(docker_runner, "logger", logger_mock)
    monkeypatch.setattr(docker_runner, "get_language", lambda lang: DummySpec())
    monkeypatch.setattr(docker_runner.uuid, "uuid4", lambda: "fixed-uuid")

    real_join = docker_runner.os.path.join
    def fake_join(*parts):
        if parts and parts[0] == "/shared_tmp":
            parts = (str(tmp_path / "shared_tmp"),) + tuple(parts[1:])
        return real_join(*parts)

    monkeypatch.setattr(docker_runner.os.path, "join", fake_join)
    monkeypatch.setattr(docker_runner.os, "makedirs", lambda *a, **k: None)
    monkeypatch.setattr(docker_runner.shutil, "rmtree", lambda *a, **k: None)

    times = iter([10.0, 10.2])
    monkeypatch.setattr(docker_runner.time, "time", lambda: next(times))

    container = MagicMock()
    container.wait.return_value = {"StatusCode": 0}
    container.attrs = {"State": {"OOMKilled": True, "ExitCode": 137}}
    container.logs.return_value = b""

    client = MagicMock()
    client.containers.run.return_value = container
    monkeypatch.setattr(docker_runner, "get_docker_client", lambda: client)

    m = mock_open()
    monkeypatch.setattr(builtins, "open", m)

    res = docker_runner.run_solution_in_container(
        code="",
        language="python",
        test_cases=[{"input": "", "expected_output": ""}],
        time_limit=1,
        memory_limit=1,
    )
    assert res["status"] == "MLE"
    assert res["results"][0]["status"] == "MLE"
