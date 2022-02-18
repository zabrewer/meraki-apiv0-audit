import meraki
import meraki.aio
import asyncio
import tqdm.asyncio
import datetime

__author__ = 'Zach Brewer, Nico Darrow'
__email__ = 'zbrewer@cisco.com'
__version__ = '0.0.2'
__license__ = 'MIT'

'''
aync code that returns the all api calls for a given org

uses timestamps and pagination to speed up async requests

see https://developer.cisco.com/meraki/api-v1/#!get-organization-api-requests
'''

def get_date_intervals(days, slices):

    '''Takes the current date and calculates the number of days back from today
    it then "slices" start and end times and returns the results in UTC timestamps

    Parameters
    ----------
    days : int
        number of days to return starting with the current day/time and working backwards
    slices : int
        number of slices - most common is 2.  
        E.g. if you went back 5 days with a slice value of 2, 
        this function would return start/end timestamps for the last 5 days in 12 hour increments

    Returns
    -------
    results
        a nested list (list of lists) of pairs of start/end timestamps
    '''
    results = []
    current_time = datetime.datetime.utcnow()
    start_time = current_time - datetime.timedelta(days)
    current_timestamp = current_time.timestamp()
    start_timestamp = start_time.timestamp()
    delta_time = current_timestamp - start_timestamp
    slice_interval = delta_time / (days * slices)
    last_used = start_timestamp

    for _ in range(1, (days * slices) + 1 ):
        t0 = last_used
        t1 = t0 + slice_interval
        last_used = t1
        start_date_slice = datetime.datetime.fromtimestamp(t0)
        end_date_slice = datetime.datetime.fromtimestamp(t1)

        if start_date_slice < end_date_slice:
            results.append([start_date_slice.isoformat(), end_date_slice.isoformat()])

    return results

async def get_v0_requests(aiomeraki, org, start_date, end_date):
    '''Async function that calls getOrganizationApiRequests for a given org using start and end dates (pagination)
    
    Parameters
    ----------
    aiomeraki : class AsyncDashboardAPI
        instance of the AsyncDashboardAPI class from the meraki python package
    org : 
        number of slices - most common is 2.  
        E.g. if you went back 5 days with a slice value of 2, 
        this function would return start/end timestamps for the last 5 days in 12 hour increments
    start_date : 
        the start date for the api requests (t0 in the Meraki Dashboard API documentation)
    end_date :
        the start date for the api requests (t1 in the Meraki Dashboard API documentation)

    Returns
    -------
    request_data
        a nested dict including all v0 API calls for a given org, start_date, and end_date
    '''

    try: 
        org_requests = await aiomeraki.organizations.getOrganizationApiRequests(
            organizationId=org['id'],
            perPage=1000,
            total_pages='all',
            t0=start_date,
            t1=end_date,
        )

    except meraki.exceptions.AsyncAPIError as e:
        print(f'Meraki AIO API Error (OrgID "{ org["id"] }", OrgName "{ org["name"] }"): \n { e }')

    except Exception as e:
        print(f'some other ERROR: {e}')

    request_data = []
    for req in org_requests:
        if 'v0' in req['path']:
            req.update(org_id = org['id'], org_name = org['name'])
            request_data.append(req)

    return request_data

async def async_apicall(api_key, target_orgs, lookback, debug_values, get_orgs=False):
    
    '''Async function that instantiates a Meraki dashboard API session
    NOTE: you have to use "async with" so that the session will be closed correctly at the end of the usage
    
    Parameters
    ----------
    apikey : str
        meraki dashboard api key
    target_orgs : list
        nested dict of all target orgs in format of [{'id':'123', 'name':'OrgName'}]
        must at least include keys 'id' and 'name'
        can also be results of another call to getOrganizaitons() in the Meraki API or a filtered subset of that call completed elsewhere
    lookback : int
        number of days to look back - usually max of 31 is supported by the meraki dashboard API
    debug_values: dict
        dictionary of debug_values for meraki dashboard api session
    get_orgs: bool, optional
        flag - if True, this does an async to getOrganizaitons()

    Returns
    -------
    all_requests
        a nested dict of v0 dashboard API requests for target_orgs in the given number of days (lookback)
    '''
    
    async with meraki.aio.AsyncDashboardAPI(
            api_key,
            base_url='https://api.meraki.com/api/v1',
            log_file_prefix=__file__[:-3],
            maximum_concurrent_requests=10,
            maximum_retries= 100,
            use_iterator_for_get_pages = False,
            wait_on_rate_limit=True,
            output_log=debug_values['output_log'],
            print_console=debug_values['output_console'],
            suppress_logging=debug_values['suppress_logging']
        ) as aiomeraki:

        if get_orgs:        
            orgs = await aiomeraki.organizations.getOrganizations()
        else:
            orgs = target_orgs

        apicall_tasks = []
        date_ranges = get_date_intervals(days=lookback, slices=2)

        for date_range in date_ranges:
            for org in orgs:
                apicall_tasks.append(get_v0_requests(aiomeraki, org=org, start_date=date_range[0], end_date=date_range[1]))

        all_requests = []

        for task in tqdm.tqdm(
                asyncio.as_completed(apicall_tasks),
                total = len(apicall_tasks),
                colour='green',
                ):

            api_json = await task
            for api_call in api_json:
                all_requests.append(api_call)
        
        return all_requests

def asyncget_requests(api_key, orgs, lookback, debug_app=False, get_orgs=False):
    if debug_app:
        debug_values = {'output_log' : True, 'output_console' : True, 'suppress_logging' : False}
    else:
        debug_values = {'output_log' : False, 'output_console' : False, 'suppress_logging' : True}

    #begin async loop
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_apicall(api_key, orgs, lookback, debug_values, get_orgs))