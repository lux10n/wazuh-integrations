import json
import re
from collections import Counter
from prettytable import PrettyTable

def extract_json(line):
    """Extract JSON payload from a syslog line, if any."""
    match = re.search(r'({.*})', line)
    if match:
        try:
            return json.loads(match.group(1).replace('\ufeff', ''))
        except json.JSONDecodeError:
            return None
    return None

def get_nested_value(data, field):
    keys = field.split(".")
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data

def analyze_field(file_path, field):
    """List all distinct values and counts for a given field."""
    values = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = extract_json(line)
            if not data:
                continue

            value = get_nested_value(data, field)

            if value is not None:
                values.append(value)

    if not values:
        print(f"No values found for field '{field}'.")
        return

    counter = Counter(values)
    table = PrettyTable(["Value", "Count"])
    for val, count in counter.most_common():
        table.add_row([val, count])

    print(f'BREAKDOWN : {field}')
    print(table)
    print('\n'*3)

# Example usage:
# analyze_field("eset-logs.log", "domain")
# analyze_field("eset-logs.log", "event_type")
# analyze_field("eset-logs.log", "event")
# analyze_field("eset-logs.log", "severity")
# analyze_field("eset-logs.log", "result")
# analyze_field("eset-logs.log", "user")
# analyze_field("eset-logs.log", "scanner_id")
analyze_field("jira.log", "jira.category")
analyze_field("jira.log", "jira.summary")
analyze_field("jira.log", "jira.objectItem.name")
# analyze_field("intercom-wrapped.log", "activity_description")