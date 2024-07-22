'''
  Author: Eric Julien
  Date: 20240722
  Description: This program takes as input a json file and converts it to a CSV file.  It
  was particularly designed for AWS CLI output for describing EC2 instances.
  
'''
import json
import csv
import argparse

instances = []
csv_keys = []
temp_dict = {}

def parse_json(the_value, key_name, instance, path, instance_list, in_list=False):
    '''
    This is a recursive function that takes output from an AWS CLI describe-instances command
    and changes the json to csv.

    the_value - This is either a dict, list, or single value
    key_name  - The dict key of the_value
    instance  - This dict keeps track of all key/values for the instance/resource
    path      - The "path" of keys to the instance(s)/resource(s)
    instance_list - The list of instances/resources
    in_list   - Boolean that tracks if the values are in a list
    '''

    # Parse each kv in the dict
    if isinstance(the_value, dict):
        func_path = path[:] # Clone it, We don't want the original path to change

        for inner_attr in the_value:
            if len(func_path)>0 and func_path[0] == inner_attr:
                # We found a match with the lowest path item
                if len(func_path)>1:
                    func_path.pop(0)
                    parse_json(the_value.get(inner_attr), inner_attr, instance, func_path, instance_list, in_list)
                    # We finished parsing the instance/resource
                elif len(func_path)==1:
                    # Start parsing the instance/resource
                    instance = {}
                    parse_json(the_value.get(inner_attr), "", instance, [], instance_list, False)
                    # We finished parsing the instance/resource
            elif len(func_path)==0:
                if key_name =="":
                    newkeyname = inner_attr
                else:
                    newkeyname = f"{key_name}.{inner_attr}"
                parse_json(the_value.get(inner_attr), newkeyname, instance, func_path, instance_list, in_list)
   
    # Parse each item in the list
    elif isinstance(the_value, list):
        for item in the_value:
            try:
                parse_json(item, key_name, instance, path, instance_list, True)
                if key_name == "":
                    instance_list.append(instance)
                    instance = {}
            except Exception as e:
                print(f"ERROR - Parsing the list item - {e}")

    # Finally add each kv to the instance dict
    else:
        newkey = f"{key_name}"
        try:
            if (in_list) and instance.get(newkey, False):
                instance[newkey] = f"{instance[newkey]}|{the_value}"
            else:
                instance[newkey] = the_value
                csv_keys.append(newkey)
        except Exception as e:
            print(f"ERROR - Adding key/value to instance - {e}")

def open_json_file(input_file):
    # Open the json file for reading
    print(f"Opening {input_file}")
    try:
        with open(input_file) as json_file:
            data = json.load(json_file)
    except Exception as e:
        print(f"ERROR - Opening JSON file - {e}")
    return data

def open_csv_file_for_writing(output_file):
    # Open the csv output file
    try:
        csv_file = open(output_file, 'w')
        csv_writer = csv.writer(csv_file)
    except Exception as e:
        print(f"ERROR - Opening CSV file for writing - {e}")
    return csv_writer, csv_file

def put_path_in_list(path):
    # Put the 'path' in a list
    try:
        if path:
            path_list = path.split(':')
            print(f"path_list = {path_list}")
        else:
            path_list = ""
    except Exception as e:
        print(f"ERROR - Putting 'path' in list - {e}")
    return path_list

def put_data_in_csv_file(instances, csv_keys, csv_writer):
    # Put the data in the CSV file
    count = 0
    for instance in instances:
        if count == 0:
            # Write the headers
            try:
                csv_writer.writerow(csv_keys)
                count += 1
            except Exception as e:
                print(f"ERROR - Writing header line to CSV file - {e}")

        # Create the row line, give empty value if instance doesn't have the key
        row = []
        for key in csv_keys:
            try:
                row.append(instance.get(key,''))
            except Exception as e:
                print(f"ERROR - Creating row to CSV file - {e}")
        
        # Put row line in csv file
        try:
            csv_writer.writerow(row)
        except Exception as e:
                print(f"ERROR - Writing row to CSV file - {e}")



# Get the command line args
parser = argparse.ArgumentParser(
            prog = 'aws_cli_json2csv.py',
            description = 'Transforms AWC CLI JSON output to CSV.')
parser.add_argument("input_file", help="The JSON file to convert to CSV")
parser.add_argument("output_file", help="The CSV output file")
parser.add_argument("-p", "--path", help="The path of the keys to the resource, with ':' between each key. For example for AWS CLI 'describe_instances', the path is 'Reservations:Instances'")
# TODO: add filter to include/exclude columns in CSV
args = parser.parse_args()

# Open files
data = open_json_file(args.input_file)
csv_writer, csv_file = open_csv_file_for_writing(args.output_file)
# Path transformation
path_list = put_path_in_list(args.path)

# Do the heavy lifting
parse_json(data, "", temp_dict, path_list, instances)
# If the there is no path, there won't be a list, so need to output the one CSV row that was created.
if path_list =="":
    instances.append(temp_dict)

# Remove duplicate header values, this doesn't maintain the order of items in the list
csv_keys = (list(set(csv_keys)))
csv_keys.sort()

print(f"Writing data to CSV file {args.output_file}")
put_data_in_csv_file(instances, csv_keys, csv_writer)

csv_file.close()
