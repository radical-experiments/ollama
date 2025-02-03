
mkdir -p $CAMPAIGN

export SID="$CAMPAIGN.s$ZMQ_SERVICES.c$ZMQ_CLIENTS.r$ZMQ_REQUESTS.d$ZMQ_DELAY_MS"
export PFILE="$CAMPAIGN/zmq_base_${SID}.prof"
export XFILE="$CAMPAIGN/zmq_base_${SID}_rate.png"

echo
echo "====================================================================="
echo "sid $SID"
# skip if xfile exists
if ! test -f $PFILE; then
  # rp_kill
    killall python3 > /dev/null 2>&1
    rm -rf *.log rp.session.*

    # make install-ve
    echo "run ------------------------------------------------------------------"
    echo "sid $SID"

    ./zmq_prof.py > /dev/null 2>&1
    rm *.log

    for f in $(find rp.session.* -name radical.zmq.prof); do
        echo "===> $f"
    done
    find rp.session.* -name radical.zmq.prof | xargs cat | sort -un > $PFILE
    wc -l $PFILE

fi

echo "$XFILE"
if ! test -f $XFILE; then
    echo "plot ----------------------------------------------------------------"
    ./zmq_plot.py $PFILE
  # sxiv $XFILE &
    ls -la $PFILE $XFILE
    echo "sid $SID"
fi
echo "====================================================================="

