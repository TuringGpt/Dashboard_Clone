-- Ensure schema_manager exists with the requested auth plugin and privileges
DROP USER IF EXISTS 'schema_manager'@'localhost';
DROP USER IF EXISTS 'schema_manager'@'%';

CREATE USER 'schema_manager'@'localhost' IDENTIFIED WITH mysql_native_password BY 'StrongPassword123!';
CREATE USER 'schema_manager'@'%' IDENTIFIED WITH mysql_native_password BY 'StrongPassword123!';

GRANT ALL PRIVILEGES ON *.* TO 'schema_manager'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO 'schema_manager'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;

-- Verify user/plugin (logged to init output)
SELECT user, host, plugin FROM mysql.user WHERE user = 'schema_manager';
