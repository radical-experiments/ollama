#!/usr/bin/env python3

import radical.pilot as rp

BASE   = '/home/merzky/j/ollama'
OLLAMA = '%s/ollama'                % BASE
CLIENT = '%s/test_ollama_client.py' % BASE

N_NODES               = 2
OLLAMA_RANKS_PER_NODE = 1
OLLAMA_GPUS_PER_RANK  = 1

CLIENTS_PER_NODE      = 1
RANKS_PER_CLIENT      = 2
THREADS_PER_CLIENT    = 1


if __name__ == '__main__':

    session = rp.Session()
    try:
        pmgr  = rp.PilotManager(session=session)
        tmgr  = rp.TaskManager(session=session)
        pdesc = rp.PilotDescription({'resource': 'local.localhost',
                                     'runtime' : 1024 * 1024,
                                     'nodes'   : N_NODES})
        pilot = pmgr.submit_pilots(pdesc)
        tmgr.add_pilots(pilot)

      # pilot.prepare_env('ollama_env', {'type'    : 'venv',
      #                                  'path'    : '/tmp/ve_ollama',
      #                                  'setup'   : ['ollama', 'radical.pilot',
      #                                               '/home/merzky/j/rp'],
      #                                 })

        # ollama instances need ports assigned manually
        getip = 'python3 -c "import radical.utils as ru; print(ru.get_hostip())"'
        pat   = '.*Listening on ([0-9:\\.]*).*'
        od    = rp.TaskDescription(
                {'uid'          : 'ollama',
                 'mode'         : rp.TASK_SERVICE,
                 'executable'   : OLLAMA,
                 'arguments'    : ['serve'],
                 'ranks'        : OLLAMA_RANKS_PER_NODE * N_NODES,
                 'gpus_per_rank': OLLAMA_GPUS_PER_RANK,
                 'pre_exec'     : [
                     'hostip=$(%s)' % getip,
                     'hostport=$((11000 + $RP_RANK))',
                     'export OLLAMA_HOST=$hostip:$hostport',
                     'echo $RP_RANK:$OLLAMA_HOST'],
                 'info_pattern' : 'stderr:%s' % pat,
                 'timeout'      : 10,  # startup timeout
                 'named_env'    : 'rp'})
        ollama = tmgr.submit_tasks(od)

        info = ollama.wait_info()
        urls = ','.join(info.values())
        print(urls)
        assert False

        pat = 'Running on (.*)'
        td = rp.TaskDescription({'uid'         : 'load_balancer',
                                 'mode'        : rp.TASK_SERVICE,
                                 'executable'  : 'radical-pilot-http-balancer',
                                 'arguments'   : [ollama.info],
                                 'info_pattern': 'stderr:%s' % pat,
                                 'timeout'     : 10,
                                 'named_env'   : 'rp'})
        balancer = tmgr.submit_tasks(td)
        print(balancer.uid, balancer.wait_info())

        tds = list()
        for _ in range(CLIENTS_PER_NODE * N_NODES):
            td  = rp.TaskDescription({'executable' : CLIENT,
                                      'services'   : [balancer.uid],
                                      'ranks'      : RANKS_PER_CLIENT,
                                      'named_env'  : 'rp'})
            tds.append(td)

        tasks = tmgr.submit_tasks(tds)
        tmgr.wait_tasks(uids=[t.uid for t in tasks])


        for task in tasks:
            print('STDOUT: %s' % task.stdout)
            print('STDERR: %s' % task.stderr)

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------

