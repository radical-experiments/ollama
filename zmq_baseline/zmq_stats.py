#!/usr/bin/env python3

import os
import sys
import glob
import radical.utils as ru

dirs = ['local_zero', 'local_seed', 'remote_zero', 'remote_seed']

sys.exit()

with open('zmq_stats.dat', 'w') as fout:

    tmp = '# %18s %4s %4s %12s %12s %12s' \
        % ('campaign', 'n_s', 'n_c', 'n_req', 't_diff', 'rate')
    fout.write('%s\n' % tmp)
    print(tmp)

    for d in dirs:
        for f in sorted(list(glob.glob('%s/*.prof' % d))):

            prof   = ru.read_profiles([f])
            sid    = list(prof.keys())[0]
            events = prof[sid]

            elems = sid.split('.')
            campaign   = elems[0].split('/')[0]
            n_services = int(elems[1][1:])
            n_clients  = int(elems[2][1:])

          # print(f)
          # print(sid, elems, campaign, n_services, n_clients)

            starts = [e[0] for e in events if e[1] == 'request_start']
            stops  = [e[0] for e in events if e[1] == 'request_stop']

            t_min  = min(starts)
            t_max  = max(stops)
            t_diff = t_max - t_min
            rate   = len(starts) / t_diff

            tmp = '%20s %4d %4d %12d %12.2f %12.2f' \
                % (campaign, n_services, n_clients, len(starts), t_diff, rate)
            fout.write('%s\n' % tmp)
            print(tmp)

        print()




