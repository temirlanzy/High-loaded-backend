#!/bin/bash
# Streaming replica on port 5433 (hot standby) cloned from the primary on 5432. Run as root.
set -e
BIN=/usr/lib/postgresql/16/bin; ROOT=/var/lib/sis3
rm -rf $ROOT/replica
runuser -u postgres -- $BIN/pg_basebackup -h 127.0.0.1 -p 5432 -D $ROOT/replica -R -X stream -c fast
cat >> $ROOT/replica/postgresql.conf <<EOC
port = 5433
hot_standby_feedback = on
shared_buffers = 1GB
EOC
runuser -u postgres -- $BIN/pg_ctl -D $ROOT/replica -l $ROOT/replica.log -w start
