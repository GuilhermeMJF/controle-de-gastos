import time
from collections import defaultdict, deque
from threading import Lock


class Limitador:
    def __init__(self, maximo: int, janela_segundos: int):
        self.maximo = maximo
        self.janela = janela_segundos
        # Para cada chave (um e-mail ou um IP), os momentos das tentativas recentes
        self._tentativas: dict[str, deque[float]] = defaultdict(deque)
        # As rotas podem rodar ao mesmo tempo; a trava evita que duas mexam na lista juntas
        self._trava = Lock()

    def _recentes(self, chave: str, agora: float) -> deque[float]:
        """Descarta as tentativas que já saíram da janela de tempo."""
        fila = self._tentativas[chave]
        while fila and agora - fila[0] > self.janela:
            fila.popleft()
        return fila

    def segundos_bloqueado(self, chave: str) -> int:
        """0 se ainda pode tentar; senão, quantos segundos faltam para liberar."""
        with self._trava:
            agora = time.monotonic()
            fila = self._recentes(chave, agora)
            if len(fila) < self.maximo:
                if not fila:
                    del self._tentativas[chave]  # não guarda chaves vazias na memória
                return 0
            return int(self.janela - (agora - fila[0])) + 1

    def registrar(self, chave: str):
        with self._trava:
            self._tentativas[chave].append(time.monotonic())

    def esquecer(self, chave: str):
        """Zera as tentativas de uma chave (ex.: depois de um login certo)."""
        with self._trava:
            self._tentativas.pop(chave, None)

    def zerar(self):
        """Zera tudo. Usado nos testes, para um teste não atrapalhar o outro."""
        with self._trava:
            self._tentativas.clear()