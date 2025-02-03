#!/usr/bin/env python3

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

    t_start = session.t_start
    t_stop  = session.t_stop
    print(t_start, t_stop)
    for entity in session.get():
        for event in entity.events:
            event[ru.TIME] -= t_start

    # FIXME: adaptive sampling (100 bins over range?)
    data = {metric: session.rate(event=metrics[metric], sampling=1.0)
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
    ax.set_ylim(bottom=0)
    # FIXME: why is the x-axis label gone?
    plt.xlabel(to_latex('time [s]'))
    plt.ylabel(to_latex('rate (#inferences / sec)'))

    fig.savefig('%s_rate.png' % sid)


# ------------------------------------------------------------------------------
#
def plot_scaling():

    idx_c = 0
    idx_s = 1
    idx_c = 2
    idx_t = 3


    # data elements: campaign, n_servers, n_tasks, n_requests, duration, rate

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
    #   - one line per n_tasks
    #   - one color per campaign

    c_names = set([str(x[0]) for x in data])

    for plot_filter in ['noop', 'llama', 'local', 'remote']:

        bundles   = defaultdict(dict)
        fig, ax   = plt.subplots(figsize = ra.get_plotsize(200))
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
                # annotate with n_tasks
                last = bundles[c_name][sc][-1]
                if c_name not in ['remote_noop', 'local_noop']:
                    if      annotated \
                        and annotated is not True \
                        and 'llama' in annotated \
                        and 'llama' in c_name:
                        pass
                    else:
                        annotated = True
                        ax.annotate('   %4d services' % sc, (last[0], last[1]),
                                    fontsize=10, xytext=(10, 0),
                                    textcoords='offset points',)

            patch = Line2D([0], [0], color=c_colors[c_name],
                           linewidth=3, linestyle='-')
            patches.append(patch)
            labels.append(c_name.replace('_', ' '))

            if annotated:
                annotated = c_name

      # title = 'scaling'  #  (%s)' % plot_filter
      # plt.suptitle(title, y=1.02, fontsize=12)
      # plt.title('one line per [n] service instances', fontsize=8)

        ax.legend(patches, labels)
        ax.set_xscale('log')
        ax.set_xticks(ticks=[1, 2, 4, 8, 16],
                      labels=[1, 2, 4, 8, 16],
                      fontsize=10)
        ax.set_yscale('log')
        ax.set_yticks([0.1, 1, 10], [0.1, 1, 10], fontsize=10)
        plt.ylim([0.1, 10])
        plt.xlabel('n_tasks', fontsize=10)
        plt.ylabel('rate (\\#inferences / sec)', fontsize=10)
        fig.savefig('scaling_%s.pdf' % plot_filter, bbox_inches='tight')


        if plot_filter in ['noop']:

            fig2, ax2   = plt.subplots(figsize = ra.get_plotsize(300))
            patches   = list()
            labels    = list()

            local_data  = list()
            remote_data = list()

            for i in bundles['local_noop']:
                for dat in bundles['local_noop'][i]:
                    if dat[0] == i:
                        local_data.append(dat)
                        break

            for i in bundles['remote_noop']:
                for dat in bundles['remote_noop'][i]:
                    if dat[0] == i:
                        remote_data.append(dat)
                        break

            ax2.plot([x[0] for x in local_data],
                     [x[1] for x in local_data],
                     '-o', color=c_colors['local_noop'],
                           label='local_noop')
            ax2.plot([x[0] for x in remote_data],
                     [x[1] for x in remote_data],
                     '-o', color=c_colors['remote_noop'],
                           label='remote_noop')

            title = 'weak scaling (%s)' % plot_filter
            plt.suptitle(title, y=1.02, fontsize=12)
            plt.title('n_services == 1', fontsize=8)

            ax2.legend()
            ax2.set_yscale('log')
            plt.xlabel('n_tasks')
            plt.ylabel('rate (\\#inferences / sec)')
            fig2.savefig('weak_scaling_%s.png' % plot_filter, bbox_inches='tight')



            fig3, ax3   = plt.subplots(figsize = ra.get_plotsize(300))
            patches   = list()
            labels    = list()

            local_data  = list()
            remote_data = list()

            for dat in bundles['local_noop'][1]:
                local_data.append(dat)

            for dat in bundles['remote_noop'][1]:
                remote_data.append(dat)

            ax3.plot([x[0] for x in local_data],
                     [x[1] for x in local_data],
                     '-o', color=c_colors['local_noop'],
                           label='local_noop')
            ax3.plot([x[0] for x in remote_data],
                     [x[1] for x in remote_data],
                     '-o', color=c_colors['remote_noop'],
                           label='remote_noop')

            title = 'strong scaling (%s)' % plot_filter
            plt.suptitle(title, y=1.02, fontsize=12)
            plt.title('n_services == n_tasks', fontsize=8)

            ax3.legend()
            ax3.set_yscale('log')
            plt.xlabel('n_tasks')
            plt.ylabel('rate (\\#inferences / sec)')
            fig3.savefig('strong_scaling_%s.png' % plot_filter, bbox_inches='tight')


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    if len(sys.argv) > 1:
        for src in sys.argv[1:]:
            print('---->', src)
            plot_rates(src)

    else:
        plot_scaling()


# ------------------------------------------------------------------------------

