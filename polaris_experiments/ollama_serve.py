
import os
import time

import radical.utils as ru

WORK_DIR = '/home/matitov/ollama'


def ollama_serve():
    host_ip = ru.get_hostip()
    ru.sh_callout_bg(f'OLLAMA_HOST={host_ip} {WORK_DIR}/bin/ollama serve',
                     shell=True)

    ollama_host = None

    stderr_file = os.getenv('RP_TASK_ID') + '.err'
    while not ollama_host:
        with ru.ru_open(stderr_file) as fd:
            stderr_ctx = fd.read()
        if 'OLLAMA_HOST' not in stderr_ctx:
            continue
        ollama_host = stderr_ctx.split('OLLAMA_HOST:', 1)[1].split(' ', 1)[0]

    return ollama_host


def main():
    reg_addr = os.getenv('RP_REGISTRY_ADDRESS')
    reg = ru.zmq.RegistryClient(url=reg_addr)
    reg['ollama.addr'] = ollama_serve()
    reg.close()


if __name__ == '__main__':
    main()
    while True:
        time.sleep(10)

