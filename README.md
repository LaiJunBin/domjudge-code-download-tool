# Domjudge code download tool

Download domjudge contest source code tool.

## Install
```
$ pip install -r requirements.txt
```

## Setting (.env)
```
API_HOST={Your domjuage url}
API_USERNAME={domjudge apiuser username}
API_PASSWORD={domjudge apiuser password}
```

## Run Server
```
$ uvicorn main:app
```

The server will run at http://localhost:8000