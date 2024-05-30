from telethon import TelegramClient, sync
import yaml
import argparse

config = {}
with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.loader.SafeLoader)
    
proxy = None
if config['proxy']:
    proxy = config['proxy']

client = TelegramClient(config['session'], config['api_id'], config['api_hash'], proxy=proxy).start(bot_token=config['bot_token'])

if __name__ == '__main__':
    with client:
        user = client.get_entity(config['telegram_user'])
        admin = client.get_entity(config['telegram_admin'])
    print(f"User ID: {user.id}")
    print(f"Admin ID: {admin.id}")
