import datetime
import json
import pathlib
import time
from csv import DictWriter
from pprint import pprint

import click
import meraki

import admins
import api_req

__author__ = 'Zach Brewer'
__email__ = 'zbrewer@cisco.com'
__version__ = '0.0.3'
__license__ = 'MIT'

def clean_orgs(all_orgs, user_orgs):

    user_orgs = [org.lower().strip() for org in user_orgs]

    cleaned_orgs = []
    for org in all_orgs:
        if user_orgs[0] == 'all':
            if org['api']['enabled'] == False:
                click.secho(
                    f'[WARNING] You provided the "all" argument but the following org does not have the Meraki API enabled. Organiztion Name: "{org["name"]}." Skipping this organization from v0 API Audit.\n',
                    fg='yellow'
                    )
            else:
                cleaned_orgs.append(org)

        if org['name'] in user_orgs and org['api']['enabled'] == False:
            click.secho(f'[WARNING] You provided an org name without the Meraki API enabled. Organiztion Name: "{org["name"]}." Skipping this organization from v0 API Audit.\n',
            fg='yellow')

        elif org['name'].lower() in user_orgs:
            cleaned_orgs.append(org)

    if cleaned_orgs:
        return cleaned_orgs
    click.secho(
    '[WARNING] Either given names were not found or no given org names have API enabled.\n', fg='yellow'
    )
    click.secho(
        'NOTE: Organization names that contain spaces must be wrapped in quotes (e.g. "Org Name")\n', fg='yellow'
    )

    click.secho(
        'The given API key has access to the following orgs:\n', fg='yellow'
    )
    for loop_count, org in enumerate(all_orgs):
        click.secho(f'{org["name"]}', fg='white')
        if loop_count == 0:
            time.sleep(5)
        else:
            time.sleep(.01)
    exit(0)

def add_admins(request_json, admin_json):
    combined_data = []
    for admin in admin_json:
        for request in request_json:
            if admin['id'] == request['adminId']:
                combined_data.append({'admin_name': admin['name'], 'admin_email': admin['email'], **request})

    return combined_data

def export_calls_to_csv(fname, v0_calls, *fields):
    if not fields:
        fields = ['adminId',
                'admin_email',
                'admin_name',
                'host',
                'method',
                'org_id',
                'org_name',
                'path',
                'queryString',
                'version',
                'operationId',
                'responseCode',
                'sourceIp',
                'ts',
                'userAgent'
            ]
    try:
        with open(fname, 'w') as csvfile:
            writer = DictWriter(csvfile, fieldnames=fields)
            writer.writeheader()
            counter = 0

            for api_call in v0_calls:
                counter += 1
                writer.writerow(api_call)

    except OSError as e:
        click.secho(f'[ERROR] Error when writing csv file: \n {e}', fg='red')

    return counter

class CallDashboard(object):
    def __init__(self, apikey):
        """call to dashboard API and makes session available to other methods in this class

        """
        self.api_session = meraki.DashboardAPI(
        api_key=apikey,
        base_url="https://api.meraki.com/api/v1/",
        output_log=False,
        print_console=False,
        suppress_logging=True,
        )

    def get_allorgs(self):
        return self.api_session.organizations.getOrganizations()

@click.command()
@click.argument('apikey', nargs=1)
@click.argument(
    'orgs', 
    nargs=-1, 
    )
@click.option(
    '--days', 
    default=31, 
    help='Number of days to audit for v0 API calls. \n Default is 31.  Max is 31, min is 1 day.'
    )
def audit(apikey, orgs, days):
    """Audits the meraki v0 api calls for one or more orgs. Sends audit data to a timestamped CSV file in the same directory."""
    
    # re-assign this variable name b/c click expects the name of the argument to match kwargs it's cleaner to call these user_orgs
    user_orgs = list(orgs)

    if days < 1 or days > 31 :
        click.secho('[WARNING] Number of days should be a value of 1 to 31\n', fg='yellow')
        exit(0)

    if 'all' in user_orgs and len(orgs) > 1:
        click.secho('[WARNING] You included "all" in orgs as well as other org names - ignoring "all" and processing other org names.\n', fg='yellow')
        user_orgs.remove('all')

    if not user_orgs:
        click.secho('[WARNING] No org names specified. \nOrgs can be any number of org names seperated by a single space or "all" (no quotes) to audit all orgs available to your API key. \nExiting...', fg='yellow')
        exit(0)
    else:
        click.secho('Getting all orgs that this API key has access to...\n', fg='green')
        try:

            session = CallDashboard(apikey=apikey)
            all_orgs = session.get_allorgs()

        except meraki.exceptions.APIError as e:
            print(f'Meraki API ERROR: {e}\n')
            exit(0)

        except Exception as e:
            print(f'Non Meraki-SDK ERROR: {e}')
            exit(0)

    # clean up leading/trailing spaces and capitalization mismatch for orgs
    # also test for orgs that were not found, that the user doesn't have accesss to or that don't have the API enabled
    sanitized_orgs = clean_orgs(all_orgs, user_orgs=user_orgs)

    # make call to our async admin package (import admins)
    click.secho('Getting admins for the following org names:\n', fg='green')

    click.secho(
    f'{" | ".join(x["name"] for x in sanitized_orgs)}\n', fg='white'
    )

    all_admins = admins.asyncget_admins(api_key=apikey, orgs=sanitized_orgs)

    # make call to our async api_req package (import api_req)
    click.secho(
        'Getting API calls for the following org names:\n', fg='green'
        )
    click.secho(
        f'{" | ".join(x["name"] for x in sanitized_orgs)}\n', fg='white'
        )
    click.secho(f'Auditing orgs with v0 API calls for the past {days} days.', fg='green')
    click.secho(
        '[INFO] This may take some time for multiple orgs with large API call volumes!\n',
        fg='yellow',
    )

    v0_requests = api_req.asyncget_requests(api_key=apikey, orgs=sanitized_orgs, lookback=days)

    csv_json = add_admins(request_json=v0_requests, admin_json=all_admins)

    now = datetime.datetime.now()
    filename_time = now.strftime("%Y-%m-%d_%H:%M:%S")

    f_name = 'v0audit_' + filename_time + '.csv'
    f_path =  pathlib.Path.cwd()
    click.secho(f'Writing audit results to csv file "{f_name}" into directory {f_path}.', fg='green')

    number_of_calls = export_calls_to_csv(fname=f_name, v0_calls=csv_json)
    click.secho(f'SUCCESS! Successfully wrote {number_of_calls} Meraki Dashboard v0 API calls to csv file.', fg='green')

if __name__ == '__main__':
    audit()