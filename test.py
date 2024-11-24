import csv
import re
import os
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    input_folder = r'C:\test\files_input'
    output_file_summary = r'summary.csv'
    output_file_slow = r'slow.csv'
    output_file_unique = r'unique.csv'
    
    folder_read_write(input_folder, output_file_summary, output_file_slow, output_file_unique)

def date_format_conv(date_value):
    date_object = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
    converted_date = date_object.strftime('%Y/%m/%d %H:%M:%S')
    return converted_date

def utc_to_jct(utc_str):
    utc_dt = datetime.strptime(utc_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('UTC'))
    jst_dt = utc_dt.astimezone(ZoneInfo('Asia/Tokyo'))
    jst_str = jst_dt.strftime('%Y-%m-%d %H:%M:%S')
    return jst_str

def process_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?duration: (\d+\.\d+) ms.*?statement: (.*?)(?=\n\d{4}-\d{2}-\d{2}|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    results = []
    slow_results = []
    unique_results = []
    for match in matches:
        date, speed, sql = match
        sql = ' '.join(sql.split())
        date_utc = date_format_conv(date)
        date_jst = date_format_conv(utc_to_jct(date))
        speed_float = float(speed)
        speed_seconds = speed_float / 1000

        result = [date_utc, date_jst, speed, sql]
        results.append(result)
        
        if speed_float >= 5000:
            slow_results.append(result)
        
        if speed_seconds >= 5:
            unique_results.append([date_utc, date_jst, speed_seconds, sql])

    return results, slow_results, unique_results

def folder_read_write(input_folder, output_file_summary, output_file_slow, output_file_unique):
    all_results = []
    all_slow_results = []
    all_unique_results = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_folder, filename)
            results, slow_results, unique_results = process_file(file_path)
            all_results.extend(results)
            all_slow_results.extend(slow_results)
            all_unique_results.extend(unique_results)

    write_csv(output_file_summary, all_results, ["日付UTC", "日付JST", "速度(duration)", "SQL"])
    write_csv(output_file_slow, all_slow_results, ["日付UTC", "日付JST", "速度(duration)", "SQL"])

    # Group by first 20 characters of SQL and keep only the slowest
    grouped_results = {}
    for result in all_unique_results:
        sql_key = result[3][:20]
        if sql_key not in grouped_results or float(result[2]) > float(grouped_results[sql_key][2]):
            grouped_results[sql_key] = result

    write_csv(output_file_unique, grouped_results.values(), ["日付UTC", "日付JST", "速度(秒)", "SQL"])

def write_csv(output_file, data, headers):
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(data)

if __name__ == '__main__':
    main()
