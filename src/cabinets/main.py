from itertools import islice
import yaml
import pprint
from seleniumrequests import Chrome 
import time
import json
import base64
import sys


job_name = sys.argv[1]

#INPUTS
nominal_sheet_size = "4x4"
kerf = 4
cabinet_selection = ['std-d2', 'std-d2', 'std-door', 's12'] + (['purse-box'] * 5) + ['hat-box']

#cabinet_selection = ['purse-box','purse-box','purse-box','purse-box','purse-box', 'hat-box']
print(cabinet_selection)

if nominal_sheet_size == "4x4":
    sheet_size = [1219, 1219]
elif nominal_sheet_size == "4x8":
    sheet_size = [1219, 2438]


print_options = {
       
    }

def chunk(arr_range, arr_size):
    arr_range = iter(arr_range)
    return iter(lambda: tuple(islice(arr_range, arr_size)), ())
def send_devtools(driver, cmd, params):
        """
        Works only with chromedriver.
        Method uses cromedriver's api to pass various commands to it.
        """
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

def generate_payloads():
    with open('cabinets.yaml', 'r') as f:
        cabinets = yaml.safe_load(f)
        parts_by_thickness = {}
        for cabinet_name in cabinet_selection:
            cabinet = cabinets['cabinets'][cabinet_name]
            for part, properties in cabinet['parts'].items():
                thickess = properties.get('thickness')
                if parts_by_thickness.get(thickess):
                    parts_by_thickness[thickess].append([f'{cabinet_name}-{part}', properties])
                else:
                    parts_by_thickness[thickess] = [[f'{cabinet_name}-{part}', properties]]
        
        

        for thickness, parts in parts_by_thickness.items():
            for group_index, group in enumerate(chunk(parts, 15)):
                payload = {
                    'name': f"All {thickness}mm parts for cabinet selection",
                    'settings.kerf': kerf,
                    'settings.labels': 'true',
                    'settings.grain': 'false',
                    'settings.groups': 'false',
                    'settings.prices': 'false',
                    'settings.priorities': 'false',
                    'settings.leftTrim': '',
                    'settings.rightTrim': '',
                    'settings.topTrim': '',
                    'settings.bottomTrim': '',
                    'stocks[0].length': sheet_size[0],
                    'stocks[0].width': sheet_size[1],
                    'stocks[0].count': 1000,
                    'stocks[0].grainDirection': '',
                    'mergeStocks': 'false' 
                }
                
                for index, part in enumerate(group):
                    id, part = part
                    payload[f'requirements[{index}].length'] = part.get('length')   
                    payload[f'requirements[{index}].width'] = part.get('width')   
                    payload[f'requirements[{index}].count'] = part.get('quantity')   
                    payload[f'requirements[{index}].label'] = id
                    payload[f'requirements[{index}].grainDirection'] = '' 
                pprint.pprint(payload)
                webdriver = Chrome()
                webdriver.get('https://www.opticutter.com/cut-list-optimizer')
                webdriver.request('POST', 'https://www.opticutter.com/cut-list-optimizer', data=payload)
                webdriver.get('https://www.opticutter.com/cut-list-optimizer/print')
                time.sleep(5)
                result = send_devtools(webdriver, "Page.printToPDF", print_options)
                
                open(f'{job_name}-{thickness}-{group_index+1}-cutlist.pdf', 'wb').write(base64.b64decode(result['data']))

generate_payloads()