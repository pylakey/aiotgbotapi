from __future__ import annotations

import asyncio
import logging
from functools import (
    partial,
    update_wrapper,
)
from typing import (
    Any,
    Callable,
    Coroutine,
    Optional,
)

import pydantic
import uvicorn
from fastapi import FastAPI

from .bot_api_client import BotAPIClient
from .filters import (
    AnyFilterCallable,
    BaseFilter,
    CallbackQueryFilterCallable,
    ChannelPostFilterCallable,
    ChatMemberFilterCallable,
    ChosenInlineResultFilterCallable,
    EditedChannelPostFilterCallable,
    EditedMessageFilterCallable,
    InlineQueryFilterCallable,
    MessageFilterCallable,
    MyChatMemberFilterCallable,
    PollAnswerFilterCallable,
    PollFilterCallable,
    PreCheckoutQueryFilterCallable,
    ShippingQueryFilterCallable,
)
from .types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChosenInlineResult,
    InlineQuery,
    InputFile,
    Message,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
    SomeUpdate,
    Update,
)


class WebHookSettings(pydantic.BaseModel):
    # Web server settings
    server_host: str = "0.0.0.0"
    server_port: int = 8055
    # Telegram hook settings
    url: str
    certificate: InputFile = None
    ip_address: str = None
    max_connections: int = 40
    allowed_updates: list[str] = None
    drop_pending_updates: bool = None


class Bot(BotAPIClient):
    __running = False
    __updates_handlers: dict[str, set[Handler]] = {
        "message": set(),
        "edited_message": set(),
        "channel_post": set(),
        "edited_channel_post": set(),
        "inline_query": set(),
        "chosen_inline_result": set(),
        "callback_query": set(),
        "shipping_query": set(),
        "pre_checkout_query": set(),
        "poll": set(),
        "poll_answer": set(),
        "my_chat_member": set(),
        "chat_member": set(),
    }
    __middlewares: list[MiddlewareCallable] = []
    __prepared_middlewares: list[MiddlewareCallable] = []
    __webhook_app: FastAPI

    def __init__(
            self,
            bot_token: str,
            *,
            polling_timeout: int = 0,
            polling_allowed_updates: list[str] = None,
            webhook_settings: WebHookSettings = None
    ):
        super(Bot, self).__init__(bot_token)
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.bot_token = bot_token
        self.polling_timeout = polling_timeout
        self.polling_allowed_updates = polling_allowed_updates
        self.webhook_settings = webhook_settings

    def __prepare_middlewares_handlers(self):
        self.__prepared_middlewares = list(reversed(self.__middlewares))

    async def __prepare_webhook(self):
        if bool(self.webhook_settings):
            await self.set_webhook(
                url=f"{self.webhook_settings.url}/{self.bot_token.split(':')[1]}",
                certificate=self.webhook_settings.certificate,
                ip_address=self.webhook_settings.ip_address,
                max_connections=self.webhook_settings.max_connections,
                allowed_updates=self.webhook_settings.allowed_updates,
                drop_pending_updates=self.webhook_settings.drop_pending_updates,
            )
            self.__webhook_app = FastAPI(
                redoc_url=None,
                docs_url=None
            )
            self.__webhook_app.add_api_route(
                f"/{self.bot_token.split(':')[1]}",
                endpoint=self.__on_webhook_received,
                methods=["POST"]
            )
        else:
            await self.delete_webhook()

    async def __on_webhook_received(self, updates: list[Update]) -> Any:
        await self.__handle_updates(updates)

    async def __call_handler(self, handler: Handler, update: SomeUpdate):
        try:
            await handler(self, update)
        except Exception as e:
            self.logger.error(f"Unable to call handler {handler} for update: {update.json()}. {e}", exc_info=True)

    async def __call_handlers(self, update: Update):
        tasks = []

        for update_type in self.__updates_handlers.keys():
            update_field: SomeUpdate = getattr(update, update_type, None)

            if bool(update_field):
                update_field.EXTRA["bot"] = self
                tasks.extend(
                    self.__call_handler(h, update_field)
                    for h in self.__updates_handlers[update_type]
                )

        # Running all handlers concurrently and independently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def __handle_update(self, update: Update):
        if len(self.__prepared_middlewares) == 0:
            return await self.__call_handlers(update)

        async def __fn(*_, **__):
            return await self.__call_handlers(update)

        call_next = __fn

        for m in self.__prepared_middlewares:
            call_next = update_wrapper(partial(m, call_next=call_next), call_next)

        return await call_next(self, update)

    async def __handle_updates(self, updates: list[Update]):
        for update in updates:
            asyncio.create_task(self.__handle_update(update))

    async def run_webhook_server(self):
        self.logger.info('Start webhook server')

        uvicorn.run(
            self.__webhook_app,
            host=self.webhook_settings.server_host,
            port=self.webhook_settings.server_port
        )

    async def run_long_polling(self):
        self.logger.info('Start polling updates')

        last_received_update_id = -1
        try:
            while self.__running:
                updates = await self.get_updates(
                    offset=last_received_update_id + 1,
                    timeout=self.polling_timeout,
                    allowed_updates=self.polling_allowed_updates
                )

                last_received_update_id = updates[-1].update_id if len(updates) > 0 else last_received_update_id
                await asyncio.sleep(0.01)
        finally:
            self.logger.info('Stop polling')
            await self.stop()

    async def start(self):
        self.logger.info('Starting bot')
        self.__prepare_middlewares_handlers()
        await self.__prepare_webhook()
        self.__running = True

    async def stop(self):
        self.logger.info('Stopping Bot...')
        self.__running = False

    async def run(self):
        async with self:
            if bool(self.webhook_settings):
                await self.run_webhook_server()
            else:
                await self.run_long_polling()

    def add_middleware(self, middleware: MiddlewareCallable):
        if self.__running:
            raise RuntimeError("Unable to add middleware in already running bot instance!")

        self.__middlewares.append(middleware)
        return middleware

    def add_update_handler(
            self,
            function: HandlerCallable,
            update_type: str,
            *,
            filters: AnyFilterCallable = None
    ) -> Handler:
        if self.__running:
            raise RuntimeError("Unable to add middleware in already running bot instance!")

        if self.__updates_handlers.get(update_type) is None:
            raise ValueError(f'Unsupported update type: {update_type}!')

        handler = Handler(function, update_type, filters=filters)
        self.__updates_handlers[update_type].add(handler)
        return handler

    def remove_update_handler(self, handler: Handler):
        try:
            self.__updates_handlers[handler.update_type].remove(handler)
        except KeyError:
            raise ValueError(f'{handler} is not registered as handler')

    def on_update(self, update_type: str, *, filters: AnyFilterCallable = None):
        def decorator(function: HandlerCallable) -> HandlerCallable:
            self.add_update_handler(function, update_type, filters=filters)
            return function

        return decorator

    def add_message_handler(self, function: MessageHandler, *, filters: MessageFilterCallable) -> Handler:
        return self.add_update_handler(function, "message", filters=filters)

    def on_message(self, *, filters: MessageFilterCallable):
        return self.on_update('message', filters=filters)

    def add_edited_message_handler(
            self,
            function: EditedMessageHandler,
            *,
            filters: EditedMessageFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "edited_message", filters=filters)

    def on_edited_message(self, *, filters: EditedMessageFilterCallable):
        return self.on_update('edited_message', filters=filters)

    def add_channel_post_handler(self, function: ChannelPostHandler, *, filters: ChannelPostFilterCallable) -> Handler:
        return self.add_update_handler(function, "channel_post", filters=filters)

    def on_channel_post(self, *, filters: ChannelPostFilterCallable):
        return self.on_update('channel_post', filters=filters)

    def add_edited_channel_post_handler(
            self,
            function: EditedChannelPostHandler,
            *,
            filters: EditedChannelPostFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "edited_channel_post", filters=filters)

    def on_edited_channel_post(self, *, filters: EditedChannelPostFilterCallable):
        return self.on_update('edited_channel_post', filters=filters)

    def add_inline_query_handler(self, function: InlineQueryHandler, *, filters: InlineQueryFilterCallable) -> Handler:
        return self.add_update_handler(function, "inline_query", filters=filters)

    def on_inline_query(self, *, filters: InlineQueryFilterCallable):
        return self.on_update('inline_query', filters=filters)

    def add_chosen_inline_result_handler(
            self,
            function: ChosenInlineResultHandler,
            *,
            filters: ChosenInlineResultFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "chosen_inline_result", filters=filters)

    def on_chosen_inline_result(self, *, filters: ChosenInlineResultFilterCallable):
        return self.on_update('chosen_inline_result', filters=filters)

    def add_callback_query_handler(
            self,
            function: CallbackQueryHandler,
            *,
            filters: CallbackQueryFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "callback_query", filters=filters)

    def on_callback_query(self, *, filters: CallbackQueryFilterCallable):
        return self.on_update('callback_query', filters=filters)

    def add_shipping_query_handler(
            self,
            function: ShippingQueryHandler,
            *,
            filters: ShippingQueryFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "shipping_query", filters=filters)

    def on_shipping_query(self, *, filters: ShippingQueryFilterCallable):
        return self.on_update('shipping_query', filters=filters)

    def add_pre_checkout_query_handler(
            self,
            function: PreCheckoutQueryHandler,
            *,
            filters: PreCheckoutQueryFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "pre_checkout_query", filters=filters)

    def on_pre_checkout_query(self, *, filters: PreCheckoutQueryFilterCallable):
        return self.on_update('pre_checkout_query', filters=filters)

    def add_poll_handler(self, function: PollHandler, *, filters: PollFilterCallable) -> Handler:
        return self.add_update_handler(function, "poll", filters=filters)

    def on_poll(self, *, filters: PollFilterCallable):
        return self.on_update('poll', filters=filters)

    def add_poll_answer_handler(self, function: PollAnswerHandler, *, filters: PollAnswerFilterCallable) -> Handler:
        return self.add_update_handler(function, "poll_answer", filters=filters)

    def on_poll_answer(self, *, filters: PollAnswerFilterCallable):
        return self.on_update('poll_answer', filters=filters)

    def add_my_chat_member_handler(
            self,
            function: MyChatMemberHandler,
            *,
            filters: MyChatMemberFilterCallable
    ) -> Handler:
        return self.add_update_handler(function, "my_chat_member", filters=filters)

    def on_my_chat_member(self, *, filters: MyChatMemberFilterCallable):
        return self.on_update('my_chat_member', filters=filters)

    def add_chat_member_handler(self, function: ChatMemberHandler, *, filters: ChatMemberFilterCallable) -> Handler:
        return self.add_update_handler(function, "chat_member", filters=filters)

    def on_chat_member(self, *, filters: ChatMemberFilterCallable):
        return self.on_update('chat_member', filters=filters)

    # Magic methods
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


HandlerCallable = Callable[[Bot, SomeUpdate], Coroutine[Any, Any, None]]
MessageHandler = Callable[[Bot, Message], Coroutine[Any, Any, None]]
EditedMessageHandler = Callable[[Bot, Message], Coroutine[Any, Any, None]]
ChannelPostHandler = Callable[[Bot, Message], Coroutine[Any, Any, None]]
EditedChannelPostHandler = Callable[[Bot, Message], Coroutine[Any, Any, None]]
InlineQueryHandler = Callable[[Bot, InlineQuery], Coroutine[Any, Any, None]]
ChosenInlineResultHandler = Callable[[Bot, ChosenInlineResult], Coroutine[Any, Any, None]]
CallbackQueryHandler = Callable[[Bot, CallbackQuery], Coroutine[Any, Any, None]]
ShippingQueryHandler = Callable[[Bot, ShippingQuery], Coroutine[Any, Any, None]]
PreCheckoutQueryHandler = Callable[[Bot, PreCheckoutQuery], Coroutine[Any, Any, None]]
PollHandler = Callable[[Bot, Poll], Coroutine[Any, Any, None]]
PollAnswerHandler = Callable[[Bot, PollAnswer], Coroutine[Any, Any, None]]
MyChatMemberHandler = Callable[[Bot, ChatMemberUpdated], Coroutine[Any, Any, None]]
ChatMemberHandler = Callable[[Bot, ChatMemberUpdated], Coroutine[Any, Any, None]]

MiddlewareCallable = Callable[[Bot, SomeUpdate, HandlerCallable], Coroutine[Any, Any, None]]


class Handler(object):
    def __init__(
            self,
            function: HandlerCallable,
            update_type: str,
            *,
            filters: Optional[AnyFilterCallable] = None
    ):
        if filters is not None and not isinstance(filters, BaseFilter):
            raise ValueError('filters should be an instance of BaseFilter!')

        self.function = function
        self.update_type = update_type
        self.filters = filters

    async def __call__(self, client: Bot, update: SomeUpdate):
        if callable(self.filters):
            filter_result = await self.filters(update)

            if not bool(filter_result):
                return

            if isinstance(filter_result, dict):
                update.EXTRA |= filter_result

        return await self.function(client, update)

    def __hash__(self):
        return self.function.__hash__()
