image:
	docker build -t local/mv:latest .

re-deploy:
	helm delete mv
	sleep 10
	helm install mv helm/mv

deploy:
	helm upgrade --install mv helm/mv