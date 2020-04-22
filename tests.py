import yaml

with open("suredone.yaml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


print (config['user'])
print (config['token'])