#!/bin/bash
# usage: stage.sh LABEL READ_PORT WRITE_PORT [EXPLAIN_PORT]  (60 s benchmark + EXPLAIN ANALYZE capture)
L=$1; RP=$2; WP=$3; EP=${4:-$RP}
cd /home/claude/sis3
runuser -u postgres -- psql -h /tmp -p $EP -d todo -X -f sql/explain.sql > results/explain_$L.txt 2>&1
./bench/run.sh $L $RP $WP 60 32 8 
