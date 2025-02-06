#!/bin/sh

mkdir -p $CAMPAIGN

export SID="$CAMPAIGN.s$ZMQ_SERVICES.c$ZMQ_CLIENTS.r$ZMQ_REQUESTS.d$ZMQ_DELAY_MS"
export PFILE="$CAMPAIGN/zmq_base_${SID}.prof"
export XFILE="$CAMPAIGN/zmq_base_${SID}_rate.png"

echo
echo "====================================================================="
echo "sid $SID"
# skip if xfile exists
if ! test -f $PFILE; then
  # bash -il -c 'rp_kill'
    killall python3
    rm -rf *.log rp.session.*

    # make install-ve
    echo "run ------------------------------------------------------------------"
    echo "sid $SID"

    ./zmq_prof.py   # > /dev/null 2>&1
    rm *.log

    for f in $(find rp.session.* -name radical.zmq.prof); do
        echo "===> $f"
        grep -c request_start $f
        grep -c request_stop  $f
    done
    find rp.session.* -name radical.zmq.prof | xargs cat | sort -u >> $PFILE
    wc -l $PFILE
    grep -c request_start $PFILE
    grep -c request_stop  $PFILE

    exit
fi

# bash -il -c 'rp_kill'
killall python3
rm -rf *.log rp.session.*

# echo "$XFILE"
# if ! test -f $XFILE; then
#     echo "plot ----------------------------------------------------------------"
#     ./zmq_plot.py $PFILE
#   # sxiv $XFILE &
#     ls -la $PFILE $XFILE
#     echo "sid $SID"
# fi
# echo "====================================================================="

