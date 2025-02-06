#!/bin/sh

export OLLAMA_NUM_PARALLEL=3
export OLLAMA_NOPRUNE=true
export OLLAMA_TMPDIR=/tmp

./bin/ollama start

