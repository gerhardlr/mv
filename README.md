# This repo is a demonstration of testing a state machine running as a server

There are two levels of testing:
1. dev tests: for testing and developing the state machine server
2. feature tests: for testing the machine

The main purpose is to demonstrate how the features tests need to allow for working with a system whose state persists between tests and changes with a significant duration. The server serves its state as (1) a rest (call/return) interface; and (2) a websocket (pub/sub). Therefore, it allows for subscribing to the state changes whilst commanding states to be changed.

Commanding the state to be changed can either be done as a "blocking call" or a non blocking call (background). The commands can be set with a specific duration to take place to simulate changes that may take some time. This allows for demonstrating the scenario where the system is busy changing state whilst attempting to perform a next command (resulting in a 405 error).

The interface to the server is done via an intermediate proxy object.

Although the dev tests can be ran with mock replacesments, the feature tests requires the fastapi dev server to be started (see below).

## Installing the system
The project requires python 3.10 and poetry to be installed (you can also use the devcontainer supplied)
```
poetry install
```

## Running the fastapi server:

For dev mode (i.e. automatic restart server after a file has been saved)

```
poetry run fastapi dev mv/server.py --port 30002
```

To run the server as for default production

```
poetry shell
serve
```

## Running the tango device server:

```
poetry shell
serve_tango app -nodb --dlist "mv/statemachine/1" -port 30002
```


## deploying

This devcontainer comes with the implicit loading of a minikube. When the window is launched minikube is started in the background.

However it often may be the case that the minikube service is stuck or broken so make sure it is running by typing:
```
minikube status
```
If minikube is stuck you can start it manually:
```
minikube start
```

Note that by default the docker registry used is decoupled from the one being used by minikube. This means, images that you build using docker will not automatically be picked up by kubernetes (in the case of a pullPolicy of "Never"). To enable this run:
```
eval $(minikube docker-env)

```
To check that your docker registry is pushing to minikube run:

```
docker image ls
```

It should show your images (if build) together with those used by kubernetes (registry.k8s.io/).

The tool that we will use to deploy kubernetes resources will be helm. However to simplify things we will not be using any variables in the templates (i.e. the templates can be used directly by kubectl commands as well).

To check if any installations are running:

```
helm ls
```

you can delete any helm installations by running

```
helm delete <installation name>
```

the installations are contained withing the `helm/` folder (e.g. `helm/mv1`). To deploy an instance:
```
helm install <instance name> helm/<installation folder> 
```
Usually the instance name is the same as the installation folder.

Each installation is discussed in more detail below.

### mv1 installation

This installation demonstrates the server running as a container withing a kubernetes K8 "POD".

```
helm install mv1 helm/mv1
```
To get a view of the installation you can use the vscode tool or run:

```
kubectl get pods
kubectl describe pod/mv
```

K8 does provides communication to pods only via a virtual subnet called clusterIPs (typically 10.0.0.0/28). This means you wont be able to call this service from the host itself. To do this an additional container (curl) has been installed within the same pod.
A k8s POD is a set of one or more containers (mostly just 1) which acts as processes running within a "localhost" of that POD. So if you run a shell within the curl container:

```
kubectl exec --stdin --tty mv -c curl -- sh
```

Then you can reach that server via local host:
1. to get the state of the statemachine

```
curl localhost:8000/state

```

2. to switch on

```
curl localhost -X POST localhost:8000/switch_on
```

3. to switch off

```
curl localhost -X POST localhost:8000/switch_off
```

### mv1b installation

This installation abstracts the pod deployment as a generic backend that can be mapped via a proxy acting as a "load balancer" (the head), directing incoming network traffic to allocated pods called by the given service name. This service can be of Type NodePort which maps a host port to the proxy service, allowing access to the service from the host itself.

To install the application, first uninstall previous installation (to ensure things are stable wait a few seconds afterwards)

```
helm uninstall mv1
```

then 

```
helm install mv1b helm/mv1b
```

To get state of the service run

```
kubectl get service
```
This will show a service named mv of type NodePort.

Note that this time the curl container was deployed as a separate pod (to demonstrate communications between pods via services).

So to see that a service abstracts the pod you can call that service name directly from the curl pod using the name mv (instead of localhost) and the port 80 (instead of 8000 because it was set so in the service spec).

```
kubectl exec --stdin --tty curl -- curl mv/state
```
Note that the command above was ran inside the pod by injecting the command to run inside and then exiting out of the session afterwards.

Finally by setting the service to be of type NodePort implies that the host (or node in K8s speak) will listen on the given port (30000) and forward it to the service proxy (which then forwards it to the pod). So now one should be able to call the service directly from the host on the node's virtual network interface. But that means one require the host network interface:

```
minikube ip
```
which would give an IP address (e.g. something like 192.168.49.2) 
(note if you run ifconfig you will get a network interface adapter (virtual) that maps to that subnet)

So to run the command from your local host:
```
curl 192.168.49.2:30000/state
```
This means you can actually run your tests by setting the SERVER_IP and SERVER_PORT to the settings above.

### mv1c installation

In this installation a pod is defined to the k8s cluster as a deployment. In other words it gets "metadata" that defines deployment characteristics about the pod. In essence a deployment tells kubernetes the whish to have a "type" of pod deployed (defined in terms of a template) without caring the specifics of the pod itself -(there is also a stafefullset type of deployment that does care about the specific naming and addressing of the pod but not the instance itself). In essence the pod becomes replaceable. This means the kubernetes controller can "re-deploy" a pod or re-instantiate the pod in cases of failures. Note the service will still work the same as it maps to specific labels (defined in the pod template) generated on the pod.

To demonstrate this run:

```
helm in stall mv1c helm/mv1c
```

If you run `kubectl get pods` you will get a pod with a hashcode appended to its name (e.g. mv-589bd796f-2wgrm) if you delete that pod by running 

```
kubectl delete pod mv-589bd796f-2wgrm (replace with actual name)
```

a new pod instance will immediately by deployed (see this by running `kubectl get pods again`)

To verify that a new pod get's deployed run a command on the state machine to change it's state:

```
curl -X POST 192.168.49.2:30000/switch_on
curl 192.168.49.2:30000/state
```
The output should be "ON". Now if you delete the pod:

```
kubectl delete pod mv-589bd796f-2wgrm (replace with actual name)
```

Then get the state of the machine again:

```
curl 192.168.49.2/state
```
The state of the machine has been initialized again to null. In real life this is not desireable. State should
persist even if the power fails. So to do this we need to look at how K8s allow for persistance.

### mv2 installation

For this application we need to have additional functionality of the server to persist its state. So in stead of having a state machine that writes state as a dictionary in memory, we have a version that writes it as a json file to a specific folder.

You can test this by deploying the server after setting the `PERSIST_STATE_IN_FILE=True`

```
export PERSIST_STATE_IN_FILE=True
poetry run serve
```

If you run tests now you will see that a file has been created: `.build/state,json` so setting the state is persisted in between startups.

To enable this in a kubernetes deployment you make use of the `volume` field for a given pod (or pod template for a deployment) this volume is given a name that gets referred to within a container as something that the container can "mount into" using the `volumeMounts` field. In our case we have ensured that a volume named `state` mounts onto the field `app/.build` (the location that the app is set to write to). There are a myriad types of volumes that can be created and used but for this simple example a volume of type `hostPath` (not to be used in production) that persist data onto the actual host (the exact location is determined by minikube).

Lasty a container spec also allows for setting env variables into the running container. We therefore set `PERSIST_STATE_IN_FILE=True` for this pod to make sure the server runs in the correct mode.

To test that this work you install the app:

```
helm install mv2 helm/mv2
```

And then run the same state changes and pod delete commands for the `mv1c` deployment. After the pod get;s redeployed 
the state remains on.

As previously mentioned a deployment defines information about how the pod gets's deployed. One of that is how many instances of that same pod you want to be running at the same time. Since the service maps to any pod with the required labels, running multiple instances does not affect the way the server is addressed. The proxy will however map the call to any available pod making up the deployment. In principle this should not be a problem if communication is strictly one way and stateless for every REST command. However since our server also allows for pub/sub behaviour the correct way in which events are sent back must also be "stateless". The way the default server works is to set a signal (indicating that the state has changed) upon writing state - which then causes the websocket to publish to the client that the state has changed. But if there are running multiple instances the pod responsible for signalling to the client may not be the same one as the pod responsible for setting the state. This can be demonstrated by scaling up the number of pods:

```
kubectl scale --replicas=3 deployment/mv

```
If your run the `test_server_on` pytest the test will stuck waiting for the event indicating ON because it doesnt get the event from the specific pod responsible to publish this. 

To do this correctly one should persist the information in a database (e.g. redis) with the ability to create pub/sub connections - this shall be demonstrated in the next type of installation.

### mv3 installation

This deployment solves the problem of running multiple replica servers using a redis backend for persisting the state.

To do this a new state machine variant is needed that interfaces with a Redis server. This can be tested by running the system with the env `USE_REDIS_FOR_STATE_SERVER=True`. If you want to do debugging or development you can set `USEFAKE_REDIS=True`

The redis server settings is provided the the following env variables:
1. REDIS_HOST e.g. 192.168.49.2
2. REDIS_PORT e.g 30001

The redis server is deployed as a seperate pod (statefullset), with a nodeport service (port 30001). This means you can also run the server from you host machine and connect to the redis via the nodeport 30001

To deploy run

```
helm install mv3 helm/mv3
```

Then run the tests on you host.

Now scale the system up to 3.

```
kubectl scale --replicas=3 deployment/mv
```

Then run the tests again. This time the tests will pass.

### tangomv installation

This application uses the tango device server as the server (using the same statemachine and backend)

To install run:

```
helm install mvtango helm/mvtango
```

To test that the server is running:

```
export SERVER_IP=192.168.49.2
export SERVER_IP=30002
ping_device
```

Note, currently there is a delay of 12 seconds in waiting for events to be pushed from tango device. This seems to have
something to do with the way the server is deployed with in K8s.






