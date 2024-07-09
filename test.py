#!/usr/bin/env python3

import sys

import radical.pilot as rp


if __name__ == '__main__':

    session = rp.Session()
    try:

        pmgr  = rp.PilotManager(session=session)
        tmgr  = rp.TaskManager(session=session)
        pdesc = rp.PilotDescription({'resource': 'local.localhost',
                                     'runtime' : 1024 * 1024,
                                     'nodes'   : 1})
        pilot = pmgr.submit_pilots(pdesc)
        tmgr.add_pilots(pilot)

      # pmgr.wait_pilots(state=[rp.PMGR_ACTIVE])
      # pilot.prepare_env('ollama_env', {'type' : 'virtenv',
      #                                  'setup': ['ollama', 'radical.pilot']})


        pat = '.*Listening on \([0-9:\.]*\).*'
        sd  = rp.TaskDescription({'mode'        : rp.TASK_SERVICE,
                                  'name'        : 'ollama',
                                  'info_pattern': 'stdout:%s' % pat,
                                  'timeout'     : 10,  # startup timeout
                                  'executable'  : '/home/merzky/j/ollama/ollama',
                                  'arguments'   : ['start'],
                                  'named_env'   : 'rp'})
        service = tmgr.submit_tasks(sd)
        import time
        time.sleep(10)


        n   = 1
        tds = list()
        for _ in range(n):
            td  = rp.TaskDescription({'executable': '/home/merzky/j/ollama/client.py',
                                      'named_env' : 'rp',
                                      'services'  : ['ollama'],
                                      'ranks'     : 1})
            tds.append(td)

        tasks = tmgr.submit_tasks(tds)

        tmgr.wait_tasks(uids=[t.uid for t in tasks])

        for task in tasks:
            print('STDOUT: %s' % task.stdout)

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------

