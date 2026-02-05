# algo_contest_platform
Платформа для проведения алгоритмических контестов, вдохновленная Leetcode и Codeforces. Позволяет пользователям соревноваться, решать задачи и создавать собственные задачи с автоматической проверкой кода.

Технологический стек: FastAPI, PostgreSQL, Keycloak, RabbitMQ, React.js, Krakend.

[demo](https://drive.google.com/file/d/1TQxG2UOXatZCHUaR-tiadEH7BxdVIhF4/view?usp=sharing)

## Шаги для запуска
```
git clone https://github.com/111zxc/algo_contest_platform
cd .\algo_contest_platform\
cp ./services/tester_service/.env.example ./services/tester_service/.env
cp ./services/content_service/.env.example ./services/content_service/.env
docker-compose up -d
```
