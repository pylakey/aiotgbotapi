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
    Message,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
    SomeUpdate,
    Update,
)


class Bot(BotAPIClient):
    loop: asyncio.AbstractEventLoop = None
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

    def __init__(self, bot_token: str):
        super(Bot, self).__init__(bot_token)
        self.logger = logging.getLogger(self.__class__.__qualname__)
        self.bot_token = bot_token

    # Magic methods
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    def __prepare_middlewares_handlers(self):
        self.__prepared_middlewares = list(reversed(self.__middlewares))

    async def __call_handler(self, handler: Handler, update: SomeUpdate):
        try:
            await handler(self, update)
        except Exception as e:
            self.logger.error(e, exc_info=True)

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

    async def __updates_loop(self):
        try:
            last_received_update_id = -1

            while self.__running:
                updates = await self.get_updates(
                    offset=last_received_update_id + 1,
                    timeout=2
                )

                for update in updates:
                    last_received_update_id = update.update_id
                    self.loop.create_task(self.__handle_update(update))
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as e:
            self.logger.error(f'Unhandled exception occurred!. {e.__class__.__qualname__}. {e}', exc_info=True)

    async def start(self):
        self.logger.info('Starting bot')
        # Setting up asyncio stuff
        self.loop = asyncio.get_running_loop()
        # Preparing middlewares handlers
        self.__prepare_middlewares_handlers()
        # Starting updates loop
        self.__running = True
        self.loop.create_task(self.__updates_loop())

    async def stop(self):
        self.logger.info('Stopping Bot...')
        self.__running = False

    async def idle(self):
        try:
            while True:
                await asyncio.sleep(0.1)
        finally:
            self.logger.info('Stop Idling...')

    async def _run(self):
        async with self:
            await self.idle()

    def run(self):
        asyncio.run(self._run())

    def add_middleware(self, middleware: MiddlewareCallable):
        if self.__running:
            raise RuntimeError("Unable to add middleware in already running bot instance!")

        self.__middlewares.append(middleware)
        return middleware

    def add_update_handler(
            self,
            function: HandlerCallable,
            update_type: str = '*',
            *,
            filters: AnyFilterCallable = None
    ):
        if self.__running:
            raise RuntimeError("Unable to add middleware in already running bot instance!")

        if self.__updates_handlers.get(update_type) is None:
            raise ValueError(f'Unsupported update type: {update_type}!')

        self.__updates_handlers[update_type].add(Handler(function, filters=filters))

    def on_update(self, update_type: str = '*', *, filters: AnyFilterCallable = None):
        def decorator(function: HandlerCallable) -> HandlerCallable:
            self.add_update_handler(function, update_type, filters=filters)
            return function

        return decorator

    def add_message_handler(self, function: MessageHandler, *, filters: MessageFilterCallable):
        self.add_update_handler(function, "message", filters=filters)

    def on_message(self, *, filters: MessageFilterCallable):
        return self.on_update('message', filters=filters)

    def add_edited_message_handler(self, function: EditedMessageHandler, *, filters: EditedMessageFilterCallable):
        self.add_update_handler(function, "edited_message", filters=filters)

    def on_edited_message(self, *, filters: EditedMessageFilterCallable):
        return self.on_update('edited_message', filters=filters)

    def add_channel_post_handler(self, function: ChannelPostHandler, *, filters: ChannelPostFilterCallable):
        self.add_update_handler(function, "channel_post", filters=filters)

    def on_channel_post(self, *, filters: ChannelPostFilterCallable):
        return self.on_update('channel_post', filters=filters)

    def add_edited_channel_post_handler(
            self,
            function: EditedChannelPostHandler,
            *,
            filters: EditedChannelPostFilterCallable
    ):
        self.add_update_handler(function, "edited_channel_post", filters=filters)

    def on_edited_channel_post(self, *, filters: EditedChannelPostFilterCallable):
        return self.on_update('edited_channel_post', filters=filters)

    def add_inline_query_handler(self, function: InlineQueryHandler, *, filters: InlineQueryFilterCallable):
        self.add_update_handler(function, "inline_query", filters=filters)

    def on_inline_query(self, *, filters: InlineQueryFilterCallable):
        return self.on_update('inline_query', filters=filters)

    def add_chosen_inline_result_handler(
            self,
            function: ChosenInlineResultHandler,
            *,
            filters: ChosenInlineResultFilterCallable
    ):
        self.add_update_handler(function, "chosen_inline_result", filters=filters)

    def on_chosen_inline_result(self, *, filters: ChosenInlineResultFilterCallable):
        return self.on_update('chosen_inline_result', filters=filters)

    def add_callback_query_handler(self, function: CallbackQueryHandler, *, filters: CallbackQueryFilterCallable):
        self.add_update_handler(function, "callback_query", filters=filters)

    def on_callback_query(self, *, filters: CallbackQueryFilterCallable):
        return self.on_update('callback_query', filters=filters)

    def add_shipping_query_handler(self, function: ShippingQueryHandler, *, filters: ShippingQueryFilterCallable):
        self.add_update_handler(function, "shipping_query", filters=filters)

    def on_shipping_query(self, *, filters: ShippingQueryFilterCallable):
        return self.on_update('shipping_query', filters=filters)

    def add_pre_checkout_query_handler(
            self,
            function: PreCheckoutQueryHandler,
            *,
            filters: PreCheckoutQueryFilterCallable
    ):
        self.add_update_handler(function, "pre_checkout_query", filters=filters)

    def on_pre_checkout_query(self, *, filters: PreCheckoutQueryFilterCallable):
        return self.on_update('pre_checkout_query', filters=filters)

    def add_poll_handler(self, function: PollHandler, *, filters: PollFilterCallable):
        self.add_update_handler(function, "poll", filters=filters)

    def on_poll(self, *, filters: PollFilterCallable):
        return self.on_update('poll', filters=filters)

    def add_poll_answer_handler(self, function: PollAnswerHandler, *, filters: PollAnswerFilterCallable):
        self.add_update_handler(function, "poll_answer", filters=filters)

    def on_poll_answer(self, *, filters: PollAnswerFilterCallable):
        return self.on_update('poll_answer', filters=filters)

    def add_my_chat_member_handler(self, function: MyChatMemberHandler, *, filters: MyChatMemberFilterCallable):
        self.add_update_handler(function, "my_chat_member", filters=filters)

    def on_my_chat_member(self, *, filters: MyChatMemberFilterCallable):
        return self.on_update('my_chat_member', filters=filters)

    def add_chat_member_handler(self, function: ChatMemberHandler, *, filters: ChatMemberFilterCallable):
        self.add_update_handler(function, "chat_member", filters=filters)

    def on_chat_member(self, *, filters: ChatMemberFilterCallable):
        return self.on_update('chat_member', filters=filters)


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
    def __init__(self, function: HandlerCallable, *, filters: BaseFilter = None):
        if filters is not None and not isinstance(filters, BaseFilter):
            raise ValueError('filters should be an instance of BaseFilter!')

        self.function: HandlerCallable = function
        self.filters: Optional[AnyFilterCallable] = filters

    async def __call__(self, client: Bot, update: SomeUpdate):
        if callable(self.filters):
            filter_result = await self.filters(update)

            if not bool(filter_result):
                return

            if isinstance(filter_result, dict):
                update.EXTRA |= filter_result

        return await self.function(client, update)
