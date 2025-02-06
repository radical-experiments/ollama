#!/usr/bin/env python3

import os
import sys
import time
import random
import ollama

import numpy as np

import radical.pilot as rp
import radical.utils as ru


sid          = os.environ.get('SID')
n_nodes      = int(os.environ.get('N_NODES',         1))
n_services   = int(os.environ.get('ZMQ_SERVICES',    1))
n_clients    = int(os.environ.get('ZMQ_CLIENTS',     1))
r_per_client = int(os.environ.get('ZMQ_REQUESTS',    1))
r_delay      = float(os.environ.get('ZMQ_DELAY_MS', -1)) / 1000


# ------------------------------------------------------------------------------
#
def rand(center, sigma):

    return max(0, random.gauss(center, sigma))


# ------------------------------------------------------------------------------
#
def app():

    session = rp.Session()
    try:
        pmgr  = rp.PilotManager(session=session)
        tmgr  = rp.TaskManager(session=session)
        pdesc = rp.PilotDescription({'resource': 'local.localhost',
                                     'runtime' : 120,
                                     'nodes'   : n_nodes})
        pilot = pmgr.submit_pilots(pdesc)
        tmgr.add_pilots(pilot)

        info = dict()

      # if 'local' in sid:
        if True:

            # run service tasks
            sds = list()
            for i in range(n_services):
                sd = rp.TaskDescription({'mode'          : rp.TASK_SERVICE,
                                         'uid'           : 'zmq_service.%04d' % i,
                                         'executable'     : __file__,
                                         'arguments'      : ['service', 1024 + i],
                                         'info_pattern'   : 'stdout:.*url: (.*)',
                                         'named_env'      : 'rp'})
                sds.append(sd)
            services = tmgr.submit_tasks(sds)

            for serv in services:
                info[serv.uid] = serv.wait_info()
                print(' * %s: %s' % (serv.uid, info[serv.uid]))

      # elif 'remote' in sid:
      #
      #     # use remote services
      #     for i in range(n_services):
      #         uid = 'zmq_service.%04d' % i
      #         port = 10001 + i
      #         url  = 'tcp://95.217.193.116:%d' % port
      #         info[uid] = url


        # ---------------------------------------------------------------------
        # run clients
        cds = list()
        for i in range(n_clients):
            uid = list(info.keys())[i % n_services]
            arg = info[uid]
            cd = rp.TaskDescription({'uid'       : 'zmq_client.%04d' % i,
                                     'services'  : [uid],
                                     'executable': __file__,
                                     'arguments' : ['client', arg]})
            cds.append(cd)

        clients = tmgr.submit_tasks(cds)
        tmgr.wait_tasks(uids=[client.uid for client in clients])

    finally:
        session.close(download=True)


# ------------------------------------------------------------------------------
#
def service(port):

    use_traces = bool(r_delay < 0)

    uid  = os.environ.get('RP_TASK_ID')
    url  = os.environ.get('OLLAMA_URL')
    prof = ru.Profiler('radical.zmq')

    assert uid, 'must run as RP task'

    oll_ep = None
    prompt = None

    print(use_traces, r_delay)

    if not use_traces:

        oll_ep = ollama.Client(host=url)
        prompt = {'role'   : 'user',
                  'stream' : False,
                  'content': 'echo "Hello, World!"'}
        oll_ep = None


    def hello(arg: str, *args, **kwargs) -> str:
        prof.prof('hello_start', uid=uid)

        if oll_ep:
            start = time.time()
            oll_ep.chat(model='llama-8b', messages=[prompt])
            delay = time.time() - start

        else:
            if r_delay > 0:
                time.sleep(r_delay)
                delay = r_delay
            else:
                delay = rand(4.44, 0.55)
                time.sleep(delay)

        ret = 'hello %s: %7.2f' % (arg, delay)
        prof.prof('hello_stop',  uid=uid)
        return ret

    serv = ru.zmq.Server(url='tcp://*:%d' % int(port), prof=prof)
    serv.register_request('hello', hello)
    serv.start()

    sys.stdout.write('url: %s\n' % serv.addr)
    sys.stdout.flush()

    serv.wait()
    prof.close()


# ------------------------------------------------------------------------------
#
def client(url):

    uid  = os.environ['RP_TASK_ID']
    cli  = ru.zmq.Client(url=url)
    prof = ru.Profiler('radical.zmq')

    for i in range(r_per_client):
        rid = 'reg.%s.%08d' % (uid, i)
        prof.prof('request_start', uid=rid, msg=i)
      # time.sleep(rand(0.047, 0.040) / 2)

        rep = cli.request(cmd='hello', arg='world %d' % i, uid=rid)

      # time.sleep(rand(0.047, 0.040) / 2)
        prof.prof('request_stop', uid=rid, msg=rep)

    prof.close()


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    mode = sys.argv[1] if len(sys.argv) > 1 else 'app'
    marg = sys.argv[2] if len(sys.argv) > 2 else None

    if   mode == 'app'    : app()
    elif mode == 'service': service(port=marg)
    elif mode == 'client' : client(url=marg)
    else: raise ValueError('unknown mode %s' % mode)


# ------------------------------------------------------------------------------

