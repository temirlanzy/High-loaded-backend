#!/bin/bash
# usage: run.sh LABEL READ_PORT WRITE_PORT SECONDS READ_CLIENTS WRITE_CLIENTS [extra pgbench flags]
L=$1; RP=$2; WP=$3; T=$4; RC=$5; WC=$6; shift 6
cd /home/claude/sis3; rm -f results/${L}_read.* results/${L}_write.*
COMMON="-h 127.0.0.1 -U postgres -n -M simple -j 1 -T $T -l $*"
pgbench $COMMON -p $RP -c $RC --log-prefix results/${L}_read \
  -f bench/read_list.sql@35 -f bench/read_overdue.sql@20 -f bench/read_tag.sql@15 -f bench/read_report.sql@10 ${RDB:-todo} > results/${L}_read.out 2>&1 &
pgbench $COMMON -p $WP -c $WC -R 300 --log-prefix results/${L}_write \
  -f bench/write_insert.sql@1 -f bench/write_update.sql@1 ${WDB:-todo} > results/${L}_write.out 2>&1 &
wait
python3 bench/stats.py $L
