import os


def health_check():
    env = dict(**os.environ)
    profile = str(env["PROFILE"])
    return {
        'statusCode': 200,
        'body': print("[%s] Marketbill file process service is running...", profile)
    }
