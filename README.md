# Prozorro bridge contracting
## Manual install

1. Install requirements

```
virtualenv -p python3.8.2 venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

2. Set variables in **settings.py**

3. Run application

```
python -m prozorro_bridge_pricequotation.main
```

## Tests and coverage 

```
coverage run --source=./src/prozorro_bridge_pricequotation -m pytest tests/
```

## Config settings (env variables):

**Required**

```API_OPT_FIELDS``` - Fields to parse from feed (need for crawler)
```PUBLIC_API_HOST``` - API host on which chronograph will iterate by feed (need for crawler also)
```CDB_PUBLIC_API_HOST``` - the same is ```PUBLIC_API_HOST```
```MONGODB_URL``` - String of connection to database (need for crawler also)

**Optional**
- ```CRAWLER_USER_AGENT``` - Set value of variable to all requests header `User-Agent`
- ```MONGODB_DATABASE``` - Name of database
- ```MONGODB_PRICEQUOTATION_COLLECTION``` - Name of collection where will be stored processed pq
- ```API_TOKEN``` - Service access token to CDB
- ```USER_AGENT``` - Value of header to be added to requests

**Doesn't set by env**
- ```ERROR_INTERVAL``` - timeout interval between requests if something goes wrong and need to retry

