#!/usr/bin/env python3

import radical.analytics as ra
import radical.utils     as ru

import matplotlib.pyplot as plt

rate = {
       'request_start': {ru.EVENT: 'request_start'},
       'request_stop' : {ru.EVENT: 'request_stop' },
}

colors = {'request_start': '#CC5555',
          'request_stop':  '#55CC55'}

plt.style.use(ra.get_mplstyle("radical_mpl"))


# ------------------------------------------------------------------------------
#
def plot_rates(session):

    data = dict()
    for metric in rate:
        data[metric] = session.rate(event=rate[metric], sampling=60.0)

    # prep figure
    fig  = plt.figure(figsize=(6,3))
    ax   = fig.add_subplot(111)

    for metric in data:
        x = [e[0] for e in data[metric]]
        y = [e[1] for e in data[metric]]
        x0 = min(x)
        x = [i - x0 for i in x]

        plt.step(x, y, color=colors[metric], label=metric, where='post',
                linewidth=2, alpha=0.8)

    ax.legend(list(data.keys()), ncol=3, loc='upper center',
                                 bbox_to_anchor=(0.5,1.11))
    plt.xlabel('time [s]')
    plt.ylabel('rate (\#requests / sec)')

    fig.savefig('%s_rates.png' % session.uid)


# ------------------------------------------------------------------------------
#
def main():

  with open('radical.ollama.prof', 'r') as fin:
      with open('tmp.prof', 'w') as fout:

          for i,line in enumerate(fin.readlines()):

            # if i > 1000:
            #     break

            # if line.startswith('#'): continue
              if 'sync' in line      : continue

              time, event, comp, thread, uid, state, msg = line.split(',')
              msg = msg.replace('\n', '')
              uid = uid.replace('_', '.')
              msg = msg.replace('_', '.')

              fout.write('%s,%s,%s,%s,%s,%s,%s,%s\n'
                         % (time, event, comp, uid, msg or uid, 'ACTIVE', msg, ''))

  # Load the Ollama session
  session = ra.Session(src='tmp.prof', stype='radical')
  plot_rates(session)


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    main()


# ------------------------------------------------------------------------------

