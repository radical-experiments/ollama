#!/usr/bin/env python3

import time
import radical.pilot as rp


if __name__ == '__main__':

    session = rp.Session()
    try:

        pmgr  = rp.PilotManager(session=session)
        tmgr  = rp.TaskManager(session=session)
        pdesc = rp.PilotDescription({'resource': 'local.localhost',
                                     'runtime' : 1024 * 1024,
                                     'nodes'   : 10})
        pilot = pmgr.submit_pilots(pdesc)
        tmgr.add_pilots(pilot)

      # pilot.prepare_env('ollama_env', {'type'    : 'venv',
      #                                  'path'    : '/tmp/ve_ollama',
      #                                  'setup'   : ['ollama', 'radical.pilot',
      #                                               '/home/merzky/j/rp'],
      #                                 })

        # ollama instances need ports assigned manually
        port = 11000
        host = 'localhost'
        sds  = list()
        for i in range(2):
            pat   = '.*Listening on ([0-9:\\.]*).*'
            sd    = rp.TaskDescription(
                    {'uid'         : 'ollama_%03d' % i,
                     'mode'        : rp.TASK_SERVICE,
                     'executable'  : '/home/merzky/j/ollama/ollama',
                     'arguments'   : ['start'],
                     'environment' : {'OLLAMA_HOST': '%s:%s' % (host, port)},
                     'timeout'     : 10,  # startup timeout
                     'info_pattern': 'stderr:%s' % pat,
                     'named_env'   : 'rp'})
            sds.append(sd)
            port += 1

        ollamas = tmgr.submit_tasks(sds)

        for task in ollamas:
            print(task.uid, task.wait_info())

        pat = 'Running on (.*)'
        td = rp.TaskDescription({'uid'         : 'load_balancer',
                                 'mode'        : rp.TASK_SERVICE,
                                 'executable'  : 'radical-pilot-http-balancer',
                                 'arguments'   : [o.info for o in ollamas],
                                 'info_pattern': 'stderr:%s' % pat,
                                 'timeout'     : 10,
                                 'named_env'   : 'rp'})
        balancer = tmgr.submit_tasks(td)
        print(balancer.uid, balancer.wait_info())

        n   = 2
        tds = list()
        for _ in range(n):
            td  = rp.TaskDescription({'executable' : '/home/merzky/j/rp/ollama_client.py',
                                      'services'   : [balancer.uid],
                                      'ranks'      : 1,
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

