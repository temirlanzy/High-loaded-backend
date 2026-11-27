# SIS #3 — тюнинг БД (To-Do, PostgreSQL 16)

Порядок воспроизведения (Ubuntu 24.04, root, PostgreSQL 16 и PgBouncer установлены):

```bash
./setup_cluster.sh                                   # основной сервер :5432, база todo
P="runuser -u postgres -- psql -h /tmp -p 5432 -d todo -v ON_ERROR_STOP=1 -q"
$P -f sql/01_schema_baseline.sql                     # схема без индексов
$P -f sql/02_seed.sql                                # 3 млн задач
$P -c "CREATE SEQUENCE task_id_seq START 3000001" -c "VACUUM (ANALYZE)" -c "CHECKPOINT"

./bench/stage.sh S0_baseline 5432 5432               # замер «до» + EXPLAIN ANALYZE

$P -f sql/03_indexes.sql                             # S1: индексы
./bench/stage.sh S1_indexes 5432 5432

$P -f sql/04_partitioning.sql                        # S2a: RANGE по created_at
./bench/stage.sh S2_partitioning 5432 5432
$P -f sql/04b_partition_hash.sql                     # S2b: HASH по user_id (используется дальше)
./bench/stage.sh S2b_hash 5432 5432

./setup_replica.sh                                   # S3: реплика :5433
./bench/stage.sh S3_replica 5433 5432 5432           # чтения на реплику, запись на основной

# S4: PgBouncer :6432 (conf/pgbouncer.ini и conf/userlist.txt скопировать в /var/lib/sis3/)
runuser -u postgres -- pgbouncer -d /var/lib/sis3/pgbouncer.ini
RDB=todo_ro WDB=todo ./bench/run.sh S4_pgbouncer 6432 6432 60 32 8
```

Параметры `run.sh`: `LABEL READ_PORT WRITE_PORT SECONDS READ_CLIENTS WRITE_CLIENTS`.
Перцентили p50/p95/p99 считает `bench/stats.py` по логам `pgbench -l`
(результат — `results/<LABEL>.json`). Планы EXPLAIN ANALYZE — `results/explain_<LABEL>.txt`.

Эксперименты по пулингу: `results/P1_connect.txt` (`pgbench -C`, `SELECT 1`),
`results/P2_manyclients.txt` (250 клиентов напрямую и через PgBouncer).
