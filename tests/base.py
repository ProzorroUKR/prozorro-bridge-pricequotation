import json
import os

PWD = os.path.dirname(os.path.realpath(__file__))

with open(PWD + '/data/tender.json', 'r') as json_file:
    TEST_TENDER = json.load(json_file)

with open(PWD + '/data/new_tender.json', 'r') as json_file:
    TEST_NEW_TENDER = json.load(json_file)

with open(PWD + '/data/profile.json') as json_file:
    TEST_PROFILE = json.load(json_file)

with open(PWD + '/data/new_agreement.json') as json_file:
    TEST_NEW_AGREEMENT = json.load(json_file)

with open(PWD + '/data/agreement.json') as json_file:
    TEST_AGREEMENT = json.load(json_file)
