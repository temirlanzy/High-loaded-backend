#!/bin/bash
# Creates primary (5432) and streaming replica (5433). Run as root.
set -e
BIN=/usr/lib/postgresql/16/bin
ROOT=/var/lib/sis3
rm -rf $ROOT; mkdir -p $ROOT; chown postgres:postgres $ROOT
runuser -u postgres -- $BIN/initdb -D $ROOT/primary -A trust >/dev/null
cat /home/claude/sis3/conf/primary_extra.conf >> $ROOT/primary/postgresql.conf
echo "host replication all 127.0.0.1/32 trust" >> $ROOT/primary/pg_hba.conf
runuser -u postgres -- $BIN/pg_ctl -D $ROOT/primary -l $ROOT/primary.log -w start
runuser -u postgres -- psql -h /tmp -p 5432 -c "CREATE DATABASE todo" 
echo primary up
