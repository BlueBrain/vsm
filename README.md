# Visualisation SBO Middleware


## Starting application

---
### Using docker-compose
The easiest is to use a docker compose:
```
TODO
```
---
### Manual docker start

You can start services separately as well:
```
docker build -t vsm .
``` 
#### Master
 
```
docker run --rm -ti --network host -e VMM_DB_HOST=${MONGO_URL} vsm -m vsm.master
```

#### Worker
```
docker run --rm -ti --network host -e VMM_DB_HOST=${MONGO_URL} vsm -m vsm.slave
```

Note that you should run docker in network host mode, otherwise you will run into a problem with accessing a mongodb instance.

---
### Start natively

There are two entrypoints available: 
`mooc_proxy` starting vsm.master and `ws_proxy` which starts vsm.slave

---
## Options
### Start-up arguments
To get help on arguments:
```
 mooc_proxy --help
 # In docker:
 docker run --rm vsm -m vsm.master --help 
 docker run --rm vsm -m vsm.salve --help
  
```
You may want to have a look into a settings file for a complete list of environmental variables used by VMM.
The most important is:
- VMM_UNICORE_SA_TOKEN: A token used to allocate a job using UNICORE

#### LTI auth related
For LTI testing an env var dumdumdumdumdummyclient can be used. 
- dumdumdumdumdummyclient="dumdumdumdumdummykey"
---

## API documentation
OpenAPI/swagger is used to document REST API. When running a server just visit: http://localhost:4444/api/doc#/

## Running tests with coverage report
It is the easiest to run tests in a Docker container:
```
make run-docker-tests
```
otherwise:
```
$ VMM_TEST=True VMM_SECURE_ADMIN_KEY="s3cur3" python -m pytest -v -s --cov=vsm
```
you can add `-report=html ` to generate html report

## Contributing

Please run ```make precommit``` before commiting which runs **black** and **isort**