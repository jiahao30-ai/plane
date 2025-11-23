-- 先创建一个临时表或使用变量进行映射
UPDATE medicine
SET id = id - 100 
WHERE id >= 213;