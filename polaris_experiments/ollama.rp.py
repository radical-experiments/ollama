
# cd ~/ollama
# source ve/bin/activate
# nohup python3 ollama.rp.py > OUTPUT 2>&1 </dev/null &

import os

import radical.pilot as rp

os.environ['RADICAL_LOG_LVL'] = 'DEBUG'
os.environ['RADICAL_REPORT']  = 'TRUE'

WORK_DIR = '/home/matitov/ollama'
N_NODES = 2  # 1 for service and 1 for tasks -> 2, 3, 5, 9
CPUS_PER_NODE = 64

IS_BASE = False  # 1 task with many prompts
WITH_PROBE_TASK = False  # have a single-core task before a batch of tasks


def main():
    session = rp.Session()
    pmgr = rp.PilotManager(session)
    tmgr = rp.TaskManager(session)

    service_td = rp.TaskDescription({
        'executable': 'python3',
        'arguments': ['$RP_PILOT_SANDBOX/ollama_serve.py'],
        'pre_exec': [
            'module load PrgEnv-nvhpc',
            'unset https_proxy',
            'unset http_proxy',
            'source %s/ve/bin/activate' % WORK_DIR
        ],
        'cores_per_rank': CPUS_PER_NODE,
        'gpus_per_rank': 4,
        'gpu_type': rp.CUDA
    })

    pilot = pmgr.submit_pilots(rp.PilotDescription({
        'resource': 'anl.polaris',
        'project': 'RECUP',
        'nodes': N_NODES,
        'runtime': 60,
        'sandbox': WORK_DIR,
        'services': [service_td],
        'input_staging': ['ollama_serve.py', 'ollama_client.py']
    }))

    tmgr.add_pilots(pilot)
    pilot.wait(rp.PMGR_ACTIVE)

    tds = []
    if IS_BASE:
        tds.append(rp.TaskDescription({
            'executable': 'python3',
            'arguments': ['$RP_PILOT_SANDBOX/ollama_client.py', '-n', 10],
            'pre_exec': [
                'unset http_proxy',
                'unset https_proxy',
                'source %s/ve/bin/activate' % WORK_DIR,
            ]
        }))
    else:
        for _ in range((N_NODES - 1) * CPUS_PER_NODE):
            tds.append(rp.TaskDescription({
                'executable': 'python3',
                'arguments': ['$RP_PILOT_SANDBOX/ollama_client.py'],
                'pre_exec': [
                    'unset https_proxy',
                    'unset http_proxy',
                    'source %s/ve/bin/activate' % WORK_DIR,
                ]
            }))

    if WITH_PROBE_TASK:
        tmgr.submit_tasks(tds[0])
        tmgr.wait_tasks()

    tmgr.submit_tasks(tds)
    tmgr.wait_tasks()

    session.close(download=True)


if __name__ == '__main__':
    main()

