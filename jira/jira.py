import os, json, datetime, time
try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    exit('Module requests is not installed. Install using `pip install requests`')

LOG_OUTFILE = os.path.join(os.path.dirname(__file__), "jira.log")

TIME_INTERVAL_SECONDS = 10 * 60  # 10 minutes

try:
    JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')
    JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
    JIRA_BASE_URL = os.environ.get('JIRA_BASE_URL')

    assert type(JIRA_API_TOKEN) is str, "Jira token not set"
    assert type(JIRA_EMAIL) is str, "Jira email not set"
    assert type(JIRA_BASE_URL) is str, "Jira base URL not set"

except Exception as thrown_exception:
    raise thrown_exception


def tag_and_save(json_event):
    try:
        transformed_event = {
            "integration": "jira",
            "jira": json_event
        }
        with open(LOG_OUTFILE, 'a') as log_writer:
            log_writer.write(f'{json.dumps(transformed_event)}\n')
    except Exception as thrown_exception:
        raise thrown_exception


def pull_activity_logs(date_after, date_before):
    stop_querying = False
    offset = 0

    while not stop_querying:

        next_url = (
            f"{JIRA_BASE_URL}/rest/api/3/auditing/record"
            f"?from={date_after}&to={date_before}&offset={offset}"
        )

        response = requests.get(
            url=next_url,
            auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN),
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Wazuh-Agent'
            },
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f'API error {response.status_code}: {response.text}')

        api_response = response.json()

        pulled_events = api_response.get('records', [])
        total = api_response.get('total', 0)
        limit = api_response.get('limit', 1000)

        EXCLUDED_SUMMARIES = {
            "Project version created",
            "Project version released",
            "Deleted Jira issue"
        }

        saved_events = 0
        for event in pulled_events:
            if event.get("summary") in EXCLUDED_SUMMARIES:
                continue
            tag_and_save(event)
            saved_events+=1

        print(f'[i] Pulled and saved {saved_events} events to {LOG_OUTFILE}.')

        offset += limit

        time.sleep(1)

        if len(pulled_events) < limit:
            stop_querying = True

if __name__ == '__main__':
    try:
        os.makedirs(os.path.dirname(LOG_OUTFILE), exist_ok=True)

        # range dates must be in RFC3339 format with milliseconds
        date_upper_bound = now = datetime.datetime.now(datetime.timezone.utc)
        date_lower_bound = date_upper_bound - datetime.timedelta(seconds=TIME_INTERVAL_SECONDS)


        rfc3339_format = '%Y-%m-%dT%H:%M:%S.%fZ'

        current_date_before = date_upper_bound.strftime(rfc3339_format)
        current_date_after = date_lower_bound.strftime(rfc3339_format)

        print(f'[i] Range : {current_date_after} => {current_date_before}')
        print(f'[i] Pulling audit logs...')

        pull_activity_logs(
            date_after=current_date_after,
            date_before=current_date_before
        )

    except Exception as e:
        print(f'[!] Script failed: {str(e)}')
        raise