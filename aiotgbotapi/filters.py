import re
from abc import (
    ABC,
    abstractmethod,
)
from collections import (
    Callable,
    Coroutine,
)
from typing import (
    Any,
    Generic,
    NoReturn,
    Optional,
    TypeVar,
    Union,
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
    _BaseModel,
)

MessageFilterCallable = Callable[[Message], Coroutine[Any, Any, bool]]
EditedMessageFilterCallable = Callable[[Message], Coroutine[Any, Any, bool]]
ChannelPostFilterCallable = Callable[[Message], Coroutine[Any, Any, bool]]
EditedChannelPostFilterCallable = Callable[[Message], Coroutine[Any, Any, bool]]
InlineQueryFilterCallable = Callable[[InlineQuery], Coroutine[Any, Any, bool]]
ChosenInlineResultFilterCallable = Callable[[ChosenInlineResult], Coroutine[Any, Any, bool]]
CallbackQueryFilterCallable = Callable[[CallbackQuery], Coroutine[Any, Any, bool]]
ShippingQueryFilterCallable = Callable[[ShippingQuery], Coroutine[Any, Any, bool]]
PreCheckoutQueryFilterCallable = Callable[[PreCheckoutQuery], Coroutine[Any, Any, bool]]
PollFilterCallable = Callable[[Poll], Coroutine[Any, Any, bool]]
PollAnswerFilterCallable = Callable[[PollAnswer], Coroutine[Any, Any, bool]]
MyChatMemberFilterCallable = Callable[[ChatMemberUpdated], Coroutine[Any, Any, bool]]
ChatMemberFilterCallable = Callable[[ChatMemberUpdated], Coroutine[Any, Any, bool]]

AnyFilterCallable = Union[
    MessageFilterCallable,
    EditedMessageFilterCallable,
    ChannelPostFilterCallable,
    EditedChannelPostFilterCallable,
    InlineQueryFilterCallable,
    ChosenInlineResultFilterCallable,
    CallbackQueryFilterCallable,
    ShippingQueryFilterCallable,
    PreCheckoutQueryFilterCallable,
    PollFilterCallable,
    PollAnswerFilterCallable,
    MyChatMemberFilterCallable,
    ChatMemberFilterCallable,
]


class BaseFilter(ABC):
    _name = None
    data_filter: bool = False  # If True - dict, returned from filter() will be merged into up

    @abstractmethod
    async def __call__(self, update: _BaseModel) -> Optional[Union[bool, dict]]:
        return True

    def __and__(self, other: 'BaseFilter') -> 'BaseFilter':
        return MergedFilter(self, and_filter=other)

    def __or__(self, other: 'BaseFilter') -> 'BaseFilter':
        return MergedFilter(self, or_filter=other)

    def __xor__(self, other: 'BaseFilter') -> 'BaseFilter':
        return XORFilter(self, other)

    def __invert__(self) -> 'BaseFilter':
        return InvertedFilter(self)

    def __repr__(self) -> str:
        # We do this here instead of in a __init__ so filter don't have to call __init__ or super()
        if self.name is None:
            self.name = self.__class__.__name__

        return self.name

    @property
    def name(self) -> Optional[str]:
        return self._name

    @name.setter
    def name(self, name: Optional[str]) -> None:
        self._name = name


FilterUpdateType = TypeVar('FilterUpdateType', bound=_BaseModel)


class _BaseModelFilter(BaseFilter, ABC, Generic[FilterUpdateType]):
    async def __call__(self, update: FilterUpdateType) -> Optional[Union[bool, dict]]:
        super_result = await super().__call__(update)

        if not bool(super_result):
            return False

        return await self.filter(update)

    @abstractmethod
    async def filter(self, update: FilterUpdateType) -> Optional[Union[bool, dict]]:
        pass


class InvertedFilter(_BaseModelFilter):
    def __init__(self, f: BaseFilter):
        self.f = f

    async def filter(self, update: _BaseModel) -> bool:
        result = await self.f(update)
        return not bool(result)

    @property
    def name(self) -> str:
        return f"<inverted {self.f}>"

    @name.setter
    def name(self, name: str) -> NoReturn:
        raise RuntimeError('Cannot set name for InvertedFilter')


class MergedFilter(_BaseModelFilter):
    """Represents a filter consisting of two other filters.

    Args:
        base_filter: Filter 1 of the merged filter.
        and_filter: Optional filter to "and" with base_filter. Mutually exclusive with or_filter.
        or_filter: Optional filter to "or" with base_filter. Mutually exclusive with and_filter.

    """

    def __init__(
            self,
            base_filter: BaseFilter,
            and_filter: BaseFilter = None,
            or_filter: BaseFilter = None
    ):
        self.base_filter = base_filter

        if self.base_filter.data_filter:
            self.data_filter = True

        self.and_filter = and_filter

        if self.and_filter and not isinstance(self.and_filter, bool) and self.and_filter.data_filter:
            self.data_filter = True

        self.or_filter = or_filter

        if self.or_filter and not isinstance(self.and_filter, bool) and self.or_filter.data_filter:
            self.data_filter = True

    async def filter(self, update: _BaseModel) -> Union[bool, dict]:  # pylint: disable=R0911
        base_output = await self.base_filter(update)

        # We need to check if the filters are data filters and if so return the merged data.
        # If it's not a data filter or an or_filter but no matches return bool
        if self.and_filter:
            # And filter needs to short circuit if base is falsey
            if base_output:
                comp_output = await self.and_filter(update)

                if comp_output:
                    if self.data_filter:
                        merged = (base_output or {}) | (comp_output or {})

                        if merged:
                            return merged

                    return True
        elif self.or_filter:
            # Or filter needs to short circuit if base is truthey
            if base_output:
                if self.data_filter:
                    return base_output

                return True

            comp_output = await self.or_filter(update)

            if comp_output:
                if self.data_filter:
                    return comp_output

                return True

        return False

    @property
    def name(self) -> str:
        return (
            f"<{self.base_filter} {'and' if self.and_filter else 'or'} "
            f"{self.and_filter or self.or_filter}>"
        )

    @name.setter
    def name(self, name: str) -> NoReturn:
        raise RuntimeError('Cannot set name for MergedFilter')


class XORFilter(_BaseModelFilter):
    """
    Convenience filter acting as wrapper for :class:`MergedFilter` representing the an XOR gate
    for two filters.

    Args:
        base_filter: Filter 1 of the merged filter.
        xor_filter: Filter 2 of the merged filter.

    """

    def __init__(self, base_filter: BaseFilter, xor_filter: BaseFilter):
        self.base_filter = base_filter
        self.xor_filter = xor_filter
        self.merged_filter = (base_filter & ~xor_filter) | (~base_filter & xor_filter)

    async def filter(self, update: _BaseModel) -> Optional[Union[bool, dict]]:
        return await self.merged_filter(update)

    @property
    def name(self) -> str:
        return f'<{self.base_filter} xor {self.xor_filter}>'

    @name.setter
    def name(self, name: str) -> NoReturn:
        raise RuntimeError('Cannot set name for XORFilter')


# Predefined filters
class MessageFilter(_BaseModelFilter[Message]):
    name = 'Filters.message'

    async def filter(self, message: Message) -> bool:
        return True


class MessageTextFilter(MessageFilter):
    name = 'Filters.text'

    async def filter(self, message: Message) -> bool:
        return bool(message.text)


class MessageAnimationFilter(_BaseModelFilter):
    name = 'Filters.animation'

    async def filter(self, message: Message) -> bool:
        return bool(message.animation)


class MessageAudioFilter(_BaseModelFilter):
    name = 'Filters.audio'

    async def filter(self, message: Message) -> bool:
        return bool(message.audio)


class MessageDocumentFilter(_BaseModelFilter):
    name = 'Filters.document'

    async def filter(self, message: Message) -> bool:
        return bool(message.document)


class MessagePhotoFilter(_BaseModelFilter):
    name = 'Filters.photo'

    async def filter(self, message: Message) -> bool:
        return bool(message.photo)


class MessageStickerFilter(_BaseModelFilter):
    name = 'Filters.sticker'

    async def filter(self, message: Message) -> bool:
        return bool(message.sticker)


class MessageVideoFilter(_BaseModelFilter):
    name = 'Filters.video'

    async def filter(self, message: Message) -> bool:
        return bool(message.video)


class MessagevideoNoteFilter(_BaseModelFilter):
    name = 'Filters.video_note'

    async def filter(self, message: Message) -> bool:
        return bool(message.video_note)


class MessageVoiceFilter(_BaseModelFilter):
    name = 'Filters.voice'

    async def filter(self, message: Message) -> bool:
        return bool(message.voice)


class MessageCaptionFilter(_BaseModelFilter):
    name = 'Filters.caption'

    async def filter(self, message: Message) -> bool:
        return bool(message.caption)


class MessageContactFilter(_BaseModelFilter):
    name = 'Filters.contact'

    async def filter(self, message: Message) -> bool:
        return bool(message.contact)


class MessageDiceFilter(_BaseModelFilter):
    name = 'Filters.dice'

    async def filter(self, message: Message) -> bool:
        return bool(message.dice)


class MessageGameFilter(_BaseModelFilter):
    name = 'Filters.game'

    async def filter(self, message: Message) -> bool:
        return bool(message.game)


class MessagePollFilter(_BaseModelFilter):
    name = 'Filters.poll'

    async def filter(self, message: Message) -> bool:
        return bool(message.poll)


class MessageVenueFilter(_BaseModelFilter):
    name = 'Filters.venue'

    async def filter(self, message: Message) -> bool:
        return bool(message.venue)


class MessageLocationFilter(_BaseModelFilter):
    name = 'Filters.location'

    async def filter(self, message: Message) -> bool:
        return bool(message.location)


class MessagepinnedMessageFilter(_BaseModelFilter):
    name = 'Filters.pinned_message'

    async def filter(self, message: Message) -> bool:
        return bool(message.pinned_message)


class MessageInvoiceFilter(_BaseModelFilter):
    name = 'Filters.invoice'

    async def filter(self, message: Message) -> bool:
        return bool(message.invoice)


class MessagesuccessfulPaymentFilter(_BaseModelFilter):
    name = 'Filters.successful_payment'

    async def filter(self, message: Message) -> bool:
        return bool(message.successful_payment)


class CommandFilter(MessageTextFilter):
    data_filter = True
    command: str = None

    def __init__(self, command: str = '*'):
        self.command = command.lstrip('/')

    async def filter(self, message: Message) -> Union[bool, dict]:
        message_text = message.text

        if not message_text.startswith('/'):
            return False

        [bot_command, *bot_command_args] = message_text.lstrip('/').split()

        if not bool(self.command) or self.command in ["*", bot_command]:
            return {
                'command': bot_command,
                'command_args': bot_command_args
            }

        return False


class RegexFilter(MessageTextFilter):
    data_filter = True
    regex: re.Pattern

    def __init__(self, pattern: str, flags: int = 0):
        self.regex = re.compile(pattern, flags=flags)

    async def filter(self, message: Message) -> Union[bool, dict]:
        message_text = message.text or message.caption

        if not bool(message_text):
            return False

        match = self.regex.match(message_text)

        if bool(match):
            return {"regex_match": match}

        return False


class Filters:
    text = MessageTextFilter()
    animation = MessageAnimationFilter()
    audio = MessageAudioFilter()
    document = MessageDocumentFilter()
    photo = MessagePhotoFilter()
    sticker = MessageStickerFilter()
    video = MessageVideoFilter()
    video_note = MessagevideoNoteFilter()
    voice = MessageVoiceFilter()
    caption = MessageCaptionFilter()
    contact = MessageContactFilter()
    dice = MessageDiceFilter()
    game = MessageGameFilter()
    poll = MessagePollFilter()
    venue = MessageVenueFilter()
    location = MessageLocationFilter()
    pinned_message = MessagepinnedMessageFilter()
    invoice = MessageInvoiceFilter()
    successful_payment = MessagesuccessfulPaymentFilter()

    # "Callable" filters
    command = CommandFilter
    regex = RegexFilter
