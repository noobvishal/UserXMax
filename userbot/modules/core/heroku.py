# Copyright (C) 2020 Adek Maulana.
# All rights reserved.
"""
   Heroku manager for your userbot
"""

import heroku3
import asyncio
import os
import requests
import math

from ..help import add_help_item
from userbot import HEROKU_APPNAME, HEROKU_APIKEY
from userbot.events import register
from userbot.utils.prettyjson import prettyjson

Heroku = heroku3.from_key(HEROKU_APIKEY)
heroku_api = "https://api.heroku.com"


@register(outgoing=True, pattern=r"^.(set|get|del) var(?: |$)(.*)(?: |$)([\s\S]*)")
async def variable(var):
    """
        Manage most of ConfigVars setting, set new var, get current var,
        or delete var...
    """
    if HEROKU_APPNAME is not None:
        app = Heroku.app(HEROKU_APPNAME)
    else:
        return await var.edit("`[HEROKU]:"
                              "\nPlease setup your` **HEROKU_APPNAME**")
    exe = var.pattern_match.group(1)
    heroku_var = app.config()
    if exe == "get":
        await var.edit("`Getting information...`")
        await asyncio.sleep(1.5)
        try:
            variable = var.pattern_match.group(2).split()[0]
            if variable in heroku_var:
                return await var.edit("**ConfigVars**:"
                                      f"\n\n`{variable} = {heroku_var[variable]}`\n")
            else:
                return await var.edit("**ConfigVars**:"
                                      f"\n\n`Error:\n-> {variable} don't exists`")
        except IndexError:
            configs = prettyjson(heroku_var.to_dict(), indent=2)
            with open("configs.json", "w") as fp:
                fp.write(configs)
            with open("configs.json", "r") as fp:
                result = fp.read()
                if len(result) >= 4096:
                    await var.client.send_file(
                        var.chat_id,
                        "configs.json",
                        reply_to=var.id,
                        caption="`Output too large, sending it as a file`",
                    )
                else:
                    await var.edit("`[HEROKU]` ConfigVars:\n\n"
                                   "================================"
                                   f"\n```{result}```\n"
                                   "================================"
                                   )
            os.remove("configs.json")
            return
    elif exe == "set":
        await var.edit("`Setting information...`")
        variable = var.pattern_match.group(2)
        if not variable:
            return await var.edit(">`.set var <ConfigVars-name> <value>`")
        value = var.pattern_match.group(3)
        if not value:
            variable = variable.split()[0]
            try:
                value = var.pattern_match.group(2).split()[1]
            except IndexError:
                return await var.edit(">`.set var <ConfigVars-name> <value>`")
        await asyncio.sleep(1.5)
        if variable in heroku_var:
            await var.edit(f"**{variable}**  `successfully changed to`  ->  **{value}**")
        else:
            await var.edit(f"**{variable}**  `successfully added with value`  ->  **{value}**")
        heroku_var[variable] = value
    elif exe == "del":
        await var.edit("`Getting information to deleting variable...`")
        try:
            variable = var.pattern_match.group(2).split()[0]
        except IndexError:
            return await var.edit("`Please specify ConfigVars you want to delete`")
        await asyncio.sleep(1.5)
        if variable in heroku_var:
            await var.edit(f"**{variable}**  `successfully deleted`")
            del heroku_var[variable]
        else:
            return await var.edit(f"**{variable}**  `is not exists`")


@register(outgoing=True, pattern=r"^.usage(?: |$)")
async def dyno_usage(dyno):
    """
        Get your account Dyno Usage
    """
    await dyno.edit("`Processing...`")
    useragent = ('Mozilla/5.0 (Linux; Android 10; SM-G975F) '
                 'AppleWebKit/537.36 (KHTML, like Gecko) '
                 'Chrome/80.0.3987.149 Mobile Safari/537.36'
                 )
    user_id = Heroku.account().id
    headers = {
     'User-Agent': useragent,
     'Authorization': f'Bearer {HEROKU_APIKEY}',
     'Accept': 'application/vnd.heroku+json; version=3.account-quotas',
    }
    path = "/accounts/" + user_id + "/actions/get-quota"
    r = requests.get(heroku_api + path, headers=headers)
    if r.status_code != 200:
        return await dyno.edit("`Error: something bad happened`\n\n"
                               f">.`{r.reason}`\n")
    result = r.json()
    quota = result['account_quota']
    quota_used = result['quota_used']

    """ - Used - """
    remaining_quota = quota - quota_used
    percentage = math.floor(remaining_quota / quota * 100)
    minutes_remaining = remaining_quota / 60
    hours = math.floor(minutes_remaining / 60)
    minutes = math.floor(minutes_remaining % 60)

    """ - Current - """
    App = result['apps']
    try:
        App[0]['quota_used']
    except IndexError:
        AppQuotaUsed = 0
        AppPercentage = 0
    else:
        AppQuotaUsed = App[0]['quota_used'] / 60
        AppPercentage = math.floor(App[0]['quota_used'] * 100 / quota)
    AppHours = math.floor(AppQuotaUsed / 60)
    AppMinutes = math.floor(AppQuotaUsed % 60)

    await asyncio.sleep(1.5)

    return await dyno.edit("**Dyno Usage**:\n\n"
                           f" -> `Dyno usage for`  **{HEROKU_APPNAME}**:\n"
                           f"     •  `{AppHours}`**h**  `{AppMinutes}`**m**  "
                           f"**|**  [`{AppPercentage}`**%**]"
                           "\n\n"
                           " -> `Dyno hours quota remaining this month`:\n"
                           f"     •  `{hours}`**h**  `{minutes}`**m**  "
                           f"**|**  [`{percentage}`**%**]"
                           )


add_help_item(
    "heroku",
    "Core",
    "Manage your heroku vars.",
    """
    `.usage`
    **Usage:** Check your heroku dyno hours remaining.
    
    `.set var <NEW VAR> <VALUE>`
    **Usage:** Add new variable or update existing value variable
    !!! WARNING !!!, after setting a variable the bot will restarted
    
    `.get var or .get var <VAR>`
    **Usage:** get your existing varibles, use it only on your private group!
    This returns all of your private information, please be caution...
    
    `.del var <VAR>`
    **Usage:** delete existing variable.
    !!! WARNING !!!, after deleting variable the bot will restarted
    """
)
