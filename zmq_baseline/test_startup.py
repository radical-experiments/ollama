#!/usr/bin/env python3

import os
import sys
import time
import random

import numpy as np

import radical.pilot as rp
import radical.utils as ru


sid          = os.environ.get('SID')
n_nodes      = int(os.environ.get('N_NODES',        1))
n_services   = int(os.environ.get('ZMQ_SERVICES',   1))
n_clients    = int(os.environ.get('ZMQ_CLIENTS',    1))
r_per_client = int(os.environ.get('ZMQ_REQUESTS',   1))
r_delay      = float(os.environ.get('ZMQ_DELAY_MS', 0)) / 1000


# ------------------------------------------------------------------------------
#
def app():

    session = rp.Session()
    try:
        pmgr  = rp.PilotManager(session=session)
        tmgr  = rp.TaskManager(session=session)
        pd    = {'resource': 'local.localhost',
                 'runtime' : 120,
                 'nodes'   : n_nodes}
        pd    = {'resource': 'ncsa.delta',
                 'project' : 'bblj',
                 'nodes'   : n_nodes,
                 'runtime' : 10000}
        pdesc = rp.PilotDescription(pd)
        pilot = pmgr.submit_pilots(pdesc)
        tmgr.add_pilots(pilot)

        info = dict()

        if 'local' in sid:

            # run service tasks
            sds = list()
          # for i in range(n_services):
            for i in range(1):
                sd = rp.TaskDescription({'mode'          : rp.TASK_SERVICE,
                                         'uid'           : 'zmq_service.%04d' % i,
                                         'executable'     : __file__,
                                         'ranks': n_services, 
                                         'cores_per_rank': 1,
                                         'arguments'      : ['service', 1024 + i],
                                         'info_pattern'   : 'stdout:.*url: (.*)',
                                         'named_env'      : 'rp'})
                sds.append(sd)
            services = tmgr.submit_tasks(sds)

            for serv in services:
                info[serv.uid] = serv.wait_info()
                print(' * %s: %s' % (serv.uid, info[serv.uid]))

        elif 'remote' in sid:

            # use remote services
            for i in range(n_services):
                uid = 'zmq_service.%04d' % i
                port = 10001 + i
                url  = 'tcp://95.217.193.116:%d' % port
                info[uid] = url

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------
#
def service(port):

    use_traces = True

    uid  = os.environ.get('RP_TASK_ID')
    url  = os.environ.get('OLLAMA_URL')
    prof = ru.Profiler('radical.zmq')

    assert uid, 'must run as RP task'

    if use_traces:

        if r_delay:
            seed = iter([r_delay])
        else:
            def get_seed():
                rgen  = np.random.default_rng()
                seeds = rgen.normal(4.44, 0.55, size=5_000)
                while True:
                    seed = max(random.choice(seeds), 2.22)
                    yield float(seed)
            seed = get_seed()

    else:

        import ollama
        oll_ep = ollama.Client(host=url)
        prompt = {'role'   : 'user',
                  'stream' : False,
                  'content': 'echo "Hello, World!"'}

    def hello(arg: str) -> str:

        prof.prof('hello_start', uid=uid)

        if use_traces:
            delay = next(seed)
            time.sleep(delay)
        else:
            start = time.time()
            oll_ep.chat(model='llama-8b', messages=[prompt])
            delay = time.time() - start

        ret = 'hello %s: %7.2f' % (arg, delay)
        prof.prof('hello_stop',  uid=uid)
        return ret

    serv = ru.zmq.Server(url='tcp://*:%d' % int(port))
    serv.register_request('hello', hello)
    serv.start()

    sys.stdout.write('url: %s\n' % serv.addr)
    sys.stdout.flush()

    serv.wait()


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    mode = sys.argv[1] if len(sys.argv) > 1 else 'app'
    marg = sys.argv[2] if len(sys.argv) > 2 else None

    if   mode == 'app'    : app()
    elif mode == 'service': service(port=marg)
    else: raise ValueError('unknown mode %s' % mode)


# ------------------------------------------------------------------------------

