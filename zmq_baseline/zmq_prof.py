#!/usr/bin/env python3

import os
import sys
import time

import radical.pilot as rp
import radical.utils as ru


n_nodes      = int(os.environ.get('N_NODES',        1))
n_services   = int(os.environ.get('ZMQ_SERVICES',   1))
n_clients    = int(os.environ.get('ZMQ_CLIENTS',    1))
r_per_client = int(os.environ.get('ZMQ_KREQUESTS',  1)) * 1024
r_delay      = float(os.environ.get('ZMQ_DELAY_MS', 0)) / 1000


# ------------------------------------------------------------------------------
#
def app():

    session = rp.Session()
    try:
        pmgr  = rp.PilotManager(session=session)
        tmgr  = rp.TaskManager(session=session)
        pdesc = rp.PilotDescription({'resource': 'local.localhost',
                                     'runtime' : 15,
                                     'nodes'   : n_nodes})
        pilot = pmgr.submit_pilots(pdesc)
        tmgr.add_pilots(pilot)

        # ---------------------------------------------------------------------
        # run service
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

        info = dict()
        for service in services:
            info[service.uid] = service.wait_info()
            print(' * %s: %s' % (service.uid, info[service.uid]))


        # ---------------------------------------------------------------------
        # run clients
        cds = list()
        for i in range(n_clients):
            service = services[i % n_services]
            arg = info[service.uid]
            cd = rp.TaskDescription({'uid'       : 'zmq_client.%04d' % i,
                                     'services'  : [service.uid],
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

    uid  = os.environ['RP_TASK_ID']
    prof = ru.Profiler('radical.zmq')

    def hello(arg: str) -> str:
        prof.prof('hello_start', uid=uid)
        if r_delay: time.sleep(r_delay)
        ret = 'hello ' + arg
        prof.prof('hello_stop',  uid=uid)
        return ret

    service = ru.zmq.Server(url='tcp://*:%d' % int(port))
    service.register_request('hello', hello)
    service.start()

    sys.stdout.write('url: %s\n' % service.addr)
    sys.stdout.flush()

    service.wait()


# ------------------------------------------------------------------------------
#
def client(url):

    uid    = os.environ['RP_TASK_ID']
    client = ru.zmq.Client(url=url)
    prof   = ru.Profiler('radical.zmq')

    for i in range(r_per_client):
        prof.prof('request_start', uid=uid, msg=i)
        client.request(cmd='hello', arg='world %d' % i)
        prof.prof('request_stop', uid=uid, msg=i)


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    mode = sys.argv[1] if len(sys.argv) > 1 else 'app'
    arg  = sys.argv[2] if len(sys.argv) > 2 else None

    if   mode == 'app'    : app()
    elif mode == 'service': service(port=arg)
    elif mode == 'client' : client(url=arg)
    else: raise ValueError('unknown mode %s' % mode)


# ------------------------------------------------------------------------------

