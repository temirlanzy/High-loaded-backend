-- 20k users, 100k projects, 50 tags, 3M tasks over 24 months (ids grow with time, like real inserts)
INSERT INTO users SELECT g, 'user'||g||'@mail.test', now() - (random()*730)*interval '1 day' FROM generate_series(1,20000) g;
INSERT INTO projects SELECT g, 1+(random()*19999)::int, 'Project '||g, now() - (random()*730)*interval '1 day' FROM generate_series(1,100000) g;
INSERT INTO tags SELECT g, 'tag'||g FROM generate_series(1,50) g;
INSERT INTO tasks
SELECT g,
       1+(random()*19999)::int,
       1+(random()*99999)::int,
       'Task '||g||' '||md5(g::text),
       (ARRAY['todo','todo','doing','done','done','done','done'])[1+(random()*6)::int],
       1+(random()*4)::int,
       (ts::date + (random()*30)::int),
       ts,
       ts
FROM (SELECT g, timestamptz '2024-11-29' + (g/3000000.0)*interval '729 days' AS ts FROM generate_series(1,3000000) g) s;
INSERT INTO task_tags
SELECT DISTINCT t.id, 1+(random()*49)::int FROM tasks t, generate_series(1,2) k WHERE random() < 0.8;
ANALYZE;
