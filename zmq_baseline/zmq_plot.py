#!/usr/bin/env python

__copyright__ = 'Copyright 2013-2016, http://radical.rutgers.edu'
__license__   = 'MIT'


import sys

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


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("\n\tusage: %s <profile>\n" % sys.argv[0])
        sys.exit(1)

    src     = sys.argv[1]
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

