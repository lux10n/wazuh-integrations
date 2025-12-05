import os, json, datetime

try:
    import requests
except ImportError:
    exit('Module requests is not installed. Install using `pip install requests`')

LOG_OUTFILE = os.path.join(os.path.dirname(__file__), "cloudflare.log")

# Audit logs: searchable up to 30 days
# Firewall events: searchable up to 15 days, but only one day (86400s) can be queried at a time

TIME_INTERVAL_SECONDS = 10 * 60 # 10 minutes

try:
    CF_ACCOUNT_ID = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    assert type(CF_ACCOUNT_ID) is str, "Cloudflare Account ID not set"
    CF_API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
    assert type(CF_API_TOKEN) is str, "Cloudflare API Token not set"
except Exception as thrown_exception:
    raise thrown_exception

def tag_and_save(json_event):
    try:
        transformed_event = {
            "integration" : "cloudflare",
            "cloudflare" : json_event
        }
        with open(LOG_OUTFILE, 'a') as log_writer:
            log_writer.write(f'{json.dumps(transformed_event)}\n')
    except Exception as thrown_exception:
        raise thrown_exception


def pull_audit_logs(date_before, date_after):
    try:
        audit_logs = []
        stop_querying = False
        pagination_cursor = None

        while not stop_querying:

            logpull_query = requests.get(
                url = (
                    f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}'
                    f'/logs/audit?before={date_before}&since={date_after}&direction=asc'
                )+(f'&cursor={pagination_cursor}' if pagination_cursor else ''), 
                
                headers = {
                    'Authorization' : f'Bearer {CF_API_TOKEN}',
                    'User-Agent' : f'Wazuh-Agent'
                },
                
                timeout = 10 #10 seconds timeout
            )

            api_response = logpull_query.json()
            
            pulled_events = api_response.get('result')

            if pulled_events is None : pulled_events = [] # return empty list if no pulled events

            print(f'[i] Pulled {len(pulled_events)} events.')

            audit_logs += pulled_events

            # check for available cursor, else break
            pagination_cursor = api_response.get('result_info').get('cursor')
            if pagination_cursor is None : 
                stop_querying = True

        # sort audit_logs by action.time ASC

        # print(f'[i] Audit logs : {audit_logs}')
        
        return audit_logs

    except Exception as thrown_exception:
        raise thrown_exception

def pull_firewall_events(date_before, date_after):
    try:
        # Pulls date # firewall # waf / l7ddos # allow / block # small description # name of the IP Provider # POST # HTTPS # domain.com # /login # data if post or query params if get # user agent # 403 / 500 / 200 # additional rule description

        # firewallAction : action is because indexing conflict with audit logs

        firewall_events_query = '''
            query ListFirewallEvents($filter: FirewallEventsAdaptiveFilter_InputObject) {
                viewer {
                    zones {
                        zoneTag
                        firewallEventsAdaptive(
                            filter: $filter
                            limit: 10000
                            orderBy: [datetime_ASC]
                        ) {
                            datetime 
                            kind
                            source
                            firewallAction : action
                            description
                            clientIP 
                            clientIPClass
                            clientASNDescription
                            clientCountryName
                            clientRequestHTTPMethodName
                            clientRequestScheme
                            clientRequestHTTPHost
                            clientRequestPath
                            clientRequestQuery
                            userAgent
                            originResponseStatus
                            metadata {
                                key
                                value
                            }
                            rayName
                        } 
                    }
                }
            }
        '''
        graphql_variables = {
            "filter": {
                "datetime_geq": date_after,
                "datetime_leq": date_before,
            }
        }

        graphql_fw_query = requests.post(
            url = 'https://api.cloudflare.com/client/v4/graphql',
            json = {
                "query" : firewall_events_query,
                "variables" : graphql_variables,
            },
            headers = {
                'Authorization' : f'Bearer {CF_API_TOKEN}',
                'User-Agent' : f'Wazuh-Agent'
            },
        )

        graphql_response = graphql_fw_query.json()

        # print(f'[i] GraphQL API Response : {graphql_response}')
        
        firewall_events = []
        
        for zone in graphql_response.get('data').get('viewer').get('zones'):
            for firewall_event in zone.get('firewallEventsAdaptive'):
                firewall_event['zoneTag'] = zone.get('zoneTag') # tag every specific event with the zone
                firewall_events.append(firewall_event)

        # sort firewall_events by datetime ASC

        # print(f'[i] Firewall events : {firewall_events}')

        print(f'[i] Pulled {len(firewall_events)} events.')

        return firewall_events

    except Exception as thrown_exception:
        raise thrown_exception

if __name__ == '__main__':
    os.makedirs(os.path.dirname(LOG_OUTFILE), exist_ok=True) # create log file folder if it does not exist
    # range dates must be in RFC3339 format, see https://developers.cloudflare.com/api/resources/accounts/subresources/logs/subresources/audit/methods/list/
    date_upper_bound = now = datetime.datetime.now(datetime.timezone.utc)
    date_lower_bound = date_upper_bound - datetime.timedelta(seconds=TIME_INTERVAL_SECONDS)
    rfc3339_format = '%Y-%m-%dT%H:%M:%SZ'

    current_date_before = date_upper_bound.strftime(rfc3339_format)
    current_date_after = date_lower_bound.strftime(rfc3339_format)

    print(f'[i] Range : {current_date_after} => {current_date_before}')

    print(f'[i] Pulling audit logs...')
    cloudflare_audit_logs = pull_audit_logs(
        date_before=current_date_before,
        date_after=current_date_after
    )

    print(f'[i] Pulling firewall events...')
    cloudflare_firewall_events = pull_firewall_events(
        date_before=current_date_before,
        date_after=current_date_after
    )

    print(f'[i] Writing logs to {LOG_OUTFILE}...')
    for audit_event in cloudflare_audit_logs :
        tag_and_save(audit_event)
    for firewall_event in cloudflare_firewall_events :
        tag_and_save(firewall_event)
    print(f'[i] Wrote logs to {LOG_OUTFILE}.')