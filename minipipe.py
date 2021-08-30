import boto3
import datetime
import json
import os
import requests
import time

from botocore.exceptions import ClientError
from sys import argv


CLIENT = None

DELETES = []
UPDATES = []

STACKS = []

ACCOUNTS = []
REGIONS = ['us-east-2']


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    user = ''
    repo = ''
    sha = 'master'

    # if CodeBuild:
    # repo = os.environ['CODEBULD_SOURCE_REPO_URL'].split('/')[-1]
    # sha = os.environ['CODEBULD_SOURCE_VERSION']

    # file_parsing_complete = parse_file_changes(user, repo, sha)
    file_parsing_complete = local_parse_file_changes()
    print(f"Updates: {UPDATES}")
    if file_parsing_complete:
        for each in UPDATES:
            for region in REGIONS:
                # create_client(region)
                run_updates(each)

    print(f"Stacks: {STACKS}")
        
    # stacks_to_delete_complete = local_stacks_to_delete()
    print(f"Deletes: {DELETES}")
    # if stacks_to_delete_complete:
    #     for each in DELETES:
    #         for region in REGIONS:
    #             create_client(region)
    #             local_stacks_to_delete(each)

    return


def run_updates(template_file):
    global STACKS

    head, tail = os.path.split(template_file)
    stack_name = f"minipipe-{tail.split('.')[0]}"
    cloudformation_template = None
    with open(template_file, 'r') as yaml_file:
        cloudformation_template = yaml_file.read()
        # yaml_file.seek(0)
        # for line in yaml_file:
        #     if line.startswith('#regions:'):
        #         regions = line.split(',').strip()
    if cloudformation_template:
        # print(stack_name)
        STACKS.append(stack_name)
        # deploy_cloudformation(stack_name, cloudformation_template)
    return


def list_files(current_path):
    return os.listdir(current_path)


def local_stacks_to_delete():
    global DELETES

    stacks = CLIENT.list_stacks(
        StackStatusFilter=[
            'CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_FAILED', 'ROLLBACK_COMPLETE', 'DELETE_IN_PROGRESS', 'DELETE_FAILED', 'DELETE_COMPLETE', 'UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_IN_PROGRESS', 'UPDATE_ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_COMPLETE', 'REVIEW_IN_PROGRESS', 'IMPORT_IN_PROGRESS', 'IMPORT_COMPLETE', 'IMPORT_ROLLBACK_IN_PROGRESS', 'IMPORT_ROLLBACK_FAILED', 'IMPORT_ROLLBACK_COMPLETE',
        ]
    )

    for stack in stacks['StackSummaries']:
        if 'minipipe-' in stack['StackName']:
            if stack['StackName'] not in STACKS:
                DELETES.append(stack['StackName'])
    return False

def local_parse_file_changes():
    global UPDATES

    directories = [os.getcwd()]
    for directory in directories: # root files
        for i in os.scandir(directory):
            if i.is_file():
                file_name = str(i.name).split('.')
                if len(file_name) == 2:
                    if file_name[1] in ('yaml', 'yml'):
                        UPDATES.append(i.path)
            elif i.is_dir():
                directories.append(i)

    if UPDATES:
        return True
    else:
        return False


# vvv This needs work! vvv
# def parse_file_changes_github(user, repo, sha):
#     global DELETES
#     global UPDATES


#     if os.name == 'nt':
#         file_name = dir_path + '\\' + '\\'.join(template_file.split('\/')[1:])
#     elif os.name == 'posix':
#         file_name = f"{dir_path}/{'/'.join(template_file.split('/')[1:])}"

#     response = requests.get(url=f'https://github.com/api/v3/repos/{user}/{repo}/commits/{sha}')
#     if response.status_code == 200:
#         commit = json.loads(response.text)
#         for each in commit.get('files', []):
#             if 'iac' in each['filename'] and each['filename'].split('/')[-1].split('.')[1] in ['yaml', 'yml'] and 'buildspec' not in each['filename']:
#                 if each['status'] in ['modified', 'added']:
#                     UPDATES.append(each['filename'])
#                 elif each['status'] == 'removed':
#                     DELETES.append(each['filename'])
#                 elif each['status'] == 'renamed':
#                     DELETES.append(each['previous_filename'])
#                     UPDATES.append(each['filename'])
#         return True
#     return False


def create_client(region):
    # session = boto3.Session(profile_name=account, region_name=region)
    session = boto3.Session(region_name=region)
    global CLIENT
    CLIENT = session.client('cloudformation')
    return


def cf_check_status(stack_name):
    try:
        response = CLIENT.describe_stacks(StackName=stack_name)
    except ClientError as err:
        response = None
    return response


def cf_create(stack_name, cloudformation_template):
    response = CLIENT.create_stack(
        StackName=stack_name,
        TemplateBody=cloudformation_template
    )
    stack_id = response['StackId']
    print(f"creating stack: {stack_id}")

    while True:
        response = cf_check_status(stack_name)
        status = response['Stacks'][0]['StackStatus']
        print(f"{stack_name}: {status}")
        if response['Stacks'][0]['StackStatus'] not in ['CREATE_IN_PROGRESS']:
            print(response['Stacks'][0]['StackStatus'])
            break
        else:
            time.sleep(10)
    return


def cf_delete(stack_name):
    CLIENT.delete_stack(StackName=stack_name)
    response = cf_check_status(stack_name)
    print(response)
    return


def cf_update(stack_name, cloudformation_template):
    try:
        CLIENT.update_stack(
            StackName=stack_name,
            TemplateBody=cloudformation_template
        )
        while True:
            response = cf_check_status(stack_name)
            if response['Stacks'][0]['StackStatus'] not in ['UPDATE_IN_PROGRESS', 'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS']:
                print(f"stack status: {response['Stacks'][0]['StackStatus']}")
                break
            elif response['Stacks'][0]['StackStatus'] == 'UPDATE_COMPLETE':
                break
            else:
                time.sleep(10)
    except ClientError as err:
        print(err)
        response = cf_check_status(stack_name)
        if response['Stacks'][0]['StackStatus'] in ['ROLLBACK_FAILED']:
            cf_delete(stack_name)
    return


def deploy_cloudformation(stack_name, cloudformation_template):
    response = cf_check_status(stack_name) 
    if response:
        cf_update(stack_name, cloudformation_template, response['Stacks'][0]['StackId'])
    else:
        cf_create(stack_name, cf_template)
    return


def delete_cloudformation():
    return


if __name__ == '__main__':
    main()