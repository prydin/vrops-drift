import requests
import json
import argparse
from requests.auth import HTTPBasicAuth

baseUrl =''
headers = { 'Content-Type': 'application/json', 'Accept': 'application/json'}



def createSymptom(name, severity, adapterKind, resourceKind, property, value, auth):
    payload = {
        'name': name,
        'adapterKindKey': adapterKind,
        'resourceKindKey': resourceKind,
        'waitCycles': '1',
        'cancelCycles': '1',
        'state': {
            'severity': severity,
            'condition': {
                'type': 'CONDITION_PROPERTY_STRING',
                'stringValue': str(value),
                'operator': 'NOT_EQ',
                'key': str(property),
                'thresholdType': 'STATIC'
            }
        }
    }
    print payload
    return requests.post(baseUrl + '/suite-api/api/symptomdefinitions',
                        headers=headers,
                        auth=auth,
                        verify=False,
                        json=payload)

def getPropertiesOfObject(name, adapterKind, resourceKind, auth):
    response = requests.get(baseUrl + '/suite-api/api/resources?name={0}&resourceKind={1}&adapterKind={2}'
                  .format(name, resourceKind, adapterKind),
                  headers=headers,
                  auth=auth,
                  verify=False)
    r = json.loads(response.content)
    id = r['resourceList'][0]['identifier']
    response = requests.get(baseUrl + '/suite-api/api/resources/{0}/properties'.format(id),
                            headers=headers,
                            auth=auth,
                            verify=False)
    return json.loads(response.content)

# Parse parameters
#
parser = argparse.ArgumentParser(description='Create symptoms based on a templte.')
parser.add_argument('--host', nargs=1, help='vR Ops host')
parser.add_argument('--user', nargs=1, help='vR Ops username')
parser.add_argument('--password', nargs=1, help='vR Ops password')
parser.add_argument('--resource', nargs=1, help='Template resource')
parser.add_argument('--resourcekind', nargs=1, help='Template resource resource kind')
parser.add_argument('--prefix', nargs=1, help='Symptom name prefix (Drift is default)')
parser.add_argument('--exclude', nargs='?', help='Name of exlcude file')
parser.add_argument('--nowarn', default=False, help='Suppress Insecure Request Warning for HTTPS')
args = parser.parse_args()

if args.nowarn:
    requests.packages.urllib3.disable_warnings()

# Load exclude file
#
excludes = {}
if args.exclude:
    with open(args.exclude) as f:
        for line in f:
            key = line.strip()
            excludes[key] = True

# Lookup resource and create symptoms based on all non-excluded properties
#
baseUrl = 'https://' + args.host[0]
auth = HTTPBasicAuth(args.user[0], args.password[0])
result = getPropertiesOfObject(args.resource[0], 'VMWARE', args.resourcekind[0], auth)
prefix=''
if args.prefix:
    prefix=args.prefix[0]
else:
    prefix='Drift'

for p in result['property']:
    pName = p.get('name')
    if excludes.get(pName):
        print pName
        continue
    result = createSymptom(prefix + ' {0}'.format(pName), 'WARNING', 'VMWARE', args.resourcekind[0],
                            pName, p['value'], auth)
    print result