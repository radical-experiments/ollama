#!/bin/sh

export CAMPAIGN=local_llama

export N_NODES=1
export ZMQ_REQUESTS=$((1024 * 1))
export ZMQ_REQUESTS=$((32))
export ZMQ_DELAY_MS=-1

for services in 0001 0002 0004 0008 0016; do
    for clients in $services 0016; do
        true

# # ------------------------------------------------
#     done
# done
#
# for services in 0001 ; do
#     for clients in 0001 ; do
# # ------------------------------------------------

        if test "$clients" -lt "$services"; then
            echo "skip c $clients / s $services"
            continue
        fi
      # echo "run  c $clients / s $services"
        export ZMQ_CLIENTS="$clients"
        export ZMQ_SERVICES="$services"
        ./campaign.sh
    done
done

