"""Las pruebas no salen a internet: cualquier intento de conectar o de resolver un nombre fuera de esta máquina
falla en el acto con un aviso claro (una prueba que dependiera de la red podría pasar o fallar según el día). La
prueba con navegador sirve la web desde esta máquina (127.0.0.1) y su navegador va en otro proceso."""
import os
import socket

import pytest

LOCALES = {"127.0.0.1", "::1", "localhost", "0.0.0.0", None, ""}


class RedEnPruebas(OSError):
    pass


@pytest.fixture(autouse=True)
def sin_red(monkeypatch):
    conectar, resolver = socket.socket.connect, socket.getaddrinfo

    def connect(self, addr):
        if isinstance(addr, tuple) and addr[0] not in LOCALES:
            raise RedEnPruebas(f"las pruebas no salen a internet: {addr[0]}")
        return conectar(self, addr)

    def getaddrinfo(host, *a, **k):
        if host not in LOCALES:
            raise RedEnPruebas(f"las pruebas no salen a internet: {host}")
        return resolver(host, *a, **k)

    # git va en otro proceso (el bloqueo de arriba no lo alcanza): en las pruebas solo puede usar repositorios locales
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    # y sin la configuración de git de esta máquina (nombre de autor…): como en GitHub, donde no hay ninguna
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
