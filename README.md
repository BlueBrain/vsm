# Visualisation SBO Middleware

This project enables running HPC/Visualisation workflows on AWS or on on-prem infrastructure for public internet users.
It is made of two main components:
### VSM master
Handles job submission, user authentication and authorization.

### VMS proxy
Used to proxy Brayns (https://github.com/BlueBrain/Brayns) WebSocket communication


## Running
Use entrypoints defined in pyproject.toml
```vsm_master = "vsm:run_master"```
```vsm_slave = "vsm:run_slave"```



# Funding & Acknowledgment

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government's ETH Board of the Swiss Federal Institutes of Technology.
