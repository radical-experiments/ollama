#!/usr/bin/env python

__copyright__ = 'Copyright 2013-2016, http://radical.rutgers.edu'
__license__   = 'MIT'


import sys
import time
import pprint

from   collections       import defaultdict
from   matplotlib.lines  import Line2D
import matplotlib.pyplot as plt

import radical.utils     as ru
import radical.pilot     as rp
import radical.analytics as ra

from radical.analytics.utils import to_latex


# ----------------------------------------------------------------------------
#
plt.style.use(ra.get_mplstyle("radical_mpl"))


# ----------------------------------------------------------------------------
#
metrics = {'request_stop' : {ru.EVENT: 'request_stop' },
           'request_start': {ru.EVENT: 'request_start'},
          }
colors  = {'request_stop' : '#CC5555',
           'request_start': '#55CC55'}

c_colors = {'local_noop'  : '#5555CC',
            'local_llama'  : '#55CC55',
            'remote_noop' : '#CC5555',
            'remote_llama' : '#CC55CC'}


# ------------------------------------------------------------------------------
#
def plot_rates(src):

    sid     = src[:-5]
    stype   = 'radical'
    session = ra.Session.create(src, stype)

    # FIXME: adaptive sampling (100 bins over range?)
    data = {metric: session.rate(event=metrics[metric], sampling=4.0)
            for metric in metrics}

    fig, ax = plt.subplots(figsize=ra.get_plotsize(500))

    for metric in data:
        x = [e[0] for e in data[metric]]
        y = [e[1] for e in data[metric]]
        # FIXME: use cmap
        ax.plot(x, y, color=colors[metric], label=to_latex(metric))
      # ax.step(x, y, color=colors[metric], label=to_latex(metric),
      #               where='post', linewidth=2, alpha=0.8)

    ax.set_title(sid + ' rate', loc='center')
    ax.legend(to_latex(list(data.keys())))
    # FIXME: why is the x-axis label gone?
    plt.xlabel(to_latex('time [s]'))
    plt.ylabel(to_latex('rate (#requests / sec)'))

    fig.savefig('%s_rate.png' % sid)


# ------------------------------------------------------------------------------
#
def plot_scaling():

    idx_c = 0
    idx_s = 1
    idx_c = 2
    idx_t = 3


    # data elements: campaign, n_servers, n_clients, n_requests, duration, rate

    data = list()
    with open('zmq_stats.dat', 'r') as fin:
        for line in fin.readlines():
            if '#' in line:
                continue
            elems = line.split()
            data.append( [str(elems[0])]
                       + [int(val) for val in elems[1:3]]
                       + [float(elems[5])])

  # pprint.pprint(data)

    # first plots: scaling:
    #   - one plot per noop / llama
    #   - n_servers = variable
    #   - x-axis: n_servers
    #   - y-axis: rate
    #   - one line per n_clients
    #   - one color per campaign

    c_names = set([str(x[0]) for x in data])

    for plot_filter in ['noop', 'llama', 'local', 'remote']:

        bundles   = defaultdict(dict)
        fig, ax   = plt.subplots(figsize = ra.get_plotsize(300))
        patches   = list()
        labels    = list()
        annotated = None

      # print(plot_filter)
        plot_data = defaultdict(dict)
        for c_name in [n for n in c_names if plot_filter in n]:

          # print(c_name)
            plot_data[c_name] = [x for x in data if c_name == x[0]]

            server_counts = list(set([x[idx_s] for x in plot_data[c_name]]))
          # print('===', server_counts)

            cnt = 0
            for sc in sorted(server_counts):

                cnt += 1

                print('------------------------', c_name, sc)
              # pprint.pprint(plot_data[c_name])

                bundles[c_name][sc] = list()
                for x in plot_data[c_name]:
                    if sc == x[idx_s]:
                        bundles[c_name][sc].append([x[idx_c], x[idx_t]])

              # pprint.pprint(bundles[c_name][sc])

                ax.plot([x[0] for x in bundles[c_name][sc]],
                        [x[1] for x in bundles[c_name][sc]],
                        '-o',
                        color=c_colors[c_name])
                      # label='%s (%d servers)' % (c_name, sc))
                # annotate with n_clients
                last = bundles[c_name][sc][-1]
                if c_name not in ['remote_noop', 'local_noop']:
                    if      annotated \
                        and annotated is not True \
                        and 'llama' in annotated \
                        and 'llama' in c_name:
                        pass
                    else:
                        annotated = True
                        ax.annotate('   %4d' % sc, (last[0], last[1]), fontsize=10,
                                    xytext=(10, 0), textcoords='offset points',)

            patch = Line2D([0], [0], color=c_colors[c_name],
                           linewidth=3, linestyle='-')
            patches.append(patch)
            labels.append(c_name.replace('_', ' '))

            if annotated:
                annotated = c_name

      # pprint.pprint(bundles)

        ax.set_title('scaling (%s)' % plot_filter, loc='center')
        ax.legend(patches, labels)
        ax.set_yscale('log')
        plt.xlabel('n_clients')
        plt.ylabel('rate (\\#req/s)')
        fig.savefig('scaling_%s.png' % plot_filter, bbox_inches='tight')


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    if len(sys.argv) > 1:
        for src in sys.argv[1:]:
            print(src)
            plot_rates(src)

    plot_scaling()


# ------------------------------------------------------------------------------

