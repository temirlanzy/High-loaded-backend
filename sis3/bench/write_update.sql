\set id random(1, 3000000)
UPDATE tasks SET status = 'done', updated_at = now() WHERE id = :id;
