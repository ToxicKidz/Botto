from bot.bot import Bot
import aiohttp

MYSTBIN_API_URL = "https://mystb.in/api/pastes"

async def get_mystbin_link(bot: Bot, content: str, syntax: str = None):
    multi_part_writer = aiohttp.MultipartWriter()
    paste_content = multi_part_writer.append(content)
    paste_content.set_content_disposition("form-data", name="data")
    paste_content = multi_part_writer.append_json(
        {"meta": [{"index": 0, "syntax": syntax}]}
    )
    paste_content.set_content_disposition("form-data", name="meta")

    async with bot.http_session.post(MYSTBIN_API_URL, data=multi_part_writer) as response:
        return await response.json()