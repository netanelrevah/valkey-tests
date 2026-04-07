import socket
import subprocess
import time
from random import randrange

import pytest

from tests.valkey_test_client import ValkeyTestClient, _encode_command, _read_response, _SocketReader


def pytest_addoption(parser):
    parser.addoption("--host", default="127.0.0.1", help="Server host to connect to")
    parser.addoption("--port", default=6379, type=int, help="Server port to connect to")
    parser.addoption(
        "--server",
        default=None,
        help=(
            "Command to start the server (e.g. 'valkey-server' or 'python -m pyvalkey'). "
            "If omitted, a server must already be running at --host:--port."
        ),
    )


def _next_free_port(min_port=57343, max_port=65535):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = randrange(min_port, max_port)
    for _ in range(10):
        try:
            sock.bind(("localhost", port))
            sock.close()
            return port
        except OSError:
            port = randrange(min_port, max_port)
    raise OSError("no free ports after 10 retries")


def _wait_for_server(host, port, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            sock = socket.create_connection((host, port), timeout=0.1)
            sock.close()
            return
        except OSError:
            time.sleep(0.01)
    raise TimeoutError(f"Server did not start on {host}:{port}")


def _create_client_socket(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.settimeout(5)
    sock.sendall(_encode_command("select", 9))
    _read_response(_SocketReader(sock))
    return sock


@pytest.fixture(scope="session")
def valkey_server(request):
    host = request.config.getoption("--host")
    port = request.config.getoption("--port")
    server_cmd = request.config.getoption("--server")
    if server_cmd:
        port = _next_free_port()
        proc = subprocess.Popen([*server_cmd.split(), "--port", str(port)])
        _wait_for_server(host, port)
        yield {"host": host, "port": port}
        proc.terminate()
        proc.wait(timeout=3)
        return
    yield {"host": host, "port": port}


@pytest.fixture()
def r(valkey_server):
    sock = _create_client_socket(valkey_server["host"], valkey_server["port"])
    try:
        yield ValkeyTestClient(sock)
    finally:
        sock.close()


def _client_fixture(valkey_server):
    sock = _create_client_socket(valkey_server["host"], valkey_server["port"])
    try:
        yield ValkeyTestClient(sock)
    finally:
        sock.close()


@pytest.fixture()
def rd(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def rd1(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def rd2(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def rd3(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def rr(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def r2(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def rd_trk(valkey_server):
    yield from _client_fixture(valkey_server)


@pytest.fixture()
def plain_client(valkey_server):
    yield from _client_fixture(valkey_server)
