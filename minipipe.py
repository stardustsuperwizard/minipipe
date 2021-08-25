#   Copyright 2021 Michael Miller
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


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

ACCOUNTS = []
REGIONS = ['us-east-1', 'us-east-2']


def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    user = ''
    repo = ''
    sha = 'master'

    # if CodeBuild:
    # repo = os.environ['CODEBULD_SOURCE_REPO_URL'].split('/')[-1]
    # sha = os.environ['CODEBULD_SOURCE_VERSION']

    file_parsing_complete = parse_file_changes(user, repo, sha)

    if file_parsing_complete:
        for each in UPDATES:
            if os.name == 'nt':
                file_name = f"{dir_path}\{'\\'.join(each.split('/')[1:])}"
            elif os.name == 'posix':
                file_name = f"{dir_path}/{'/'.join(each.split('/')[1:])}"
            head, tail = os.path.split(filename)
            stack_name = f"{each}-{tail.split('.')[0]}"
            cloudformation_template = None
            regions = []
            with open(each, 'r') as yaml_file:
                cloudformation_template = yaml_file.read()
                yaml_file.seek(0)
                for line in yaml_file:
                    if line.startswith('#regions:'):
                        regions = line.split(',').strip()
            if cloudformation_template:
                for region in region:
                    create_client(account, region)
                    print(stack_name)
                    deploy_cloudformation(stack_name, cloudformation_template)
        
        for each in DELETES:
            for region in REGIONS:
                print(stack_name)
                create_client(account, region)
                delete_cloudformation(stack_name)
    else:
        print('No files to parse. Ending.')
    return


def parse_file_changes(user, repo, sha):
    global DELETES
    global UPDATES

    response = requests.get(url=f'https://github.com/api/v3/repos/{user}/{repo}/commits/{sha}}')
    if response.status_code == 200:
        commit = json.loads(response.text)
        for each in commit.get('files', []):
            if 'iac' in each['filename'] and each['filename'].split('/')[-1].split('.')[1] in ['yaml', 'yml'] and 'buildspec' not in each['filename']:
                if each['status'] in ['modified', 'added']:
                    UPDATES.append(each['filename'])
                elif each['status'] == 'removed':
                    DELETES.append(each['filename'])
                elif each['status'] == 'renamed':
                    DELETES.append(each['previous_filename'])
                    UPDATES.append(each['filename'])
        return True
    return False


def create_client(account, region):
    session = boto3.Session(profile_name=account, region_name=region)
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


def cleanup_cloudformation(stack_name):
    response = CLIENT.list_stacks(
        StackStatusFilter=[
            'CREATE_COMPLETE',
            'ROLLBACK_FAILED',
            'ROLLBACK_COMPLETE',
            'UPDATE_COMPLETE'
        ]
    )
    
    for stack in response['StackSummaries']:
        temp_name = stack['StackId'].split('/')[1]
            if temp_name not in local_templates:
                print(f"Deleting: {temp_name}")
                cf_delete(temp_name)
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
