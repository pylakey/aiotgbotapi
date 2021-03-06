import asyncio
from typing import Type

import httpx
from fastapi.encoders import jsonable_encoder

from .types import *
from .utils import BOT_TOKEN_RE


class BotAPIClient:
    """
    Telegram Bot API v5.3.0
    updated 25.6.2021
    """

    def __init__(self, bot_token: str):
        if not bool(bot_token) or not BOT_TOKEN_RE.match(bot_token):
            raise ValueError('Wrong bot token format')

        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.__updates_queue = asyncio.Queue()

    def run(self):
        pass

    async def updates_handling_loop(self):
        while True:
            update = await self.__updates_queue.get()

    async def __make_request(
            self,
            path: str,
            *,
            response_model: Type = None,
            as_form: bool = False,
            data: dict = None
    ):
        files = None

        if as_form:
            files = {
                k: open(v.path, 'rb')
                for k, v in data.items()
                if isinstance(v, InputFile)
            }
            data = {
                k: v if not isinstance(v, InputFile) else f"attach://{k}"
                for k, v in data.items()
            }

        data = jsonable_encoder(
            data,
            exclude_none=True,
            exclude_unset=True
        )

        async with httpx.AsyncClient(base_url=self.base_url, http2=True) as client:
            response = await client.post(
                path,
                content=ujson.dumps(data) if not as_form else None,
                data=data if as_form else None,
                files=files,
                headers={
                    "Content-Type": "application/json"
                } if not as_form else None
            )

        response_json = ujson.loads(response.text)

        if response.is_error:
            try:
                return Error.parse_obj(response_json).raise_exception()
            except pydantic.ValidationError:
                response.raise_for_status()

        if response_json.get("ok"):
            if bool(response_model):
                return Response[response_model].parse_obj(response_json).result
        else:
            try:
                return Error.parse_obj(response_json).raise_exception()
            except pydantic.ValidationError:
                response.raise_for_status()

        return response_json

    async def get_updates(
            self,
            offset: int = -1,
            limit: int = 100,
            timeout: int = 0,
            allowed_updates: list[str] = None,
    ) -> list[Update]:
        """
        Use this method to receive incoming updates using long polling ([wiki](https://en.wikipedia.org/wiki/Push_technology#Long_polling)). An Array of [Update](https://core.telegram.org/bots/api/#update) objects is returned.
        https://core.telegram.org/bots/api/#getupdates

        :param offset: Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as [getUpdates](https://core.telegram.org/bots/api/#getupdates) is called with an *offset* higher than its *update_id*. The negative offset can be specified to retrieve updates starting from *-offset* update from the end of the updates queue. All previous updates will forgotten., defaults to None
        :type offset: int, optional

        :param limit: Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100., defaults to None
        :type limit: int, optional

        :param timeout: Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only., defaults to None
        :type timeout: int, optional

        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify [???message???, ???edited_channel_post???, ???callback_query???] to only receive updates of these types. See [Update](https://core.telegram.org/bots/api/#update) for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.

Please note that this parameter doesn't affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time., defaults to None
        :type allowed_updates: list[str], optional

        """
        return await self.__make_request(
            "getUpdates",
            data={
                "offset": offset,
                "limit": limit,
                "timeout": timeout,
                "allowed_updates": allowed_updates,
            },
            response_model=list[Update],
        )

    async def set_webhook(
            self,
            url: str,
            certificate: InputFile = None,
            ip_address: str = None,
            max_connections: int = 40,
            allowed_updates: list[str] = None,
            drop_pending_updates: bool = None,
    ) -> bool:
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an update for the bot, we will send an HTTPS POST request to the specified url, containing a JSON-serialized [Update](https://core.telegram.org/bots/api/#update). In case of an unsuccessful request, we will give up after a reasonable amount of attempts. Returns *True* on success.

If you'd like to make sure that the Webhook request comes from Telegram, we recommend using a secret path in the URL, e.g. `https://www.example.com/&lt;token&gt;`. Since nobody else knows your bot's token, you can be pretty sure it's us.
        https://core.telegram.org/bots/api/#setwebhook

        :param url: HTTPS url to send updates to. Use an empty string to remove webhook integration
        :type url: str

        :param certificate: Upload your public key certificate so that the root certificate in use can be checked. See our [self-signed guide](/bots/self-signed) for details., defaults to None
        :type certificate: InputFile, optional

        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS, defaults to None
        :type ip_address: str, optional

        :param max_connections: Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100. Defaults to *40*. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput., defaults to None
        :type max_connections: int, optional

        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify [???message???, ???edited_channel_post???, ???callback_query???] to only receive updates of these types. See [Update](https://core.telegram.org/bots/api/#update) for a complete list of available update types. Specify an empty list to receive all update types except *chat_member* (default). If not specified, the previous setting will be used.
Please note that this parameter doesn't affect updates created before the call to the setWebhook, so unwanted updates may be received for a short period of time., defaults to None
        :type allowed_updates: list[str], optional

        :param drop_pending_updates: Pass *True* to drop all pending updates, defaults to None
        :type drop_pending_updates: bool, optional

        """
        return await self.__make_request(
            "setWebhook",
            data={
                "url": url,
                "certificate": certificate,
                "ip_address": ip_address,
                "max_connections": max_connections,
                "allowed_updates": allowed_updates,
                "drop_pending_updates": drop_pending_updates,
            },
            as_form=True,
            response_model=bool,
        )

    async def delete_webhook(
            self,
            drop_pending_updates: bool = None,
    ) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch back to [getUpdates](https://core.telegram.org/bots/api/#getupdates). Returns *True* on success.
        https://core.telegram.org/bots/api/#deletewebhook

        :param drop_pending_updates: Pass *True* to drop all pending updates, defaults to None
        :type drop_pending_updates: bool, optional

        """
        return await self.__make_request(
            "deleteWebhook",
            data={
                "drop_pending_updates": drop_pending_updates,
            },
            response_model=bool,
        )

    async def get_webhook_info(self) -> WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters. On success, returns a [WebhookInfo](https://core.telegram.org/bots/api/#webhookinfo) object. If the bot is using [getUpdates](https://core.telegram.org/bots/api/#getupdates), will return an object with the *url* field empty.
        https://core.telegram.org/bots/api/#getwebhookinfo
        """
        return await self.__make_request(
            "getWebhookInfo",
            response_model=WebhookInfo,
        )

    async def get_me(self) -> User:
        """
        A simple method for testing your bot's authentication token. Requires no parameters. Returns basic information about the bot in form of a [User](https://core.telegram.org/bots/api/#user) object.
        https://core.telegram.org/bots/api/#getme
        """
        return await self.__make_request(
            "getMe",
            response_model=User,
        )

    async def log_out(self) -> bool:
        """
        Use this method to log out from the cloud Bot API server before launching the bot locally. You **must** log out the bot before running it locally, otherwise there is no guarantee that the bot will receive updates. After a successful call, you can immediately log in on a local server, but will not be able to log in back to the cloud Bot API server for 10 minutes. Returns *True* on success. Requires no parameters.
        https://core.telegram.org/bots/api/#logout
        """
        return await self.__make_request(
            "logOut",
            response_model=bool,
        )

    async def close(self) -> bool:
        """
        Use this method to close the bot instance before moving it from one local server to another. You need to delete the webhook before calling this method to ensure that the bot isn't launched again after server restart. The method will return error 429 in the first 10 minutes after the bot is launched. Returns *True* on success. Requires no parameters.
        https://core.telegram.org/bots/api/#close
        """
        return await self.__make_request(
            "close",
            response_model=bool,
        )

    async def send_message(
            self,
            chat_id: typing.Union[int, str],
            text: str,
            parse_mode: str = 'HTML',
            entities: list[MessageEntity] = None,
            disable_web_page_preview: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send text messages. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param text: Text of the message to be sent, 1-4096 characters after entities parsing
        :type text: str

        :param parse_mode: Mode for parsing entities in the message text. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*, defaults to None
        :type entities: list[MessageEntity], optional

        :param disable_web_page_preview: Disables link previews for links in this message, defaults to None
        :type disable_web_page_preview: bool, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendMessage",
            data={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "entities": entities,
                "disable_web_page_preview": disable_web_page_preview,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def forward_message(
            self,
            chat_id: typing.Union[int, str],
            from_chat_id: typing.Union[int, str],
            message_id: int,
            disable_notification: bool = None,
    ) -> Message:
        """
        Use this method to forward messages of any kind. Service messages can't be forwarded. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#forwardmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format `@channelusername`)
        :type from_chat_id: typing.Union[int, str]

        :param message_id: Message identifier in the chat specified in *from_chat_id*
        :type message_id: int

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        """
        return await self.__make_request(
            "forwardMessage",
            data={
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
                "disable_notification": disable_notification,
            },
            response_model=Message,
        )

    async def copy_message(
            self,
            chat_id: typing.Union[int, str],
            from_chat_id: typing.Union[int, str],
            message_id: int,
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> MessageId:
        """
        Use this method to copy messages of any kind. Service messages and invoice messages can't be copied. The method is analogous to the method [forwardMessage](https://core.telegram.org/bots/api/#forwardmessage), but the copied message doesn't have a link to the original message. Returns the [MessageId](https://core.telegram.org/bots/api/#messageid) of the sent message on success.
        https://core.telegram.org/bots/api/#copymessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format `@channelusername`)
        :type from_chat_id: typing.Union[int, str]

        :param message_id: Message identifier in the chat specified in *from_chat_id*
        :type message_id: int

        :param caption: New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the new caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "copyMessage",
            data={
                "chat_id": chat_id,
                "from_chat_id": from_chat_id,
                "message_id": message_id,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=MessageId,
        )

    async def send_photo(
            self,
            chat_id: typing.Union[int, str],
            photo: typing.Union[InputFile, str],
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send photos. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type photo: typing.Union[InputFile, str]

        :param caption: Photo caption (may also be used when resending photos by *file_id*), 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the photo caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendPhoto",
            data={
                "chat_id": chat_id,
                "photo": photo,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_audio(
            self,
            chat_id: typing.Union[int, str],
            audio: typing.Union[InputFile, str],
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            duration: int = None,
            performer: str = None,
            title: str = None,
            thumb: typing.Union[InputFile, str] = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .MP3 or .M4A format. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned. Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.

For sending voice messages, use the [sendVoice](https://core.telegram.org/bots/api/#sendvoice) method instead.
        https://core.telegram.org/bots/api/#sendaudio

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param audio: Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type audio: typing.Union[InputFile, str]

        :param caption: Audio caption, 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the audio caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param duration: Duration of the audio in seconds, defaults to None
        :type duration: int, optional

        :param performer: Performer, defaults to None
        :type performer: str, optional

        :param title: Track name, defaults to None
        :type title: str, optional

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass ???attach://_file_attach_name_??? if the thumbnail was uploaded using multipart/form-data under _file_attach_name_. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type thumb: typing.Union[InputFile, str], optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendAudio",
            data={
                "chat_id": chat_id,
                "audio": audio,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "duration": duration,
                "performer": performer,
                "title": title,
                "thumb": thumb,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_document(
            self,
            chat_id: typing.Union[int, str],
            document: typing.Union[InputFile, str],
            thumb: typing.Union[InputFile, str] = None,
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            disable_content_type_detection: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send general files. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned. Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.
        https://core.telegram.org/bots/api/#senddocument

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param document: File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type document: typing.Union[InputFile, str]

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass ???attach://_file_attach_name_??? if the thumbnail was uploaded using multipart/form-data under _file_attach_name_. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type thumb: typing.Union[InputFile, str], optional

        :param caption: Document caption (may also be used when resending documents by *file_id*), 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the document caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data, defaults to None
        :type disable_content_type_detection: bool, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendDocument",
            data={
                "chat_id": chat_id,
                "document": document,
                "thumb": thumb,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "disable_content_type_detection": disable_content_type_detection,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_video(
            self,
            chat_id: typing.Union[int, str],
            video: typing.Union[InputFile, str],
            duration: int = None,
            width: int = None,
            height: int = None,
            thumb: typing.Union[InputFile, str] = None,
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            supports_streaming: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as [Document](https://core.telegram.org/bots/api/#document)). On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned. Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.
        https://core.telegram.org/bots/api/#sendvideo

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param video: Video to send. Pass a file_id as String to send a video that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a video from the Internet, or upload a new video using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type video: typing.Union[InputFile, str]

        :param duration: Duration of sent video in seconds, defaults to None
        :type duration: int, optional

        :param width: Video width, defaults to None
        :type width: int, optional

        :param height: Video height, defaults to None
        :type height: int, optional

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass ???attach://_file_attach_name_??? if the thumbnail was uploaded using multipart/form-data under _file_attach_name_. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type thumb: typing.Union[InputFile, str], optional

        :param caption: Video caption (may also be used when resending videos by *file_id*), 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the video caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param supports_streaming: Pass *True*, if the uploaded video is suitable for streaming, defaults to None
        :type supports_streaming: bool, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendVideo",
            data={
                "chat_id": chat_id,
                "video": video,
                "duration": duration,
                "width": width,
                "height": height,
                "thumb": thumb,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "supports_streaming": supports_streaming,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_animation(
            self,
            chat_id: typing.Union[int, str],
            animation: typing.Union[InputFile, str],
            duration: int = None,
            width: int = None,
            height: int = None,
            thumb: typing.Union[InputFile, str] = None,
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound). On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.
        https://core.telegram.org/bots/api/#sendanimation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param animation: Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type animation: typing.Union[InputFile, str]

        :param duration: Duration of sent animation in seconds, defaults to None
        :type duration: int, optional

        :param width: Animation width, defaults to None
        :type width: int, optional

        :param height: Animation height, defaults to None
        :type height: int, optional

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass ???attach://_file_attach_name_??? if the thumbnail was uploaded using multipart/form-data under _file_attach_name_. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type thumb: typing.Union[InputFile, str], optional

        :param caption: Animation caption (may also be used when resending animation by *file_id*), 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the animation caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendAnimation",
            data={
                "chat_id": chat_id,
                "animation": animation,
                "duration": duration,
                "width": width,
                "height": height,
                "thumb": thumb,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_voice(
            self,
            chat_id: typing.Union[int, str],
            voice: typing.Union[InputFile, str],
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            duration: int = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as [Audio](https://core.telegram.org/bots/api/#audio) or [Document](https://core.telegram.org/bots/api/#document)). On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.
        https://core.telegram.org/bots/api/#sendvoice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type voice: typing.Union[InputFile, str]

        :param caption: Voice message caption, 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the voice message caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param duration: Duration of the voice message in seconds, defaults to None
        :type duration: int, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendVoice",
            data={
                "chat_id": chat_id,
                "voice": voice,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "duration": duration,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_video_note(
            self,
            chat_id: typing.Union[int, str],
            video_note: typing.Union[InputFile, str],
            duration: int = None,
            length: int = None,
            thumb: typing.Union[InputFile, str] = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        As of [v.4.0](https://telegram.org/blog/video-messages-and-telescope), Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send video messages. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendvideonote

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param video_note: Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended) or upload a new video using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files). Sending video notes by a URL is currently unsupported
        :type video_note: typing.Union[InputFile, str]

        :param duration: Duration of sent video in seconds, defaults to None
        :type duration: int, optional

        :param length: Video width and height, i.e. diameter of the video message, defaults to None
        :type length: int, optional

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass ???attach://_file_attach_name_??? if the thumbnail was uploaded using multipart/form-data under _file_attach_name_. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type thumb: typing.Union[InputFile, str], optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendVideoNote",
            data={
                "chat_id": chat_id,
                "video_note": video_note,
                "duration": duration,
                "length": length,
                "thumb": thumb,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def send_media_group(
            self,
            chat_id: typing.Union[int, str],
            media: list[typing.Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]],
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
    ) -> list[Message]:
        """
        Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files can be only grouped in an album with messages of the same type. On success, an array of [Messages](https://core.telegram.org/bots/api/#message) that were sent is returned.
        https://core.telegram.org/bots/api/#sendmediagroup

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param media: A JSON-serialized array describing messages to be sent, must include 2-10 items
        :type media: list[typing.Union[InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo]]

        :param disable_notification: Sends messages [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the messages are a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        """
        return await self.__make_request(
            "sendMediaGroup",
            data={
                "chat_id": chat_id,
                "media": media,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
            },
            as_form=True,
            response_model=list[Message],
        )

    async def send_location(
            self,
            chat_id: typing.Union[int, str],
            latitude: float,
            longitude: float,
            horizontal_accuracy: float = None,
            live_period: int = None,
            heading: int = None,
            proximity_alert_radius: int = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send point on the map. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendlocation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param latitude: Latitude of the location
        :type latitude: float

        :param longitude: Longitude of the location
        :type longitude: float

        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500, defaults to None
        :type horizontal_accuracy: float, optional

        :param live_period: Period in seconds for which the location will be updated (see [Live Locations](https://telegram.org/blog/live-locations), should be between 60 and 86400., defaults to None
        :type live_period: int, optional

        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified., defaults to None
        :type heading: int, optional

        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified., defaults to None
        :type proximity_alert_radius: int, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendLocation",
            data={
                "chat_id": chat_id,
                "latitude": latitude,
                "longitude": longitude,
                "horizontal_accuracy": horizontal_accuracy,
                "live_period": live_period,
                "heading": heading,
                "proximity_alert_radius": proximity_alert_radius,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def edit_message_live_location(
            self,
            latitude: float,
            longitude: float,
            chat_id: typing.Union[int, str] = None,
            message_id: int = None,
            inline_message_id: str = None,
            horizontal_accuracy: float = None,
            heading: int = None,
            proximity_alert_radius: int = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to edit live location messages. A location can be edited until its *live_period* expires or editing is explicitly disabled by a call to [stopMessageLiveLocation](https://core.telegram.org/bots/api/#stopmessagelivelocation). On success, if the edited message is not an inline message, the edited [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned.
        https://core.telegram.org/bots/api/#editmessagelivelocation

        :param latitude: Latitude of new location
        :type latitude: float

        :param longitude: Longitude of new location
        :type longitude: float

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format `@channelusername`), defaults to None
        :type chat_id: typing.Union[int, str], optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500, defaults to None
        :type horizontal_accuracy: float, optional

        :param heading: Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified., defaults to None
        :type heading: int, optional

        :param proximity_alert_radius: Maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified., defaults to None
        :type proximity_alert_radius: int, optional

        :param reply_markup: A JSON-serialized object for a new [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "editMessageLiveLocation",
            data={
                "latitude": latitude,
                "longitude": longitude,
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
                "horizontal_accuracy": horizontal_accuracy,
                "heading": heading,
                "proximity_alert_radius": proximity_alert_radius,
                "reply_markup": reply_markup,
            },
            response_model=typing.Union[Message, bool],
        )

    async def stop_message_live_location(
            self,
            chat_id: typing.Union[int, str] = None,
            message_id: int = None,
            inline_message_id: str = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to stop updating a live location message before *live_period* expires. On success, if the message is not an inline message, the edited [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned.
        https://core.telegram.org/bots/api/#stopmessagelivelocation

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format `@channelusername`), defaults to None
        :type chat_id: typing.Union[int, str], optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message with live location to stop, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        :param reply_markup: A JSON-serialized object for a new [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "stopMessageLiveLocation",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
                "reply_markup": reply_markup,
            },
            response_model=typing.Union[Message, bool],
        )

    async def send_venue(
            self,
            chat_id: typing.Union[int, str],
            latitude: float,
            longitude: float,
            title: str,
            address: str,
            foursquare_id: str = None,
            foursquare_type: str = None,
            google_place_id: str = None,
            google_place_type: str = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send information about a venue. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendvenue

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param latitude: Latitude of the venue
        :type latitude: float

        :param longitude: Longitude of the venue
        :type longitude: float

        :param title: Name of the venue
        :type title: str

        :param address: Address of the venue
        :type address: str

        :param foursquare_id: Foursquare identifier of the venue, defaults to None
        :type foursquare_id: str, optional

        :param foursquare_type: Foursquare type of the venue, if known. (For example, ???arts_entertainment/default???, ???arts_entertainment/aquarium??? or ???food/icecream???.), defaults to None
        :type foursquare_type: str, optional

        :param google_place_id: Google Places identifier of the venue, defaults to None
        :type google_place_id: str, optional

        :param google_place_type: Google Places type of the venue. (See [supported types](https://developers.google.com/places/web-service/supported_types).), defaults to None
        :type google_place_type: str, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendVenue",
            data={
                "chat_id": chat_id,
                "latitude": latitude,
                "longitude": longitude,
                "title": title,
                "address": address,
                "foursquare_id": foursquare_id,
                "foursquare_type": foursquare_type,
                "google_place_id": google_place_id,
                "google_place_type": google_place_type,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def send_contact(
            self,
            chat_id: typing.Union[int, str],
            phone_number: str,
            first_name: str,
            last_name: str = None,
            vcard: str = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send phone contacts. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendcontact

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param phone_number: Contact's phone number
        :type phone_number: str

        :param first_name: Contact's first name
        :type first_name: str

        :param last_name: Contact's last name, defaults to None
        :type last_name: str, optional

        :param vcard: Additional data about the contact in the form of a [vCard](https://en.wikipedia.org/wiki/VCard), 0-2048 bytes, defaults to None
        :type vcard: str, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendContact",
            data={
                "chat_id": chat_id,
                "phone_number": phone_number,
                "first_name": first_name,
                "last_name": last_name,
                "vcard": vcard,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def send_poll(
            self,
            chat_id: typing.Union[int, str],
            question: str,
            options: list[str],
            is_anonymous: bool = True,
            type_: str = "regular",
            allows_multiple_answers: bool = False,
            correct_option_id: int = None,
            explanation: str = None,
            explanation_parse_mode: str = 'HTML',
            explanation_entities: list[MessageEntity] = None,
            open_period: int = None,
            close_date: int = None,
            is_closed: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send a native poll. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendpoll

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param question: Poll question, 1-300 characters
        :type question: str

        :param options: A JSON-serialized list of answer options, 2-10 strings 1-100 characters each
        :type options: list[str]

        :param is_anonymous: True, if the poll needs to be anonymous, defaults to *True*, defaults to None
        :type is_anonymous: bool, optional

        :param type_: Poll type, ???quiz??? or ???regular???, defaults to ???regular???, defaults to None
        :type type_: str, optional

        :param allows_multiple_answers: True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to *False*, defaults to None
        :type allows_multiple_answers: bool, optional

        :param correct_option_id: 0-based identifier of the correct answer option, required for polls in quiz mode, defaults to None
        :type correct_option_id: int, optional

        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing, defaults to None
        :type explanation: str, optional

        :param explanation_parse_mode: Mode for parsing entities in the explanation. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type explanation_parse_mode: str, optional

        :param explanation_entities: A JSON-serialized list of special entities that appear in the poll explanation, which can be specified instead of *parse_mode*, defaults to None
        :type explanation_entities: list[MessageEntity], optional

        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with *close_date*., defaults to None
        :type open_period: int, optional

        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed. Must be at least 5 and no more than 600 seconds in the future. Can't be used together with *open_period*., defaults to None
        :type close_date: int, optional

        :param is_closed: Pass *True*, if the poll needs to be immediately closed. This can be useful for poll preview., defaults to None
        :type is_closed: bool, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendPoll",
            data={
                "chat_id": chat_id,
                "question": question,
                "options": options,
                "is_anonymous": is_anonymous,
                "type": type_,
                "allows_multiple_answers": allows_multiple_answers,
                "correct_option_id": correct_option_id,
                "explanation": explanation,
                "explanation_parse_mode": explanation_parse_mode,
                "explanation_entities": explanation_entities,
                "open_period": open_period,
                "close_date": close_date,
                "is_closed": is_closed,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def send_dice(
            self,
            chat_id: typing.Union[int, str],
            emoji: str = "????",
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send an animated emoji that will display a random value. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#senddice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of ??????????, ??????????, ??????????, ?????????, ??????????, or ??????????. Dice can have values 1-6 for ??????????, ?????????? and ??????????, values 1-5 for ?????????? and ?????????, and values 1-64 for ??????????. Defaults to ??????????, defaults to None
        :type emoji: str, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendDice",
            data={
                "chat_id": chat_id,
                "emoji": emoji,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def send_chat_action(
            self,
            chat_id: typing.Union[int, str],
            action: str,
    ) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side. The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status). Returns *True* on success.

Example: The [ImageBot](https://t.me/imagebot) needs some time to process a request and upload the image. Instead of sending a text message along the lines of ???Retrieving image, please wait??????, the bot may use [sendChatAction](https://core.telegram.org/bots/api/#sendchataction) with *action* = *upload_photo*. The user will see a ???sending photo??? status for the bot.

We only recommend using this method when a response from the bot will take a **noticeable** amount of time to arrive.
        https://core.telegram.org/bots/api/#sendchataction

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param action: Type of action to broadcast. Choose one, depending on what the user is about to receive: *typing* for [text messages](https://core.telegram.org/bots/api/#sendmessage), *upload_photo* for [photos](https://core.telegram.org/bots/api/#sendphoto), *record_video* or *upload_video* for [videos](https://core.telegram.org/bots/api/#sendvideo), *record_voice* or *upload_voice* for [voice notes](https://core.telegram.org/bots/api/#sendvoice), *upload_document* for [general files](https://core.telegram.org/bots/api/#senddocument), *find_location* for [location data](https://core.telegram.org/bots/api/#sendlocation), *record_video_note* or *upload_video_note* for [video notes](https://core.telegram.org/bots/api/#sendvideonote).
        :type action: str

        """
        return await self.__make_request(
            "sendChatAction",
            data={
                "chat_id": chat_id,
                "action": action,
            },
            response_model=bool,
        )

    async def get_user_profile_photos(
            self,
            user_id: int,
            offset: int = None,
            limit: int = 100,
    ) -> UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. Returns a [UserProfilePhotos](https://core.telegram.org/bots/api/#userprofilephotos) object.
        https://core.telegram.org/bots/api/#getuserprofilephotos

        :param user_id: Unique identifier of the target user
        :type user_id: int

        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned., defaults to None
        :type offset: int, optional

        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100., defaults to None
        :type limit: int, optional

        """
        return await self.__make_request(
            "getUserProfilePhotos",
            data={
                "user_id": user_id,
                "offset": offset,
                "limit": limit,
            },
            response_model=UserProfilePhotos,
        )

    async def get_file(
            self,
            file_id: str,
    ) -> File:
        """
        Use this method to get basic info about a file and prepare it for downloading. For the moment, bots can download files of up to 20MB in size. On success, a [File](https://core.telegram.org/bots/api/#file) object is returned. The file can then be downloaded via the link `https://api.telegram.org/file/bot&lt;token&gt;/&lt;file_path&gt;`, where `&lt;file_path&gt;` is taken from the response. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling [getFile](https://core.telegram.org/bots/api/#getfile) again.
        https://core.telegram.org/bots/api/#getfile

        :param file_id: File identifier to get info about
        :type file_id: str

        """
        return await self.__make_request(
            "getFile",
            data={
                "file_id": file_id,
            },
            response_model=File,
        )

    async def ban_chat_member(
            self,
            chat_id: typing.Union[int, str],
            user_id: int,
            until_date: int = None,
            revoke_messages: bool = None,
    ) -> bool:
        """
        Use this method to ban a user in a group, a supergroup or a channel. In the case of supergroups and channels, the user will not be able to return to the chat on their own using invite links, etc., unless [unbanned](https://core.telegram.org/bots/api/#unbanchatmember) first. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns *True* on success.
        https://core.telegram.org/bots/api/#banchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param user_id: Unique identifier of the target user
        :type user_id: int

        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or less than 30 seconds from the current time they are considered to be banned forever. Applied for supergroups and channels only., defaults to None
        :type until_date: int, optional

        :param revoke_messages: Pass *True* to delete all messages from the chat for the user that is being removed. If *False*, the user will be able to see messages in the group that were sent before the user was removed. Always *True* for supergroups and channels., defaults to None
        :type revoke_messages: bool, optional

        """
        return await self.__make_request(
            "banChatMember",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "until_date": until_date,
                "revoke_messages": revoke_messages,
            },
            response_model=bool,
        )

    async def unban_chat_member(
            self,
            chat_id: typing.Union[int, str],
            user_id: int,
            only_if_banned: bool = None,
    ) -> bool:
        """
        Use this method to unban a previously banned user in a supergroup or channel. The user will **not** return to the group or channel automatically, but will be able to join via link, etc. The bot must be an administrator for this to work. By default, this method guarantees that after the call the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat they will also be **removed** from the chat. If you don't want this, use the parameter *only_if_banned*. Returns *True* on success.
        https://core.telegram.org/bots/api/#unbanchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel (in the format `@username`)
        :type chat_id: typing.Union[int, str]

        :param user_id: Unique identifier of the target user
        :type user_id: int

        :param only_if_banned: Do nothing if the user is not banned, defaults to None
        :type only_if_banned: bool, optional

        """
        return await self.__make_request(
            "unbanChatMember",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "only_if_banned": only_if_banned,
            },
            response_model=bool,
        )

    async def restrict_chat_member(
            self,
            chat_id: typing.Union[int, str],
            user_id: int,
            permissions: ChatPermissions,
            until_date: int = None,
    ) -> bool:
        """
        Use this method to restrict a user in a supergroup. The bot must be an administrator in the supergroup for this to work and must have the appropriate admin rights. Pass *True* for all permissions to lift restrictions from a user. Returns *True* on success.
        https://core.telegram.org/bots/api/#restrictchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
        :type chat_id: typing.Union[int, str]

        :param user_id: Unique identifier of the target user
        :type user_id: int

        :param permissions: A JSON-serialized object for new user permissions
        :type permissions: ChatPermissions

        :param until_date: Date when restrictions will be lifted for the user, unix time. If user is restricted for more than 366 days or less than 30 seconds from the current time, they are considered to be restricted forever, defaults to None
        :type until_date: int, optional

        """
        return await self.__make_request(
            "restrictChatMember",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "permissions": permissions,
                "until_date": until_date,
            },
            response_model=bool,
        )

    async def promote_chat_member(
            self,
            chat_id: typing.Union[int, str],
            user_id: int,
            is_anonymous: bool = None,
            can_manage_chat: bool = None,
            can_post_messages: bool = None,
            can_edit_messages: bool = None,
            can_delete_messages: bool = None,
            can_manage_voice_chats: bool = None,
            can_restrict_members: bool = None,
            can_promote_members: bool = None,
            can_change_info: bool = None,
            can_invite_users: bool = None,
            can_pin_messages: bool = None,
    ) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Pass *False* for all boolean parameters to demote a user. Returns *True* on success.
        https://core.telegram.org/bots/api/#promotechatmember

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param user_id: Unique identifier of the target user
        :type user_id: int

        :param is_anonymous: Pass *True*, if the administrator's presence in the chat is hidden, defaults to None
        :type is_anonymous: bool, optional

        :param can_manage_chat: Pass True, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege, defaults to None
        :type can_manage_chat: bool, optional

        :param can_post_messages: Pass True, if the administrator can create channel posts, channels only, defaults to None
        :type can_post_messages: bool, optional

        :param can_edit_messages: Pass True, if the administrator can edit messages of other users and can pin messages, channels only, defaults to None
        :type can_edit_messages: bool, optional

        :param can_delete_messages: Pass True, if the administrator can delete messages of other users, defaults to None
        :type can_delete_messages: bool, optional

        :param can_manage_voice_chats: Pass True, if the administrator can manage voice chats, defaults to None
        :type can_manage_voice_chats: bool, optional

        :param can_restrict_members: Pass True, if the administrator can restrict, ban or unban chat members, defaults to None
        :type can_restrict_members: bool, optional

        :param can_promote_members: Pass True, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by him), defaults to None
        :type can_promote_members: bool, optional

        :param can_change_info: Pass True, if the administrator can change chat title, photo and other settings, defaults to None
        :type can_change_info: bool, optional

        :param can_invite_users: Pass True, if the administrator can invite new users to the chat, defaults to None
        :type can_invite_users: bool, optional

        :param can_pin_messages: Pass True, if the administrator can pin messages, supergroups only, defaults to None
        :type can_pin_messages: bool, optional

        """
        return await self.__make_request(
            "promoteChatMember",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "is_anonymous": is_anonymous,
                "can_manage_chat": can_manage_chat,
                "can_post_messages": can_post_messages,
                "can_edit_messages": can_edit_messages,
                "can_delete_messages": can_delete_messages,
                "can_manage_voice_chats": can_manage_voice_chats,
                "can_restrict_members": can_restrict_members,
                "can_promote_members": can_promote_members,
                "can_change_info": can_change_info,
                "can_invite_users": can_invite_users,
                "can_pin_messages": can_pin_messages,
            },
            response_model=bool,
        )

    async def set_chat_administrator_custom_title(
            self,
            chat_id: typing.Union[int, str],
            user_id: int,
            custom_title: str,
    ) -> bool:
        """
        Use this method to set a custom title for an administrator in a supergroup promoted by the bot. Returns *True* on success.
        https://core.telegram.org/bots/api/#setchatadministratorcustomtitle

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
        :type chat_id: typing.Union[int, str]

        :param user_id: Unique identifier of the target user
        :type user_id: int

        :param custom_title: New custom title for the administrator; 0-16 characters, emoji are not allowed
        :type custom_title: str

        """
        return await self.__make_request(
            "setChatAdministratorCustomTitle",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
                "custom_title": custom_title,
            },
            response_model=bool,
        )

    async def set_chat_permissions(
            self,
            chat_id: typing.Union[int, str],
            permissions: ChatPermissions,
    ) -> bool:
        """
        Use this method to set default chat permissions for all members. The bot must be an administrator in the group or a supergroup for this to work and must have the *can_restrict_members* admin rights. Returns *True* on success.
        https://core.telegram.org/bots/api/#setchatpermissions

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
        :type chat_id: typing.Union[int, str]

        :param permissions: A JSON-serialized object for new default chat permissions
        :type permissions: ChatPermissions

        """
        return await self.__make_request(
            "setChatPermissions",
            data={
                "chat_id": chat_id,
                "permissions": permissions,
            },
            response_model=bool,
        )

    async def export_chat_invite_link(
            self,
            chat_id: typing.Union[int, str],
    ) -> str:
        """
        Use this method to generate a new primary invite link for a chat; any previously generated primary link is revoked. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the new invite link as *String* on success.
        https://core.telegram.org/bots/api/#exportchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "exportChatInviteLink",
            data={
                "chat_id": chat_id,
            },
            response_model=str,
        )

    async def create_chat_invite_link(
            self,
            chat_id: typing.Union[int, str],
            expire_date: int = None,
            member_limit: int = None,
    ) -> ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. The link can be revoked using the method [revokeChatInviteLink](https://core.telegram.org/bots/api/#revokechatinvitelink). Returns the new invite link as [ChatInviteLink](https://core.telegram.org/bots/api/#chatinvitelink) object.
        https://core.telegram.org/bots/api/#createchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param expire_date: Point in time (Unix timestamp) when the link will expire, defaults to None
        :type expire_date: int, optional

        :param member_limit: Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999, defaults to None
        :type member_limit: int, optional

        """
        return await self.__make_request(
            "createChatInviteLink",
            data={
                "chat_id": chat_id,
                "expire_date": expire_date,
                "member_limit": member_limit,
            },
            response_model=ChatInviteLink,
        )

    async def edit_chat_invite_link(
            self,
            chat_id: typing.Union[int, str],
            invite_link: str,
            expire_date: int = None,
            member_limit: int = None,
    ) -> ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the edited invite link as a [ChatInviteLink](https://core.telegram.org/bots/api/#chatinvitelink) object.
        https://core.telegram.org/bots/api/#editchatinvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param invite_link: The invite link to edit
        :type invite_link: str

        :param expire_date: Point in time (Unix timestamp) when the link will expire, defaults to None
        :type expire_date: int, optional

        :param member_limit: Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999, defaults to None
        :type member_limit: int, optional

        """
        return await self.__make_request(
            "editChatInviteLink",
            data={
                "chat_id": chat_id,
                "invite_link": invite_link,
                "expire_date": expire_date,
                "member_limit": member_limit,
            },
            response_model=ChatInviteLink,
        )

    async def revoke_chat_invite_link(
            self,
            chat_id: typing.Union[int, str],
            invite_link: str,
    ) -> ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot. If the primary link is revoked, a new link is automatically generated. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns the revoked invite link as [ChatInviteLink](https://core.telegram.org/bots/api/#chatinvitelink) object.
        https://core.telegram.org/bots/api/#revokechatinvitelink

        :param chat_id: Unique identifier of the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param invite_link: The invite link to revoke
        :type invite_link: str

        """
        return await self.__make_request(
            "revokeChatInviteLink",
            data={
                "chat_id": chat_id,
                "invite_link": invite_link,
            },
            response_model=ChatInviteLink,
        )

    async def set_chat_photo(
            self,
            chat_id: typing.Union[int, str],
            photo: InputFile,
    ) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns *True* on success.
        https://core.telegram.org/bots/api/#setchatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param photo: New chat photo, uploaded using multipart/form-data
        :type photo: InputFile

        """
        return await self.__make_request(
            "setChatPhoto",
            data={
                "chat_id": chat_id,
                "photo": photo,
            },
            as_form=True,
            response_model=bool,
        )

    async def delete_chat_photo(
            self,
            chat_id: typing.Union[int, str],
    ) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns *True* on success.
        https://core.telegram.org/bots/api/#deletechatphoto

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "deleteChatPhoto",
            data={
                "chat_id": chat_id,
            },
            response_model=bool,
        )

    async def set_chat_title(
            self,
            chat_id: typing.Union[int, str],
            title: str,
    ) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns *True* on success.
        https://core.telegram.org/bots/api/#setchattitle

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param title: New chat title, 1-255 characters
        :type title: str

        """
        return await self.__make_request(
            "setChatTitle",
            data={
                "chat_id": chat_id,
                "title": title,
            },
            response_model=bool,
        )

    async def set_chat_description(
            self,
            chat_id: typing.Union[int, str],
            description: str = None,
    ) -> bool:
        """
        Use this method to change the description of a group, a supergroup or a channel. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Returns *True* on success.
        https://core.telegram.org/bots/api/#setchatdescription

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param description: New chat description, 0-255 characters, defaults to None
        :type description: str, optional

        """
        return await self.__make_request(
            "setChatDescription",
            data={
                "chat_id": chat_id,
                "description": description,
            },
            response_model=bool,
        )

    async def pin_chat_message(
            self,
            chat_id: typing.Union[int, str],
            message_id: int,
            disable_notification: bool = None,
    ) -> bool:
        """
        Use this method to add a message to the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in a supergroup or 'can_edit_messages' admin right in a channel. Returns *True* on success.
        https://core.telegram.org/bots/api/#pinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param message_id: Identifier of a message to pin
        :type message_id: int

        :param disable_notification: Pass *True*, if it is not necessary to send a notification to all chat members about the new pinned message. Notifications are always disabled in channels and private chats., defaults to None
        :type disable_notification: bool, optional

        """
        return await self.__make_request(
            "pinChatMessage",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "disable_notification": disable_notification,
            },
            response_model=bool,
        )

    async def unpin_chat_message(
            self,
            chat_id: typing.Union[int, str],
            message_id: int = None,
    ) -> bool:
        """
        Use this method to remove a message from the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in a supergroup or 'can_edit_messages' admin right in a channel. Returns *True* on success.
        https://core.telegram.org/bots/api/#unpinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param message_id: Identifier of a message to unpin. If not specified, the most recent pinned message (by sending date) will be unpinned., defaults to None
        :type message_id: int, optional

        """
        return await self.__make_request(
            "unpinChatMessage",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
            },
            response_model=bool,
        )

    async def unpin_all_chat_messages(
            self,
            chat_id: typing.Union[int, str],
    ) -> bool:
        """
        Use this method to clear the list of pinned messages in a chat. If the chat is not a private chat, the bot must be an administrator in the chat for this to work and must have the 'can_pin_messages' admin right in a supergroup or 'can_edit_messages' admin right in a channel. Returns *True* on success.
        https://core.telegram.org/bots/api/#unpinallchatmessages

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "unpinAllChatMessages",
            data={
                "chat_id": chat_id,
            },
            response_model=bool,
        )

    async def leave_chat(
            self,
            chat_id: typing.Union[int, str],
    ) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns *True* on success.
        https://core.telegram.org/bots/api/#leavechat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "leaveChat",
            data={
                "chat_id": chat_id,
            },
            response_model=bool,
        )

    async def get_chat(
            self,
            chat_id: typing.Union[int, str],
    ) -> Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.). Returns a [Chat](https://core.telegram.org/bots/api/#chat) object on success.
        https://core.telegram.org/bots/api/#getchat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "getChat",
            data={
                "chat_id": chat_id,
            },
            response_model=Chat,
        )

    async def get_chat_administrators(
            self,
            chat_id: typing.Union[int, str],
    ) -> list[ChatMember]:
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of [ChatMember](https://core.telegram.org/bots/api/#chatmember) objects that contains information about all chat administrators except other bots. If the chat is a group or a supergroup and no administrators were appointed, only the creator will be returned.
        https://core.telegram.org/bots/api/#getchatadministrators

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "getChatAdministrators",
            data={
                "chat_id": chat_id,
            },
            response_model=list[ChatMember],
        )

    async def get_chat_member_count(
            self,
            chat_id: typing.Union[int, str],
    ) -> int:
        """
        Use this method to get the number of members in a chat. Returns *Int* on success.
        https://core.telegram.org/bots/api/#getchatmembercount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "getChatMemberCount",
            data={
                "chat_id": chat_id,
            },
            response_model=int,
        )

    async def get_chat_member(
            self,
            chat_id: typing.Union[int, str],
            user_id: int,
    ) -> ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a [ChatMember](https://core.telegram.org/bots/api/#chatmember) object on success.
        https://core.telegram.org/bots/api/#getchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param user_id: Unique identifier of the target user
        :type user_id: int

        """
        return await self.__make_request(
            "getChatMember",
            data={
                "chat_id": chat_id,
                "user_id": user_id,
            },
            response_model=ChatMember,
        )

    async def set_chat_sticker_set(
            self,
            chat_id: typing.Union[int, str],
            sticker_set_name: str,
    ) -> bool:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field *can_set_sticker_set* optionally returned in [getChat](https://core.telegram.org/bots/api/#getchat) requests to check if the bot can use this method. Returns *True* on success.
        https://core.telegram.org/bots/api/#setchatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
        :type chat_id: typing.Union[int, str]

        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :type sticker_set_name: str

        """
        return await self.__make_request(
            "setChatStickerSet",
            data={
                "chat_id": chat_id,
                "sticker_set_name": sticker_set_name,
            },
            response_model=bool,
        )

    async def delete_chat_sticker_set(
            self,
            chat_id: typing.Union[int, str],
    ) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat for this to work and must have the appropriate admin rights. Use the field *can_set_sticker_set* optionally returned in [getChat](https://core.telegram.org/bots/api/#getchat) requests to check if the bot can use this method. Returns *True* on success.
        https://core.telegram.org/bots/api/#deletechatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
        :type chat_id: typing.Union[int, str]

        """
        return await self.__make_request(
            "deleteChatStickerSet",
            data={
                "chat_id": chat_id,
            },
            response_model=bool,
        )

    async def answer_callback_query(
            self,
            callback_query_id: str,
            text: str = None,
            show_alert: bool = False,
            url: str = None,
            cache_time: int = 0,
    ) -> bool:
        """
        Use this method to send answers to callback queries sent from [inline keyboards](/bots#inline-keyboards-and-on-the-fly-updating). The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, *True* is returned.

Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via [@Botfather](https://t.me/botfather) and accept the terms. Otherwise, you may use links like `t.me/your_bot?start=XXXX` that open your bot with a parameter.
        https://core.telegram.org/bots/api/#answercallbackquery

        :param callback_query_id: Unique identifier for the query to be answered
        :type callback_query_id: str

        :param text: Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters, defaults to None
        :type text: str, optional

        :param show_alert: If *true*, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to *false*., defaults to None
        :type show_alert: bool, optional

        :param url: URL that will be opened by the user's client. If you have created a [Game](https://core.telegram.org/bots/api/#game) and accepted the conditions via [@Botfather](https://t.me/botfather), specify the URL that opens your game ??? note that this will only work if the query comes from a [*callback_game*](https://core.telegram.org/bots/api/#inlinekeyboardbutton) button.

Otherwise, you may use links like `t.me/your_bot?start=XXXX` that open your bot with a parameter., defaults to None
        :type url: str, optional

        :param cache_time: The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0., defaults to None
        :type cache_time: int, optional

        """
        return await self.__make_request(
            "answerCallbackQuery",
            data={
                "callback_query_id": callback_query_id,
                "text": text,
                "show_alert": show_alert,
                "url": url,
                "cache_time": cache_time,
            },
            response_model=bool,
        )

    async def set_my_commands(
            self,
            commands: list[BotCommand],
            scope: BotCommandScope = None,
            language_code: str = None,
    ) -> bool:
        """
        Use this method to change the list of the bot's commands. See [https://core.telegram.org/bots#commands](https://core.telegram.org/bots#commands) for more details about bot commands. Returns *True* on success.
        https://core.telegram.org/bots/api/#setmycommands

        :param commands: A JSON-serialized list of bot commands to be set as the list of the bot's commands. At most 100 commands can be specified.
        :type commands: list[BotCommand]

        :param scope: A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to [BotCommandScopeDefault](https://core.telegram.org/bots/api/#botcommandscopedefault)., defaults to None
        :type scope: BotCommandScope, optional

        :param language_code: A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands, defaults to None
        :type language_code: str, optional

        """
        return await self.__make_request(
            "setMyCommands",
            data={
                "commands": commands,
                "scope": scope,
                "language_code": language_code,
            },
            response_model=bool,
        )

    async def delete_my_commands(
            self,
            scope: BotCommandScope = None,
            language_code: str = None,
    ) -> bool:
        """
        Use this method to delete the list of the bot's commands for the given scope and user language. After deletion, [higher level commands](https://core.telegram.org/bots/api/#determining-list-of-commands) will be shown to affected users. Returns *True* on success.
        https://core.telegram.org/bots/api/#deletemycommands

        :param scope: A JSON-serialized object, describing scope of users for which the commands are relevant. Defaults to [BotCommandScopeDefault](https://core.telegram.org/bots/api/#botcommandscopedefault)., defaults to None
        :type scope: BotCommandScope, optional

        :param language_code: A two-letter ISO 639-1 language code. If empty, commands will be applied to all users from the given scope, for whose language there are no dedicated commands, defaults to None
        :type language_code: str, optional

        """
        return await self.__make_request(
            "deleteMyCommands",
            data={
                "scope": scope,
                "language_code": language_code,
            },
            response_model=bool,
        )

    async def get_my_commands(
            self,
            scope: BotCommandScope = None,
            language_code: str = None,
    ) -> list[BotCommand]:
        """
        Use this method to get the current list of the bot's commands for the given scope and user language. Returns Array of [BotCommand](https://core.telegram.org/bots/api/#botcommand) on success. If commands aren't set, an empty list is returned.
        https://core.telegram.org/bots/api/#getmycommands

        :param scope: A JSON-serialized object, describing scope of users. Defaults to [BotCommandScopeDefault](https://core.telegram.org/bots/api/#botcommandscopedefault)., defaults to None
        :type scope: BotCommandScope, optional

        :param language_code: A two-letter ISO 639-1 language code or an empty string, defaults to None
        :type language_code: str, optional

        """
        return await self.__make_request(
            "getMyCommands",
            data={
                "scope": scope,
                "language_code": language_code,
            },
            response_model=list[BotCommand],
        )

    async def edit_message_text(
            self,
            text: str,
            chat_id: typing.Union[int, str] = None,
            message_id: int = None,
            inline_message_id: str = None,
            parse_mode: str = 'HTML',
            entities: list[MessageEntity] = None,
            disable_web_page_preview: bool = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to edit text and [game](https://core.telegram.org/bots/api/#games) messages. On success, if the edited message is not an inline message, the edited [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned.
        https://core.telegram.org/bots/api/#editmessagetext

        :param text: New text of the message, 1-4096 characters after entities parsing
        :type text: str

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format `@channelusername`), defaults to None
        :type chat_id: typing.Union[int, str], optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        :param parse_mode: Mode for parsing entities in the message text. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param entities: A JSON-serialized list of special entities that appear in message text, which can be specified instead of *parse_mode*, defaults to None
        :type entities: list[MessageEntity], optional

        :param disable_web_page_preview: Disables link previews for links in this message, defaults to None
        :type disable_web_page_preview: bool, optional

        :param reply_markup: A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "editMessageText",
            data={
                "text": text,
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
                "parse_mode": parse_mode,
                "entities": entities,
                "disable_web_page_preview": disable_web_page_preview,
                "reply_markup": reply_markup,
            },
            response_model=typing.Union[Message, bool],
        )

    async def edit_message_caption(
            self,
            chat_id: typing.Union[int, str] = None,
            message_id: int = None,
            inline_message_id: str = None,
            caption: str = None,
            parse_mode: str = 'HTML',
            caption_entities: list[MessageEntity] = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to edit captions of messages. On success, if the edited message is not an inline message, the edited [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned.
        https://core.telegram.org/bots/api/#editmessagecaption

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format `@channelusername`), defaults to None
        :type chat_id: typing.Union[int, str], optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        :param caption: New caption of the message, 0-1024 characters after entities parsing, defaults to None
        :type caption: str, optional

        :param parse_mode: Mode for parsing entities in the message caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details., defaults to None
        :type parse_mode: str, optional

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of *parse_mode*, defaults to None
        :type caption_entities: list[MessageEntity], optional

        :param reply_markup: A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "editMessageCaption",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
                "caption": caption,
                "parse_mode": parse_mode,
                "caption_entities": caption_entities,
                "reply_markup": reply_markup,
            },
            response_model=typing.Union[Message, bool],
        )

    async def edit_message_media(
            self,
            media: InputMedia,
            chat_id: typing.Union[int, str] = None,
            message_id: int = None,
            inline_message_id: str = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to edit animation, audio, document, photo, or video messages. If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise. When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL. On success, if the edited message is not an inline message, the edited [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned.
        https://core.telegram.org/bots/api/#editmessagemedia

        :param media: A JSON-serialized object for a new media content of the message
        :type media: InputMedia

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format `@channelusername`), defaults to None
        :type chat_id: typing.Union[int, str], optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        :param reply_markup: A JSON-serialized object for a new [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "editMessageMedia",
            data={
                "media": media,
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=typing.Union[Message, bool],
        )

    async def edit_message_reply_markup(
            self,
            chat_id: typing.Union[int, str] = None,
            message_id: int = None,
            inline_message_id: str = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to edit only the reply markup of messages. On success, if the edited message is not an inline message, the edited [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned.
        https://core.telegram.org/bots/api/#editmessagereplymarkup

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat or username of the target channel (in the format `@channelusername`), defaults to None
        :type chat_id: typing.Union[int, str], optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the message to edit, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        :param reply_markup: A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "editMessageReplyMarkup",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
                "reply_markup": reply_markup,
            },
            response_model=typing.Union[Message, bool],
        )

    async def stop_poll(
            self,
            chat_id: typing.Union[int, str],
            message_id: int,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> Poll:
        """
        Use this method to stop a poll which was sent by the bot. On success, the stopped [Poll](https://core.telegram.org/bots/api/#poll) is returned.
        https://core.telegram.org/bots/api/#stoppoll

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param message_id: Identifier of the original message with the poll
        :type message_id: int

        :param reply_markup: A JSON-serialized object for a new message [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating)., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "stopPoll",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": reply_markup,
            },
            response_model=Poll,
        )

    async def delete_message(
            self,
            chat_id: typing.Union[int, str],
            message_id: int,
    ) -> bool:
        """
        Use this method to delete a message, including service messages, with the following limitations:
_ A message can only be deleted if it was sent less than 48 hours ago.
_ A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.
_ Bots can delete outgoing messages in private chats, groups, and supergroups.
_ Bots can delete incoming messages in private chats.
_ Bots granted *can_post_messages* permissions can delete outgoing messages in channels.
_ If the bot is an administrator of a group, it can delete any message there.
_ If the bot has *can_delete_messages* permission in a supergroup or a channel, it can delete any message there.
Returns *True* on success.
        https://core.telegram.org/bots/api/#deletemessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param message_id: Identifier of the message to delete
        :type message_id: int

        """
        return await self.__make_request(
            "deleteMessage",
            data={
                "chat_id": chat_id,
                "message_id": message_id,
            },
            response_model=bool,
        )

    async def send_sticker(
            self,
            chat_id: typing.Union[int, str],
            sticker: typing.Union[InputFile, str],
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: typing.Union[
                InlineKeyboardMarkup,
                ReplyKeyboardMarkup,
                ReplyKeyboardRemove,
                ForceReply
            ] = None,
    ) -> Message:
        """
        Use this method to send static .WEBP or [animated](https://telegram.org/blog/animated-stickers) .TGS stickers. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendsticker

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a .WEBP file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type sticker: typing.Union[InputFile, str]

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: Additional interface options. A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating), [custom reply keyboard](https://core.telegram.org/bots#keyboards), instructions to remove reply keyboard or to force a reply from the user., defaults to None
        :type reply_markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply], optional

        """
        return await self.__make_request(
            "sendSticker",
            data={
                "chat_id": chat_id,
                "sticker": sticker,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            as_form=True,
            response_model=Message,
        )

    async def get_sticker_set(
            self,
            name: str,
    ) -> StickerSet:
        """
        Use this method to get a sticker set. On success, a [StickerSet](https://core.telegram.org/bots/api/#stickerset) object is returned.
        https://core.telegram.org/bots/api/#getstickerset

        :param name: Name of the sticker set
        :type name: str

        """
        return await self.__make_request(
            "getStickerSet",
            data={
                "name": name,
            },
            response_model=StickerSet,
        )

    async def upload_sticker_file(
            self,
            user_id: int,
            png_sticker: InputFile,
    ) -> File:
        """
        Use this method to upload a .PNG file with a sticker for later use in *createNewStickerSet* and *addStickerToSet* methods (can be used multiple times). Returns the uploaded [File](https://core.telegram.org/bots/api/#file) on success.
        https://core.telegram.org/bots/api/#uploadstickerfile

        :param user_id: User identifier of sticker file owner
        :type user_id: int

        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files)
        :type png_sticker: InputFile

        """
        return await self.__make_request(
            "uploadStickerFile",
            data={
                "user_id": user_id,
                "png_sticker": png_sticker,
            },
            as_form=True,
            response_model=File,
        )

    async def create_new_sticker_set(
            self,
            user_id: int,
            name: str,
            title: str,
            emojis: str,
            png_sticker: typing.Union[InputFile, str] = None,
            tgs_sticker: InputFile = None,
            contains_masks: bool = None,
            mask_position: MaskPosition = None,
    ) -> bool:
        """
        Use this method to create a new sticker set owned by a user. The bot will be able to edit the sticker set thus created. You **must** use exactly one of the fields *png_sticker* or *tgs_sticker*. Returns *True* on success.
        https://core.telegram.org/bots/api/#createnewstickerset

        :param user_id: User identifier of created sticker set owner
        :type user_id: int

        :param name: Short name of sticker set, to be used in `t.me/addstickers/` URLs (e.g., *animals*). Can contain only english letters, digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in *???_by__bot username_???*. *_bot_username_* is case insensitive. 1-64 characters.
        :type name: str

        :param title: Sticker set title, 1-64 characters
        :type title: str

        :param emojis: One or more emoji corresponding to the sticker
        :type emojis: str

        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type png_sticker: typing.Union[InputFile, str], optional

        :param tgs_sticker: **TGS** animation with the sticker, uploaded using multipart/form-data. See [https://core.telegram.org/animated_stickers#technical-requirements](https://core.telegram.org/animated_stickers#technical-requirements) for technical requirements, defaults to None
        :type tgs_sticker: InputFile, optional

        :param contains_masks: Pass *True*, if a set of mask stickers should be created, defaults to None
        :type contains_masks: bool, optional

        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces, defaults to None
        :type mask_position: MaskPosition, optional

        """
        return await self.__make_request(
            "createNewStickerSet",
            data={
                "user_id": user_id,
                "name": name,
                "title": title,
                "emojis": emojis,
                "png_sticker": png_sticker,
                "tgs_sticker": tgs_sticker,
                "contains_masks": contains_masks,
                "mask_position": mask_position,
            },
            as_form=True,
            response_model=bool,
        )

    async def add_sticker_to_set(
            self,
            user_id: int,
            name: str,
            emojis: str,
            png_sticker: typing.Union[InputFile, str] = None,
            tgs_sticker: InputFile = None,
            mask_position: MaskPosition = None,
    ) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. You **must** use exactly one of the fields *png_sticker* or *tgs_sticker*. Animated stickers can be added to animated sticker sets and only to them. Animated sticker sets can have up to 50 stickers. Static sticker sets can have up to 120 stickers. Returns *True* on success.
        https://core.telegram.org/bots/api/#addstickertoset

        :param user_id: User identifier of sticker set owner
        :type user_id: int

        :param name: Sticker set name
        :type name: str

        :param emojis: One or more emoji corresponding to the sticker
        :type emojis: str

        :param png_sticker: **PNG** image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width or height must be exactly 512px. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files), defaults to None
        :type png_sticker: typing.Union[InputFile, str], optional

        :param tgs_sticker: **TGS** animation with the sticker, uploaded using multipart/form-data. See [https://core.telegram.org/animated_stickers#technical-requirements](https://core.telegram.org/animated_stickers#technical-requirements) for technical requirements, defaults to None
        :type tgs_sticker: InputFile, optional

        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces, defaults to None
        :type mask_position: MaskPosition, optional

        """
        return await self.__make_request(
            "addStickerToSet",
            data={
                "user_id": user_id,
                "name": name,
                "emojis": emojis,
                "png_sticker": png_sticker,
                "tgs_sticker": tgs_sticker,
                "mask_position": mask_position,
            },
            as_form=True,
            response_model=bool,
        )

    async def set_sticker_position_in_set(
            self,
            sticker: str,
            position: int,
    ) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a specific position. Returns *True* on success.
        https://core.telegram.org/bots/api/#setstickerpositioninset

        :param sticker: File identifier of the sticker
        :type sticker: str

        :param position: New sticker position in the set, zero-based
        :type position: int

        """
        return await self.__make_request(
            "setStickerPositionInSet",
            data={
                "sticker": sticker,
                "position": position,
            },
            response_model=bool,
        )

    async def delete_sticker_from_set(
            self,
            sticker: str,
    ) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns *True* on success.
        https://core.telegram.org/bots/api/#deletestickerfromset

        :param sticker: File identifier of the sticker
        :type sticker: str

        """
        return await self.__make_request(
            "deleteStickerFromSet",
            data={
                "sticker": sticker,
            },
            response_model=bool,
        )

    async def set_sticker_set_thumb(
            self,
            name: str,
            user_id: int,
            thumb: typing.Union[InputFile, str] = None,
    ) -> bool:
        """
        Use this method to set the thumbnail of a sticker set. Animated thumbnails can be set for animated sticker sets only. Returns *True* on success.
        https://core.telegram.org/bots/api/#setstickersetthumb

        :param name: Sticker set name
        :type name: str

        :param user_id: User identifier of the sticker set owner
        :type user_id: int

        :param thumb: A **PNG** image with the thumbnail, must be up to 128 kilobytes in size and have width and height exactly 100px, or a **TGS** animation with the thumbnail up to 32 kilobytes in size; see [https://core.telegram.org/animated_stickers#technical-requirements](https://core.telegram.org/animated_stickers#technical-requirements) for animated sticker technical requirements. Pass a *file_id* as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data. [More info on Sending Files ??](https://core.telegram.org/bots/api/#sending-files). Animated sticker set thumbnail can't be uploaded via HTTP URL., defaults to None
        :type thumb: typing.Union[InputFile, str], optional

        """
        return await self.__make_request(
            "setStickerSetThumb",
            data={
                "name": name,
                "user_id": user_id,
                "thumb": thumb,
            },
            as_form=True,
            response_model=bool,
        )

    async def answer_inline_query(
            self,
            inline_query_id: str,
            results: list[InlineQueryResult],
            cache_time: int = 300,
            is_personal: bool = None,
            next_offset: str = None,
            switch_pm_text: str = None,
            switch_pm_parameter: str = None,
    ) -> bool:
        """
        Use this method to send answers to an inline query. On success, *True* is returned.
No more than **50** results per query are allowed.
        https://core.telegram.org/bots/api/#answerinlinequery

        :param inline_query_id: Unique identifier for the answered query
        :type inline_query_id: str

        :param results: A JSON-serialized array of results for the inline query
        :type results: list[InlineQueryResult]

        :param cache_time: The maximum amount of time in seconds that the result of the inline query may be cached on the server. Defaults to 300., defaults to None
        :type cache_time: int, optional

        :param is_personal: Pass *True*, if results may be cached on the server side only for the user that sent the query. By default, results may be returned to any user who sends the same query, defaults to None
        :type is_personal: bool, optional

        :param next_offset: Pass the offset that a client should send in the next query with the same text to receive more results. Pass an empty string if there are no more results or if you don't support pagination. Offset length can't exceed 64 bytes., defaults to None
        :type next_offset: str, optional

        :param switch_pm_text: If passed, clients will display a button with specified text that switches the user to a private chat with the bot and sends the bot a start message with the parameter *switch_pm_parameter*, defaults to None
        :type switch_pm_text: str, optional

        :param switch_pm_parameter: [Deep-linking](/bots#deep-linking) parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters, only `A-Z`, `a-z`, `0-9`, `_` and `-` are allowed.

*Example:* An inline bot that sends YouTube videos can ask the user to connect the bot to their YouTube account to adapt search results accordingly. To do this, it displays a 'Connect your YouTube account' button above the results, or even before showing any. The user presses the button, switches to a private chat with the bot and, in doing so, passes a start parameter that instructs the bot to return an OAuth link. Once done, the bot can offer a [*switch_inline*](https://core.telegram.org/bots/api/#inlinekeyboardmarkup) button so that the user can easily return to the chat where they wanted to use the bot's inline capabilities., defaults to None
        :type switch_pm_parameter: str, optional

        """
        return await self.__make_request(
            "answerInlineQuery",
            data={
                "inline_query_id": inline_query_id,
                "results": results,
                "cache_time": cache_time,
                "is_personal": is_personal,
                "next_offset": next_offset,
                "switch_pm_text": switch_pm_text,
                "switch_pm_parameter": switch_pm_parameter,
            },
            response_model=bool,
        )

    async def send_invoice(
            self,
            chat_id: typing.Union[int, str],
            title: str,
            description: str,
            payload: str,
            provider_token: str,
            currency: str,
            prices: list[LabeledPrice],
            max_tip_amount: int = 0,
            suggested_tip_amounts: list[int] = None,
            start_parameter: str = None,
            provider_data: str = None,
            photo_url: str = None,
            photo_size: int = None,
            photo_width: int = None,
            photo_height: int = None,
            need_name: bool = None,
            need_phone_number: bool = None,
            need_email: bool = None,
            need_shipping_address: bool = None,
            send_phone_number_to_provider: bool = None,
            send_email_to_provider: bool = None,
            is_flexible: bool = None,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to send invoices. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendinvoice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format `@channelusername`)
        :type chat_id: typing.Union[int, str]

        :param title: Product name, 1-32 characters
        :type title: str

        :param description: Product description, 1-255 characters
        :type description: str

        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
        :type payload: str

        :param provider_token: Payments provider token, obtained via [Botfather](https://t.me/botfather)
        :type provider_token: str

        :param currency: Three-letter ISO 4217 currency code, see [more on currencies](/bots/payments#supported-currencies)
        :type currency: str

        :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :type prices: list[LabeledPrice]

        :param max_tip_amount: The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of `US$ 1.45` pass `max_tip_amount = 145`. See the *exp* parameter in [currencies.json](https://core.telegram.org/bots/payments/currencies.json), it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0, defaults to None
        :type max_tip_amount: int, optional

        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*., defaults to None
        :type suggested_tip_amounts: list[int], optional

        :param start_parameter: Unique deep-linking parameter. If left empty, **forwarded copies** of the sent message will have a *Pay* button, allowing multiple users to pay directly from the forwarded message, using the same invoice. If non-empty, forwarded copies of the sent message will have a *URL* button with a deep link to the bot (instead of a *Pay* button), with the value used as the start parameter, defaults to None
        :type start_parameter: str, optional

        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider., defaults to None
        :type provider_data: str, optional

        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for., defaults to None
        :type photo_url: str, optional

        :param photo_size: Photo size, defaults to None
        :type photo_size: int, optional

        :param photo_width: Photo width, defaults to None
        :type photo_width: int, optional

        :param photo_height: Photo height, defaults to None
        :type photo_height: int, optional

        :param need_name: Pass *True*, if you require the user's full name to complete the order, defaults to None
        :type need_name: bool, optional

        :param need_phone_number: Pass *True*, if you require the user's phone number to complete the order, defaults to None
        :type need_phone_number: bool, optional

        :param need_email: Pass *True*, if you require the user's email address to complete the order, defaults to None
        :type need_email: bool, optional

        :param need_shipping_address: Pass *True*, if you require the user's shipping address to complete the order, defaults to None
        :type need_shipping_address: bool, optional

        :param send_phone_number_to_provider: Pass *True*, if user's phone number should be sent to provider, defaults to None
        :type send_phone_number_to_provider: bool, optional

        :param send_email_to_provider: Pass *True*, if user's email address should be sent to provider, defaults to None
        :type send_email_to_provider: bool, optional

        :param is_flexible: Pass *True*, if the final price depends on the shipping method, defaults to None
        :type is_flexible: bool, optional

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating). If empty, one 'Pay `total price`' button will be shown. If not empty, the first button must be a Pay button., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "sendInvoice",
            data={
                "chat_id": chat_id,
                "title": title,
                "description": description,
                "payload": payload,
                "provider_token": provider_token,
                "currency": currency,
                "prices": prices,
                "max_tip_amount": max_tip_amount,
                "suggested_tip_amounts": suggested_tip_amounts,
                "start_parameter": start_parameter,
                "provider_data": provider_data,
                "photo_url": photo_url,
                "photo_size": photo_size,
                "photo_width": photo_width,
                "photo_height": photo_height,
                "need_name": need_name,
                "need_phone_number": need_phone_number,
                "need_email": need_email,
                "need_shipping_address": need_shipping_address,
                "send_phone_number_to_provider": send_phone_number_to_provider,
                "send_email_to_provider": send_email_to_provider,
                "is_flexible": is_flexible,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def answer_shipping_query(
            self,
            shipping_query_id: str,
            ok: bool,
            shipping_options: list[ShippingOption] = None,
            error_message: str = None,
    ) -> bool:
        """
        If you sent an invoice requesting a shipping address and the parameter *is_flexible* was specified, the Bot API will send an [Update](https://core.telegram.org/bots/api/#update) with a *shipping_query* field to the bot. Use this method to reply to shipping queries. On success, True is returned.
        https://core.telegram.org/bots/api/#answershippingquery

        :param shipping_query_id: Unique identifier for the query to be answered
        :type shipping_query_id: str

        :param ok: Specify True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)
        :type ok: bool

        :param shipping_options: Required if *ok* is True. A JSON-serialized array of available shipping options., defaults to None
        :type shipping_options: list[ShippingOption], optional

        :param error_message: Required if *ok* is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user., defaults to None
        :type error_message: str, optional

        """
        return await self.__make_request(
            "answerShippingQuery",
            data={
                "shipping_query_id": shipping_query_id,
                "ok": ok,
                "shipping_options": shipping_options,
                "error_message": error_message,
            },
            response_model=bool,
        )

    async def answer_pre_checkout_query(
            self,
            pre_checkout_query_id: str,
            ok: bool,
            error_message: str = None,
    ) -> bool:
        """
        Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an [Update](https://core.telegram.org/bots/api/#update) with the field *pre_checkout_query*. Use this method to respond to such pre-checkout queries. On success, True is returned. **Note:** The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.
        https://core.telegram.org/bots/api/#answerprecheckoutquery

        :param pre_checkout_query_id: Unique identifier for the query to be answered
        :type pre_checkout_query_id: str

        :param ok: Specify *True* if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use *False* if there are any problems.
        :type ok: bool

        :param error_message: Required if *ok* is *False*. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user., defaults to None
        :type error_message: str, optional

        """
        return await self.__make_request(
            "answerPreCheckoutQuery",
            data={
                "pre_checkout_query_id": pre_checkout_query_id,
                "ok": ok,
                "error_message": error_message,
            },
            response_model=bool,
        )

    async def set_passport_data_errors(
            self,
            user_id: int,
            errors: list[PassportElementError],
    ) -> bool:
        """
        Informs a user that some of the Telegram Passport elements they provided contains errors. The user will not be able to re-submit their Passport to you until the errors are fixed (the contents of the field for which you returned the error must change). Returns *True* on success.

Use this if the data submitted by the user doesn't satisfy the standards your service requires for any reason. For example, if a birthday date seems invalid, a submitted document is blurry, a scan shows evidence of tampering, etc. Supply some details in the error message to make sure the user knows how to correct the issues.
        https://core.telegram.org/bots/api/#setpassportdataerrors

        :param user_id: User identifier
        :type user_id: int

        :param errors: A JSON-serialized array describing the errors
        :type errors: list[PassportElementError]

        """
        return await self.__make_request(
            "setPassportDataErrors",
            data={
                "user_id": user_id,
                "errors": errors,
            },
            response_model=bool,
        )

    async def send_game(
            self,
            chat_id: int,
            game_short_name: str,
            disable_notification: bool = None,
            reply_to_message_id: int = None,
            allow_sending_without_reply: bool = None,
            reply_markup: InlineKeyboardMarkup = None,
    ) -> Message:
        """
        Use this method to send a game. On success, the sent [Message](https://core.telegram.org/bots/api/#message) is returned.
        https://core.telegram.org/bots/api/#sendgame

        :param chat_id: Unique identifier for the target chat
        :type chat_id: int

        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via [Botfather](https://t.me/botfather).
        :type game_short_name: str

        :param disable_notification: Sends the message [silently](https://telegram.org/blog/channels-2-0#silent-messages). Users will receive a notification with no sound., defaults to None
        :type disable_notification: bool, optional

        :param reply_to_message_id: If the message is a reply, ID of the original message, defaults to None
        :type reply_to_message_id: int, optional

        :param allow_sending_without_reply: Pass *True*, if the message should be sent even if the specified replied-to message is not found, defaults to None
        :type allow_sending_without_reply: bool, optional

        :param reply_markup: A JSON-serialized object for an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating). If empty, one 'Play game_title' button will be shown. If not empty, the first button must launch the game., defaults to None
        :type reply_markup: InlineKeyboardMarkup, optional

        """
        return await self.__make_request(
            "sendGame",
            data={
                "chat_id": chat_id,
                "game_short_name": game_short_name,
                "disable_notification": disable_notification,
                "reply_to_message_id": reply_to_message_id,
                "allow_sending_without_reply": allow_sending_without_reply,
                "reply_markup": reply_markup,
            },
            response_model=Message,
        )

    async def set_game_score(
            self,
            user_id: int,
            score: int,
            force: bool = None,
            disable_edit_message: bool = None,
            chat_id: int = None,
            message_id: int = None,
            inline_message_id: str = None,
    ) -> typing.Union[Message, bool]:
        """
        Use this method to set the score of the specified user in a game message. On success, if the message is not an inline message, the [Message](https://core.telegram.org/bots/api/#message) is returned, otherwise *True* is returned. Returns an error, if the new score is not greater than the user's current score in the chat and *force* is *False*.
        https://core.telegram.org/bots/api/#setgamescore

        :param user_id: User identifier
        :type user_id: int

        :param score: New score, must be non-negative
        :type score: int

        :param force: Pass True, if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters, defaults to None
        :type force: bool, optional

        :param disable_edit_message: Pass True, if the game message should not be automatically edited to include the current scoreboard, defaults to None
        :type disable_edit_message: bool, optional

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat, defaults to None
        :type chat_id: int, optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the sent message, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        """
        return await self.__make_request(
            "setGameScore",
            data={
                "user_id": user_id,
                "score": score,
                "force": force,
                "disable_edit_message": disable_edit_message,
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
            },
            response_model=typing.Union[Message, bool],
        )

    async def get_game_high_scores(
            self,
            user_id: int,
            chat_id: int = None,
            message_id: int = None,
            inline_message_id: str = None,
    ) -> list[GameHighScore]:
        """
        Use this method to get data for high score tables. Will return the score of the specified user and several of their neighbors in a game. On success, returns an *Array* of [GameHighScore](https://core.telegram.org/bots/api/#gamehighscore) objects.

This method will currently return scores for the target user, plus two of their closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them. Please note that this behavior is subject to change.
        https://core.telegram.org/bots/api/#getgamehighscores

        :param user_id: Target user id
        :type user_id: int

        :param chat_id: Required if *inline_message_id* is not specified. Unique identifier for the target chat, defaults to None
        :type chat_id: int, optional

        :param message_id: Required if *inline_message_id* is not specified. Identifier of the sent message, defaults to None
        :type message_id: int, optional

        :param inline_message_id: Required if *chat_id* and *message_id* are not specified. Identifier of the inline message, defaults to None
        :type inline_message_id: str, optional

        """
        return await self.__make_request(
            "getGameHighScores",
            data={
                "user_id": user_id,
                "chat_id": chat_id,
                "message_id": message_id,
                "inline_message_id": inline_message_id,
            },
            response_model=list[GameHighScore],
        )
