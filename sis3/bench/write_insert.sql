\set uid random(1, 20000)
\set pid random(1, 100000)
INSERT INTO tasks (id, user_id, project_id, title, status, priority, due_date, created_at, updated_at)
VALUES (nextval('task_id_seq'), :uid, :pid, 'New task', 'todo', 2, current_date + 3, now(), now());
