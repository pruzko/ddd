import asyncio
import json
import tqdm

import aioboto3



with open('mailinator_lambda/lambda_function.zip', 'rb') as f:
    LAMBDA_CODE = f.read()


async def find_role(cli):
    async for res in cli.get_paginator('list_roles').paginate():
        for role in res['Roles']:
            if role['RoleName'] == 'DDDLambdaRole':
                return role['Arn']
    return None


async def create_role(cli):
    trust_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {
                'Service': 'lambda.amazonaws.com'
            },
            'Action': 'sts:AssumeRole'
        }]
    }
    
    res = await cli.create_role(
        RoleName='DDDLambdaRole',
        AssumeRolePolicyDocument=json.dumps(trust_policy),
    )
    await asyncio.sleep(6)
    
    return res['Role']['Arn']


async def clear_existing_lambdas(cli):
    async for res in cli.get_paginator('list_functions').paginate():
        for func in res['Functions']:
            if func['FunctionName'].startswith('DDD_mailinator_mailboxes_'):
                await cli.delete_function(FunctionName=func['FunctionName'])


async def create_lambda(cli, role_arn, idx):
    res = await cli.create_function(
        FunctionName=f'DDD_mailinator_mailboxes_{idx}',
        Runtime='python3.8',
        Role=role_arn,
        Handler='lambda_function.lambda_handler',
        Code={ 'ZipFile': LAMBDA_CODE },
        Timeout=900,
    )
    return res['FunctionArn']


async def main():
    with open('../.env') as f:
        keys = f.read().strip().split('\n')[:2]
        aws_key_id, aws_key_secret = [k.split('=')[1] for k in keys]

    lambda_client = aioboto3.Session().client(
        service_name='lambda',
        region_name='eu-central-1',
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_key_secret,
    )
    iam_client = aioboto3.Session().client(
        service_name='iam',
        region_name='eu-central-1',
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_key_secret,
    )

    async with lambda_client as lambda_client:
        async with iam_client as iam_client:
            print('Looking for role...')
            role_arn = await find_role(iam_client)
            if not role_arn:
                print('Creating role...')
                role_arn = await create_role(iam_client)

            print('Clearing lambdas...')
            await clear_existing_lambdas(lambda_client)
            print('Creating lambdas...')
            for idx in tqdm.tqdm(range(100)):
                lambda_arn = await create_lambda(lambda_client, role_arn, idx)

            res = await lambda_client.invoke(
                FunctionName='DDD_mailinator_mailboxes_0',
                Payload=json.dumps({'addresses': ['a', 'b']})
            )
            res = await res['Payload'].read()
            print(res)


if __name__ == '__main__':
    asyncio.run(main())