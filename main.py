import asyncio
import os

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

import requests
from pyrogram import Client, filters
from requests import get

os.chdir(os.path.dirname(os.path.abspath(__file__)))

link = '🔗'
bread = '🥖'
edit_timeout = 0
api_id = Config.APP_ID,
api_hash = Config.API_HASH,
bot_token = Config.TG_BOT_TOKEN,

bot = Client("Cookie", bot_token= Config.TG_BOT_TOKEN, api_id= Config.APP_ID, api_hash= Config.API_HASH )

async def callback(curr, size, chat_id, message_id):
    try:
        global edit_timeout
        if edit_timeout < 30:
            edit_timeout += 1
            return
        edit_timeout = 0

        done = int(20 * curr / int(size))
        per = f'{curr * 100 / int(size):.1f}%  [{curr / 1024 / 1024:.1f} / {int(size) / 1024 / 1024:.1f} MB]'
        yet = '#' * done
        of = ' ' * (20 - done)
        await bot.edit_message_text(chat_id, message_id, 'Uploading... {}\n'
                                                         '[{}{}]'.format(per, yet, of))

    except Exception as e:
        print(repr(e))


@bot.on_message(filters.text & filters.private)
async def tfload(client, message):
    try:
        if '/start' in message.text.lower() or '/' not in message.text:
            await bot.send_message(message.chat.id, f"Send download link {link}")
            return

        url = message.text
        file_name = url.split("/")[-1]
        file_name = f'{file_name[:20]}...{file_name[-10:]}' if len(file_name) > 50 else file_name
        response = get(url, stream=True)
        size = response.headers.get('content-length')
        load = await bot.send_message(message.chat.id, 'Downloading...')

        if response.status_code != 200 or not size:
            await bot.send_message(message.chat.id, f'Unable to obtain file size of {url}')
            return
        if int(size) / 1024 / 1024 > 1910:
            await bot.send_message(message.chat.id, f'Unable to send file more than 1900MB.')
            return

        with open(file_name, 'wb') as f:
            ded, x = 0, 0
            for chunk in response.iter_content(4096):
                f.write(chunk)
                ded += len(chunk)
                x += 1
                if x % 5000 == 0:
                    done = int(20 * ded / int(size))
                    per = f'{ded * 100 / int(size):.1f}%  [{ded / 1024 / 1024:.1f} / {int(size) / 1024 / 1024:.1f} MB]'
                    yet = '#' * done
                    of = ' ' * (20 - done)
                    try:
                        await bot.edit_message_text(message.chat.id, load.id, 'Downloading... {}\n'
                                                                                      '[{}{}]'.format(per, yet, of))
                    except Exception as e:
                        print(repr(e))

        await bot.edit_message_text(message.chat.id, load.id, f'Downloading... 100%')
        upload = await bot.send_message(message.chat.id, 'Uploading...')
        file = await bot.send_document(message.chat.id, file_name, progress=callback,
                                       progress_args=(message.chat.id, upload.id))
        await bot.delete_messages(message.chat.id, [load.id, upload.id])

        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass

    except Exception as e:
        await bot.send_message(message.chat.id, repr(e))

bot.run()
