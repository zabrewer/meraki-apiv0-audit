import meraki
import meraki.aio
import asyncio
import tqdm.asyncio

__author__ = 'Zach Brewer, Nico Darrow'
__email__ = 'zbrewer@cisco.com'
__version__ = '0.0.2'
__license__ = 'MIT'

'''
simple code that returns the admins for multiple orgs
'''

async def get_orgadmins(aiomeraki, org):
    '''
    Async function that calls getOrganizationAdmins for a given org
    '''

    try: 
        org_admins = await aiomeraki.organizations.getOrganizationAdmins(
            organizationId=org['id']
        )

    except meraki.exceptions.AsyncAPIError as e:
        print(f'Meraki AIO API Error (OrgID "{ org["id"] }", OrgName "{ org["name"] }"): \n { e }')
        org_admins = None

    except Exception as e:
        print(f'some other ERROR: {e}')
        org_admins = None

    admin_data = []
    if org_admins:
        for admin in org_admins:
            admin.update(org_id = org['id'], org_name = org['name'])
            admin_data.append(admin)
    else:
        org_admins = None


    return admin_data

async def async_apicall(api_key, orgs, debug_values):
    # Instantiate a Meraki dashboard API session
    # NOTE: you have to use "async with" so that the session will be closed correctly at the end of the usage
    async with meraki.aio.AsyncDashboardAPI(
            api_key,
            base_url='https://api.meraki.com/api/v1',
            log_file_prefix=__file__[:-3],
            log_path='logs/',
            maximum_concurrent_requests=10,
            maximum_retries= 100,
            wait_on_rate_limit=True,
            output_log=debug_values['output_log'],
            print_console=debug_values['output_console'],
            suppress_logging=debug_values['suppress_logging']
        ) as aiomeraki:
        
        all_orgadmins = []

        admin_tasks = [get_orgadmins(aiomeraki, org) for org in orgs]
        for task in tqdm.tqdm(
                asyncio.as_completed(admin_tasks),
                total = len(admin_tasks),
                colour='green',
                ):

            admin_json = await task
            for admin in admin_json:
                all_orgadmins.append(admin)
        
        return all_orgadmins


def asyncget_admins(api_key, orgs, debug_app=False):
    if debug_app:
        debug_values = {'output_log' : True, 'output_console' : True, 'suppress_logging' : False}
    else:
        debug_values = {'output_log' : False, 'output_console' : False, 'suppress_logging' : True}

    #begin async loop
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_apicall(api_key, orgs, debug_values))
