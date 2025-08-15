
import csv

input_file = '/Users/iwakiryo2/Documents/01Research/01Source/V2X_Network_Simulation/documents/related_work/20250815_100papers.csv'

try:
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            title = row.get('Title')
            if title:
                # Use string concatenation to avoid f-string escaping issues
                query = '"' + title + '" abstract keyword'
                print(query)
except FileNotFoundError:
    pass
