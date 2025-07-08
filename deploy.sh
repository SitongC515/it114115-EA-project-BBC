aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 141968719357.dkr.ecr.us-east-1.amazonaws.com
docker build -t project-bbc .
docker tag project-bbc:latest 141968719357.dkr.ecr.us-east-1.amazonaws.com/project-bbc:latest
docker push 141968719357.dkr.ecr.us-east-1.amazonaws.com/project-bbc:latest