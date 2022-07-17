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
