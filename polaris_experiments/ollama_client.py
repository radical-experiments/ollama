
import argparse
import os
import sys

import radical.utils as ru

from langchain_community.llms import Ollama

PROMPTS = [
    'Roger has 5 tennis balls. He buys 2 more cans of tennis balls. '
    'Each can has 3 tennis balls. How many tennis balls does he have now?',
    'The cafeteria had 23 apples. If they used 20 to make lunch and '
    'bought 6 more, how many apples do they have?'
]


def get_args():
    parser = argparse.ArgumentParser(
        description='Configure ollama client',
        usage='ollama_client.py [<options>]')
    parser.add_argument(
        '-n', '--num_prompts',
        dest='num_prompts',
        type=int,
        required=False)
    return parser.parse_args(sys.argv[1:])


def main(num_prompts=None):
    num_prompts = num_prompts or len(PROMPTS)
    prompts = (PROMPTS * ((num_prompts + 1) // len(PROMPTS)))[:num_prompts]

    uid = os.getenv('RP_TASK_ID')
    prof = ru.Profiler(name=uid, ns='radical.pilot', path=os.getcwd())

    reg_addr = os.getenv('RP_REGISTRY_ADDRESS')
    reg = ru.zmq.RegistryClient(url=reg_addr)

    while True:
        ollama_addr = reg['ollama.addr']
        if ollama_addr:
            reg.close()
            break

    prof.prof('ollama_init_start', uid=uid)
    ollama = Ollama(base_url=ollama_addr,
                    model='llama3')
    prof.prof('ollama_init_stop', uid=uid)

    prof.prof('ollama_req_start', uid=uid)
    for idx, prompt in enumerate(prompts):
        prof.prof('ollama_prompt_start', uid=uid)
        res = ollama.invoke(prompt)
        msg = f'prompt:{idx}|||{len(res)}|||{res}'
        print(msg)
        prof.prof('ollama_prompt_stop', uid=uid, msg=msg)
    prof.prof('ollama_req_stop', uid=uid)


if __name__ == '__main__':
    args = get_args()
    main(args.num_prompts)

