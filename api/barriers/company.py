import json
import requests


class Company(object):

    def __init__(self, id):
        self.id = id

        url = f"https://api.datahub.dev.uktrade.io/v3/company/{self.id}"

        headers = {
            'Authorization': "Bearer ditStaffToken",
            'Content-Type': "application/json",
        }

        response = requests.request("GET", url, headers=headers)

        company_json = json.loads(response.text)

        self.name = company_json['name']
        self.comanies_house_no = company_json['company_number']
        self.address = company_json['registered_address_1']
        self.sector = company_json['sector']['name']
        self.incorporation_date = company_json['created_on']
        self.company_type = company_json['business_type']
        self.turnover_range = company_json['turnover_range']
        self.employee_range = company_json['employee_range']

    def __str__(self):
        return self.name
