import csv
import asyncio
from typing import Tuple

import aiohttp
import w3ext

PROXIES = 'proxies.txt'
ACCOUNTS = 'accounts.csv'


def load_proxies():
    with open(PROXIES, 'r') as fr:
        proxies = list(fr)

    counter = 0
    while True:
        if not (proxy := proxies[counter]).startswith("#"):
            yield proxy
        counter += 1
        if counter >= len(proxies):
            counter = 0


def load_accounts() -> Tuple[str, w3ext.Account]:
    with open(ACCOUNTS, 'r') as fr:
        reader = csv.DictReader(fr, ('private_key', 'auth_key'))
        data = list(reader)
    for item in data[1:]:
        yield item['auth_key'], w3ext.Account.from_key(item['private_key'])


async def main():
    proxies = load_proxies()
    accounts = load_accounts()

    for auth_key, account in accounts:
        await process(account, auth_key, next(proxies))


def get_headers(auth_token):
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.6',
        'Authorization': f'Bearer {auth_token}',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'https://www.intract.io',
        'Referer': 'https://www.intract.io/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'dnt': '1',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Brave";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

async def _get_message(wallet, session, proxy):
    url = "https://api.intract.io/api/qv1/auth/generate-nonce"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={
            "walletAddress": wallet
        }) as resp:
            nonce = (await resp.json())['data']['nonce']

    message = f'Please sign this message to verify your identity. Nonce: {nonce}'
    return message


async def process(account: w3ext.Account, auth_key, proxy):
    url = "https://api.intract.io/api/qv1/auth/linea-aa-wallet"

    print(f"{account}: Use proxy {proxy}")
    async with aiohttp.ClientSession(headers=get_headers(auth_key)) as session:
        nonce = await _get_message(account.address, session, proxy)
        signature = await account.sign(data=nonce)

        async with session.post(url, json={
            "signature": signature.hex(),
            "walletAddress": account.address
        }) as resp:
            print(await resp.json())


if __name__ == '__main__':
    asyncio.run(main())