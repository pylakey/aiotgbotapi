# aiotgbotapi - Asynchronous Telegram BOT API Client

[![PyPI version shields.io](https://img.shields.io/pypi/v/aiotgbotapi.svg)](https://pypi.python.org/pypi/aiotgbotapi/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/aiotgbotapi.svg)](https://pypi.python.org/pypi/aiotgbotapi/)
[![PyPI license](https://img.shields.io/pypi/l/aiotgbotapi.svg)](https://pypi.python.org/pypi/aiotgbotapi/)

## Installation

### PyPI

```shell
pip install aiotgbotapi
```

or if you use [Poetry](https://python-poetry.org)

```shell
poetry add aiotgbotapi
```

## Examples

### Basic example

```python
import asyncio
import logging

from aiotgbotapi import Bot
from aiotgbotapi.filters import Filters
from aiotgbotapi.types import Message

bot = Bot("BOT TOKEN HERE")


@bot.on_message(filters=Filters.command('start'))
async def on_start_command(_bot: Bot, message: Message):
    await message.reply(f"Hello, {message.from_.mention}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(bot.run())

```