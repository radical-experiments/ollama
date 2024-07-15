#!/usr/bin/env python3

import os
import sys
import ollama

import radical.utils as ru
import threading     as mt

n_threads  = 2
n_requests = 2

prof = ru.Profiler('radical.ollama')
url  = os.environ.get('RP_INFO_LOAD_BALANCER')

assert url, 'OLLAMA_URL not set'
print('url: %s' % url)


# ------------------------------------------------------------------------------
#
def work(tid):
    client = ollama.Client(host=url)
    prompt = {'role'   : 'user',
              'stream' : False,
              'content': 'echo "Hello, World!"'}

    try:
        for i in range(n_requests):
            prof.prof('request_start', uid=tid, msg='request_%06d' % i)
            response = client.chat(model='llama3', messages=[prompt])
            rep = response['message']['content']
            print('%d: %d' % (i, len(rep)))
            prof.prof('request_stop', uid=tid, msg='request_%06d' % i)

    except Exception as e:
        sys.stdout.write('ERROR: %s\n' % e)
        sys.stdout.flush()


# ------------------------------------------------------------------------------
#
def main():

    threads = list()

    for n in range(n_threads):
        tid = 'thread_%03d' % n

        print('start thread %s' % tid)

        prof.prof('threads_start', uid=tid)
        t = mt.Thread(target=work, args=[tid])
        t.start()
        threads.append(t)

    print('threads started')

    for t in threads:
        t.join()

    print('threads joined')


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    main()


# ------------------------------------------------------------------------------

