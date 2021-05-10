#!/usr/bin/env python3
"""
Disclaimer:
    I don't believe I wrote this one.
"""
from aiomultiprocess import Pool
import aiohttp

async def fetch_url(url):
    return await aiohttp.request('GET', url)

async def fetch_all(urls):
    async with Pool() as pool:
        results = await pool.map(fetch_url, urls)
