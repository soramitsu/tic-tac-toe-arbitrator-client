docker-compose down
docker volume rm $(docker volume ls -q | grep deploy)
docker network rm $(docker network ls | grep net | cut -d' ' -f1)

