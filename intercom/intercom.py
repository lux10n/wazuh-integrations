import os, json, datetime, time
from urllib import response

try:
    import requests
except ImportError:
    exit('Module requests is not installed. Install using `pip install requests`')

LOG_OUTFILE = os.path.join(os.path.dirname(__file__), "intercom.log")

# TIME_INTERVAL_SECONDS = 10 * 60  # 10 minutes
TIME_INTERVAL_SECONDS = 7 * 24 * 60 * 60  # 7 days

try:
    INTERCOM_TOKEN = os.environ.get('INTERCOM_TOKEN')
    assert type(INTERCOM_TOKEN) is str, "Intercom token not set"
except Exception as thrown_exception:
    raise thrown_exception


def tag_and_save(json_event):
    try:
        transformed_event = {
            "integration": "intercom",
            "intercom": json_event
        }
        with open(LOG_OUTFILE, 'a') as log_writer:
            log_writer.write(f'{json.dumps(transformed_event)}\n')
    except Exception as thrown_exception:
        raise thrown_exception


def pull_activity_logs(date_after, date_before):
    stop_querying = False
    next_url = f'https://api.intercom.io/admins/activity_logs?created_at_after={date_after}&created_at_before={date_before}'

    while not stop_querying:
        response = requests.get(
            url=next_url,
            headers={
                'Authorization': f'Bearer {INTERCOM_TOKEN}',
                'Accept': 'application/json',
                'Intercom-Version': '2.15',
                'User-Agent': 'Wazuh-Agent'
            },
            timeout=10
        )
        print(f'[i] Remaining requests : {response.headers.get("X-RateLimit-Remaining", "Unknown")}. Limits reset at {datetime.datetime.fromtimestamp(int(response.headers.get("X-RateLimit-Reset", "Unknown")))}')
        if response.status_code == 429:
            raise Exception(f'Rate limit hit. Limits reset at {datetime.datetime.fromtimestamp(int(response.headers.get("X-RateLimit-Reset", "Unknown")))}')
        if response.status_code != 200:
            raise Exception(f'API error {response.status_code}: {response.text}')

        api_response = response.json()
        pulled_events = api_response.get('activity_logs', [])

        for event in pulled_events:
            tag_and_save(event)
        print(f'[i] Pulled and saved {len(pulled_events)} events to {LOG_OUTFILE}.')

        pages = api_response.get('pages', {})
        next_url = pages.get('next')
        time.sleep(2)
        if not next_url:
            stop_querying = True

if __name__ == '__main__':
    try:
        os.makedirs(os.path.dirname(LOG_OUTFILE), exist_ok=True)

        now = datetime.datetime.now(datetime.timezone.utc)
        date_upper_bound_dt = now
        date_lower_bound_dt = now - datetime.timedelta(seconds=TIME_INTERVAL_SECONDS)

        date_upper_bound = int(date_upper_bound_dt.timestamp())
        date_lower_bound = int(date_lower_bound_dt.timestamp())

        rfc3339_format = '%Y-%m-%dT%H:%M:%SZ'
        display_date_before = date_upper_bound_dt.strftime(rfc3339_format)
        display_date_after = date_lower_bound_dt.strftime(rfc3339_format)
        print(f'[i] Range : {display_date_after} => {display_date_before}')

        print(f'[i] Pulling Intercom activity logs...')
        intercom_logs = pull_activity_logs(
            date_after=date_lower_bound,
            date_before=date_upper_bound
        )

    except Exception as e:
        print(f'[!] Script failed: {str(e)}')
        raise