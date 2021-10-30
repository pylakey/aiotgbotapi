from __future__ import annotations

import typing
from decimal import Decimal

import pydantic
import ujson
from pydantic.generics import GenericModel

from .errors import TelegramException


class _BaseModel(pydantic.BaseModel):
    EXTRA: dict = {}

    class Config:
        allow_population_by_field_name = True
        json_dumps = ujson.dumps
        json_loads = ujson.loads


SuccessModelType = typing.TypeVar('SuccessModelType')


class Response(GenericModel, typing.Generic[SuccessModelType]):
    ok: bool = False
    result: typing.Optional[SuccessModelType] = None


class Error(_BaseModel):
    ok: bool = False
    error_code: int
    description: str
    parameters: typing.Optional[ResponseParameters] = None

    @property
    def text(self):
        text = self.description

        if bool(self.parameters):
            if bool(self.parameters.retry_after):
                text += f" Retry after: {self.parameters.retry_after}."
            if bool(self.parameters.migrate_to_chat_id):
                text += f" Migrate to Chat ID: {self.parameters.migrate_to_chat_id}."

        return text

    def raise_exception(self):
        raise TelegramException(self.error_code, self.text)


class ResponseParameters(_BaseModel):
    """
    Contains information about why a request was unsuccessful.
    """

    migrate_to_chat_id: typing.Optional[int]
    """
    *Optional*. The group has been migrated to a supergroup with the specified identifier. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier.
    """
    retry_after: typing.Optional[int]
    """
    *Optional*. In case of exceeding flood control, the number of seconds left to wait before the request can be repeated
    """


class Update(_BaseModel):
    """
    This [object](https://core.telegram.org/bots/api/#available-types) represents an incoming update.  
At most **one** of the optional parameters can be present in any given update.
    """

    update_id: int
    """
    The update&#39;s unique identifier. Update identifiers start from a certain positive number and increase sequentially. This ID becomes especially handy if you&#39;re using [Webhooks](https://core.telegram.org/bots/api/#setwebhook), since it allows you to ignore repeated updates or to restore the correct update sequence, should they get out of order. If there are no new updates for at least a week, then identifier of the next update will be chosen randomly instead of sequentially.
    """
    message: typing.Optional[Message]
    edited_message: typing.Optional[Message]
    channel_post: typing.Optional[Message]
    edited_channel_post: typing.Optional[Message]
    inline_query: typing.Optional[InlineQuery]
    chosen_inline_result: typing.Optional[ChosenInlineResult]
    callback_query: typing.Optional[CallbackQuery]
    shipping_query: typing.Optional[ShippingQuery]
    pre_checkout_query: typing.Optional[PreCheckoutQuery]
    poll: typing.Optional[Poll]
    poll_answer: typing.Optional[PollAnswer]
    my_chat_member: typing.Optional[ChatMemberUpdated]
    chat_member: typing.Optional[ChatMemberUpdated]


class Message(_BaseModel):
    """
    This object represents a message.
    """

    message_id: int
    """
    Unique message identifier inside this chat
    """
    from_: typing.Optional[User] = pydantic.Field(None, alias='from')
    sender_chat: typing.Optional[Chat]
    date: int
    """
    Date the message was sent in Unix time
    """
    chat: Chat
    forward_from: typing.Optional[User]
    forward_from_chat: typing.Optional[Chat]
    forward_from_message_id: typing.Optional[int]
    """
    *Optional*. For messages forwarded from channels, identifier of the original message in the channel
    """
    forward_signature: typing.Optional[str]
    """
    *Optional*. For messages forwarded from channels, signature of the post author if present
    """
    forward_sender_name: typing.Optional[str]
    """
    *Optional*. Sender&#39;s name for messages forwarded from users who disallow adding a link to their account in forwarded messages
    """
    forward_date: typing.Optional[int]
    """
    *Optional*. For forwarded messages, date the original message was sent in Unix time
    """
    reply_to_message: typing.Optional[Message]
    via_bot: typing.Optional[User]
    edit_date: typing.Optional[int]
    """
    *Optional*. Date the message was last edited in Unix time
    """
    media_group_id: typing.Optional[str]
    """
    *Optional*. The unique identifier of a media message group this message belongs to
    """
    author_signature: typing.Optional[str]
    """
    *Optional*. Signature of the post author for messages in channels, or the custom title of an anonymous group administrator
    """
    text: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=4096,
    )
    """
    *Optional*. For text messages, the actual UTF-8 text of the message, 0-4096 characters
    """
    entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. For text messages, special entities like usernames, URLs, bot commands, etc. that appear in the text
    """
    animation: typing.Optional[Animation]
    audio: typing.Optional[Audio]
    document: typing.Optional[Document]
    photo: typing.Optional[list[PhotoSize]]
    """
    *Optional*. Message is a photo, available sizes of the photo
    """
    sticker: typing.Optional[Sticker]
    video: typing.Optional[Video]
    video_note: typing.Optional[VideoNote]
    voice: typing.Optional[Voice]
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption for the animation, audio, document, photo, video or voice, 0-1024 characters
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. For messages with a caption, special entities like usernames, URLs, bot commands, etc. that appear in the caption
    """
    contact: typing.Optional[Contact]
    dice: typing.Optional[Dice]
    game: typing.Optional[Game]
    poll: typing.Optional[Poll]
    venue: typing.Optional[Venue]
    location: typing.Optional[Location]
    new_chat_members: typing.Optional[list[User]]
    """
    *Optional*. New members that were added to the group or supergroup and information about them (the bot itself may be one of these members)
    """
    left_chat_member: typing.Optional[User]
    new_chat_title: typing.Optional[str]
    """
    *Optional*. A chat title was changed to this value
    """
    new_chat_photo: typing.Optional[list[PhotoSize]]
    """
    *Optional*. A chat photo was change to this value
    """
    delete_chat_photo: typing.Optional[bool]
    """
    *Optional*. Service message: the chat photo was deleted
    """
    group_chat_created: typing.Optional[bool]
    """
    *Optional*. Service message: the group has been created
    """
    supergroup_chat_created: typing.Optional[bool]
    """
    *Optional*. Service message: the supergroup has been created. This field can&#39;t be received in a message coming through updates, because bot can&#39;t be a member of a supergroup when it is created. It can only be found in reply_to_message if someone replies to a very first message in a directly created supergroup.
    """
    channel_chat_created: typing.Optional[bool]
    """
    *Optional*. Service message: the channel has been created. This field can&#39;t be received in a message coming through updates, because bot can&#39;t be a member of a channel when it is created. It can only be found in reply_to_message if someone replies to a very first message in a channel.
    """
    message_auto_delete_timer_changed: typing.Optional[MessageAutoDeleteTimerChanged]
    migrate_to_chat_id: typing.Optional[int]
    """
    *Optional*. The group has been migrated to a supergroup with the specified identifier. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier.
    """
    migrate_from_chat_id: typing.Optional[int]
    """
    *Optional*. The supergroup has been migrated from a group with the specified identifier. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier.
    """
    pinned_message: typing.Optional[Message]
    invoice: typing.Optional[Invoice]
    successful_payment: typing.Optional[SuccessfulPayment]
    connected_website: typing.Optional[str]
    """
    *Optional*. The domain name of the website on which the user has logged in. [More about Telegram Login »](/widgets/login)
    """
    passport_data: typing.Optional[PassportData]
    proximity_alert_triggered: typing.Optional[ProximityAlertTriggered]
    voice_chat_scheduled: typing.Optional[VoiceChatScheduled]
    voice_chat_started: typing.Optional[VoiceChatStarted]
    voice_chat_ended: typing.Optional[VoiceChatEnded]
    voice_chat_participants_invited: typing.Optional[VoiceChatParticipantsInvited]
    reply_markup: typing.Optional[InlineKeyboardMarkup]


class User(_BaseModel):
    """
    This object represents a Telegram user or bot.
    """

    id: int
    """
    Unique identifier for this user or bot. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier.
    """
    is_bot: bool
    """
    True, if this user is a bot
    """
    first_name: str
    """
    User&#39;s or bot&#39;s first name
    """
    last_name: typing.Optional[str]
    """
    *Optional*. User&#39;s or bot&#39;s last name
    """
    username: typing.Optional[str]
    """
    *Optional*. User&#39;s or bot&#39;s username
    """
    language_code: typing.Optional[str]
    """
    *Optional*. [IETF language tag](https://en.wikipedia.org/wiki/IETF_language_tag) of the user&#39;s language
    """
    can_join_groups: typing.Optional[bool]
    """
    *Optional*. True, if the bot can be invited to groups. Returned only in [getMe](https://core.telegram.org/bots/api/#getme).
    """
    can_read_all_group_messages: typing.Optional[bool]
    """
    *Optional*. True, if [privacy mode](https://core.telegram.org/bots#privacy-mode) is disabled for the bot. Returned only in [getMe](https://core.telegram.org/bots/api/#getme).
    """
    supports_inline_queries: typing.Optional[bool]
    """
    *Optional*. True, if the bot supports inline queries. Returned only in [getMe](https://core.telegram.org/bots/api/#getme).
    """

    @property
    def full_name(self):
        if bool(self.last_name):
            return f"{self.first_name} {self.last_name}"

        return self.first_name

    @property
    def mention(self):
        return f"<a href='tg://user?id={self.id}'>{self.full_name}</a>"


class Chat(_BaseModel):
    """
    This object represents a chat.
    """

    id: int
    """
    Unique identifier for this chat. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision float type are safe for storing this identifier.
    """
    type: str
    """
    Type of chat, can be either “private”, “group”, “supergroup” or “channel”
    """
    title: typing.Optional[str]
    """
    *Optional*. Title, for supergroups, channels and group chats
    """
    username: typing.Optional[str]
    """
    *Optional*. Username, for private chats, supergroups and channels if available
    """
    first_name: typing.Optional[str]
    """
    *Optional*. First name of the other party in a private chat
    """
    last_name: typing.Optional[str]
    """
    *Optional*. Last name of the other party in a private chat
    """
    photo: typing.Optional[ChatPhoto]
    bio: typing.Optional[str]
    """
    *Optional*. Bio of the other party in a private chat. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    description: typing.Optional[str]
    """
    *Optional*. Description, for groups, supergroups and channel chats. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    invite_link: typing.Optional[str]
    """
    *Optional*. Primary invite link, for groups, supergroups and channel chats. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    pinned_message: typing.Optional[Message]
    permissions: typing.Optional[ChatPermissions]
    slow_mode_delay: typing.Optional[int]
    """
    *Optional*. For supergroups, the minimum allowed delay between consecutive messages sent by each unpriviledged user. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    message_auto_delete_time: typing.Optional[int]
    """
    *Optional*. The time after which all messages sent to the chat will be automatically deleted; in seconds. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    sticker_set_name: typing.Optional[str]
    """
    *Optional*. For supergroups, name of group sticker set. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    can_set_sticker_set: typing.Optional[bool]
    """
    *Optional*. True, if the bot can change the group sticker set. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    linked_chat_id: typing.Optional[int]
    """
    *Optional*. Unique identifier for the linked chat, i.e. the discussion group identifier for a channel and vice versa; for supergroups and channel chats. This identifier may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier. Returned only in [getChat](https://core.telegram.org/bots/api/#getchat).
    """
    location: typing.Optional[ChatLocation]


class ChatPhoto(_BaseModel):
    """
    This object represents a chat photo.
    """

    small_file_id: str
    """
    File identifier of small (160x160) chat photo. This file_id can be used only for photo download and only for as long as the photo is not changed.
    """
    small_file_unique_id: str
    """
    Unique file identifier of small (160x160) chat photo, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    big_file_id: str
    """
    File identifier of big (640x640) chat photo. This file_id can be used only for photo download and only for as long as the photo is not changed.
    """
    big_file_unique_id: str
    """
    Unique file identifier of big (640x640) chat photo, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """


class ChatPermissions(_BaseModel):
    """
    Describes actions that a non-administrator user is allowed to take in a chat.
    """

    can_send_messages: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to send text messages, contacts, locations and venues
    """
    can_send_media_messages: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes, implies can_send_messages
    """
    can_send_polls: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to send polls, implies can_send_messages
    """
    can_send_other_messages: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to send animations, games, stickers and use inline bots, implies can_send_media_messages
    """
    can_add_web_page_previews: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to add web page previews to their messages, implies can_send_media_messages
    """
    can_change_info: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to change the chat title, photo and other settings. Ignored in public supergroups
    """
    can_invite_users: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to invite new users to the chat
    """
    can_pin_messages: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to pin messages. Ignored in public supergroups
    """


class ChatLocation(_BaseModel):
    """
    Represents a location to which a chat is connected.
    """

    location: Location
    address: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=64,
    )
    """
    Location address; 1-64 characters, as defined by the chat owner
    """


class Location(_BaseModel):
    """
    This object represents a point on the map.
    """

    longitude: Decimal
    """
    Longitude as defined by sender
    """
    latitude: Decimal
    """
    Latitude as defined by sender
    """
    horizontal_accuracy: typing.Optional[Decimal]
    """
    *Optional*. The radius of uncertainty for the location, measured in meters; 0-1500
    """
    live_period: typing.Optional[int]
    """
    *Optional*. Time relative to the message sending date, during which the location can be updated, in seconds. For active live locations only.
    """
    heading: typing.Optional[int]
    """
    *Optional*. The direction in which user is moving, in degrees; 1-360. For active live locations only.
    """
    proximity_alert_radius: typing.Optional[int]
    """
    *Optional*. Maximum distance for proximity alerts about approaching another chat member, in meters. For sent live locations only.
    """


class MessageEntity(_BaseModel):
    """
    This object represents one special entity in a text message. For example, hashtags, usernames, URLs, etc.
    """

    type: str
    """
    Type of the entity. Can be “mention” (`@username`), “hashtag” (`#hashtag`), “cashtag” (`$USD`), “bot_command” (`/start@jobs_bot`), “url” (`https://telegram.org`), “email” (`do-not-reply@telegram.org`), “phone_number” (`+1-212-555-0123`), “bold” (**bold text**), “italic” (*italic text*), “underline” (underlined text), “strikethrough” (strikethrough text), “code” (monowidth string), “pre” (monowidth block), “text_link” (for clickable text URLs), “text_mention” (for users [without usernames](https://telegram.org/blog/edit#new-mentions))
    """
    offset: int
    """
    Offset in UTF-16 code units to the start of the entity
    """
    length: int
    """
    Length of the entity in UTF-16 code units
    """
    url: typing.Optional[str]
    """
    *Optional*. For “text_link” only, url that will be opened after user taps on the text
    """
    user: typing.Optional[User]
    language: typing.Optional[str]
    """
    *Optional*. For “pre” only, the programming language of the entity text
    """


class Animation(_BaseModel):
    """
    This object represents an animation file (GIF or H.264/MPEG-4 AVC video without sound).
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    width: int
    """
    Video width as defined by sender
    """
    height: int
    """
    Video height as defined by sender
    """
    duration: int
    """
    Duration of the video in seconds as defined by sender
    """
    thumb: typing.Optional[PhotoSize]
    file_name: typing.Optional[str]
    """
    *Optional*. Original animation filename as defined by sender
    """
    mime_type: typing.Optional[str]
    """
    *Optional*. MIME type of the file as defined by sender
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class PhotoSize(_BaseModel):
    """
    This object represents one size of a photo or a [file](https://core.telegram.org/bots/api/#document) / [sticker](https://core.telegram.org/bots/api/#sticker) thumbnail.
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    width: int
    """
    Photo width
    """
    height: int
    """
    Photo height
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class Audio(_BaseModel):
    """
    This object represents an audio file to be treated as music by the Telegram clients.
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    duration: int
    """
    Duration of the audio in seconds as defined by sender
    """
    performer: typing.Optional[str]
    """
    *Optional*. Performer of the audio as defined by sender or by audio tags
    """
    title: typing.Optional[str]
    """
    *Optional*. Title of the audio as defined by sender or by audio tags
    """
    file_name: typing.Optional[str]
    """
    *Optional*. Original filename as defined by sender
    """
    mime_type: typing.Optional[str]
    """
    *Optional*. MIME type of the file as defined by sender
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """
    thumb: typing.Optional[PhotoSize]


class Document(_BaseModel):
    """
    This object represents a general file (as opposed to [photos](https://core.telegram.org/bots/api/#photosize), [voice messages](https://core.telegram.org/bots/api/#voice) and [audio files](https://core.telegram.org/bots/api/#audio)).
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    thumb: typing.Optional[PhotoSize]
    file_name: typing.Optional[str]
    """
    *Optional*. Original filename as defined by sender
    """
    mime_type: typing.Optional[str]
    """
    *Optional*. MIME type of the file as defined by sender
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class Sticker(_BaseModel):
    """
    This object represents a sticker.
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    width: int
    """
    Sticker width
    """
    height: int
    """
    Sticker height
    """
    is_animated: bool
    """
    *True*, if the sticker is [animated](https://telegram.org/blog/animated-stickers)
    """
    thumb: typing.Optional[PhotoSize]
    emoji: typing.Optional[str]
    """
    *Optional*. Emoji associated with the sticker
    """
    set_name: typing.Optional[str]
    """
    *Optional*. Name of the sticker set to which the sticker belongs
    """
    mask_position: typing.Optional[MaskPosition]
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class MaskPosition(_BaseModel):
    """
    This object describes the position on faces where a mask should be placed by default.
    """

    point: str
    """
    The part of the face relative to which the mask should be placed. One of “forehead”, “eyes”, “mouth”, or “chin”.
    """
    x_shift: Decimal
    """
    Shift by X-axis measured in widths of the mask scaled to the face size, from left to right. For example, choosing -1.0 will place mask just to the left of the default mask position.
    """
    y_shift: Decimal
    """
    Shift by Y-axis measured in heights of the mask scaled to the face size, from top to bottom. For example, 1.0 will place the mask just below the default mask position.
    """
    scale: Decimal
    """
    Mask scaling coefficient. For example, 2.0 means double size.
    """


class Video(_BaseModel):
    """
    This object represents a video file.
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    width: int
    """
    Video width as defined by sender
    """
    height: int
    """
    Video height as defined by sender
    """
    duration: int
    """
    Duration of the video in seconds as defined by sender
    """
    thumb: typing.Optional[PhotoSize]
    file_name: typing.Optional[str]
    """
    *Optional*. Original filename as defined by sender
    """
    mime_type: typing.Optional[str]
    """
    *Optional*. Mime type of a file as defined by sender
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class VideoNote(_BaseModel):
    """
    This object represents a [video message](https://telegram.org/blog/video-messages-and-telescope) (available in Telegram apps as of [v.4.0](https://telegram.org/blog/video-messages-and-telescope)).
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    length: int
    """
    Video width and height (diameter of the video message) as defined by sender
    """
    duration: int
    """
    Duration of the video in seconds as defined by sender
    """
    thumb: typing.Optional[PhotoSize]
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class Voice(_BaseModel):
    """
    This object represents a voice note.
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    duration: int
    """
    Duration of the audio in seconds as defined by sender
    """
    mime_type: typing.Optional[str]
    """
    *Optional*. MIME type of the file as defined by sender
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes
    """


class Contact(_BaseModel):
    """
    This object represents a phone contact.
    """

    phone_number: str
    """
    Contact&#39;s phone number
    """
    first_name: str
    """
    Contact&#39;s first name
    """
    last_name: typing.Optional[str]
    """
    *Optional*. Contact&#39;s last name
    """
    user_id: typing.Optional[int]
    """
    *Optional*. Contact&#39;s user identifier in Telegram. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier.
    """
    vcard: typing.Optional[str]
    """
    *Optional*. Additional data about the contact in the form of a [vCard](https://en.wikipedia.org/wiki/VCard)
    """


class Dice(_BaseModel):
    """
    This object represents an animated emoji that displays a random value.
    """

    emoji: str
    """
    Emoji on which the dice throw animation is based
    """
    value: int
    """
    Value of the dice, 1-6 for “🎲”, “🎯” and “🎳” base emoji, 1-5 for “🏀” and “⚽” base emoji, 1-64 for “🎰” base emoji
    """


class Game(_BaseModel):
    """
    This object represents a game. Use BotFather to create and edit games, their short names will act as unique identifiers.
    """

    title: str
    """
    Title of the game
    """
    description: str
    """
    Description of the game
    """
    photo: list[PhotoSize]
    """
    Photo that will be displayed in the game message in chats.
    """
    text: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=4096,
    )
    """
    *Optional*. Brief description of the game or high scores included in the game message. Can be automatically edited to include current high scores for the game when the bot calls [setGameScore](https://core.telegram.org/bots/api/#setgamescore), or manually edited using [editMessageText](https://core.telegram.org/bots/api/#editmessagetext). 0-4096 characters.
    """
    text_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. Special entities that appear in *text*, such as usernames, URLs, bot commands, etc.
    """
    animation: typing.Optional[Animation]


class Poll(_BaseModel):
    """
    This object contains information about a poll.
    """

    id: str
    """
    Unique poll identifier
    """
    question: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=300,
    )
    """
    Poll question, 1-300 characters
    """
    options: list[PollOption]
    """
    List of poll options
    """
    total_voter_count: int
    """
    Total number of users that voted in the poll
    """
    is_closed: bool
    """
    True, if the poll is closed
    """
    is_anonymous: bool
    """
    True, if the poll is anonymous
    """
    type: str
    """
    Poll type, currently can be “regular” or “quiz”
    """
    allows_multiple_answers: bool
    """
    True, if the poll allows multiple answers
    """
    correct_option_id: typing.Optional[int]
    """
    *Optional*. 0-based identifier of the correct answer option. Available only for polls in the quiz mode, which are closed, or was sent (not forwarded) by the bot or to the private chat with the bot.
    """
    explanation: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=200,
    )
    """
    *Optional*. Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters
    """
    explanation_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. Special entities like usernames, URLs, bot commands, etc. that appear in the *explanation*
    """
    open_period: typing.Optional[int]
    """
    *Optional*. Amount of time in seconds the poll will be active after creation
    """
    close_date: typing.Optional[int]
    """
    *Optional*. Point in time (Unix timestamp) when the poll will be automatically closed
    """


class PollOption(_BaseModel):
    """
    This object contains information about one answer option in a poll.
    """

    text: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=100,
    )
    """
    Option text, 1-100 characters
    """
    voter_count: int
    """
    Number of users that voted for this option
    """


class Venue(_BaseModel):
    """
    This object represents a venue.
    """

    location: Location
    title: str
    """
    Name of the venue
    """
    address: str
    """
    Address of the venue
    """
    foursquare_id: typing.Optional[str]
    """
    *Optional*. Foursquare identifier of the venue
    """
    foursquare_type: typing.Optional[str]
    """
    *Optional*. Foursquare type of the venue. (For example, “arts_entertainment/default”, “arts_entertainment/aquarium” or “food/icecream”.)
    """
    google_place_id: typing.Optional[str]
    """
    *Optional*. Google Places identifier of the venue
    """
    google_place_type: typing.Optional[str]
    """
    *Optional*. Google Places type of the venue. (See [supported types](https://developers.google.com/places/web-service/supported_types).)
    """


class MessageAutoDeleteTimerChanged(_BaseModel):
    """
    This object represents a service message about a change in auto-delete timer settings.
    """

    message_auto_delete_time: int
    """
    New auto-delete time for messages in the chat
    """


class Invoice(_BaseModel):
    """
    This object contains basic information about an invoice.
    """

    title: str
    """
    Product name
    """
    description: str
    """
    Product description
    """
    start_parameter: str
    """
    Unique bot deep-linking parameter that can be used to generate this invoice
    """
    currency: str
    """
    Three-letter ISO 4217 [currency](/bots/payments#supported-currencies) code
    """
    total_amount: int
    """
    Total price in the *smallest units* of the currency (integer, **not** float/double). For example, for a price of `US$ 1.45` pass `amount = 145`. See the *exp* parameter in [currencies.json](https://core.telegram.org/bots/payments/currencies.json), it shows the number of digits past the decimal point for each currency (2 for the majority of currencies).
    """


class SuccessfulPayment(_BaseModel):
    """
    This object contains basic information about a successful payment.
    """

    currency: str
    """
    Three-letter ISO 4217 [currency](/bots/payments#supported-currencies) code
    """
    total_amount: int
    """
    Total price in the *smallest units* of the currency (integer, **not** float/double). For example, for a price of `US$ 1.45` pass `amount = 145`. See the *exp* parameter in [currencies.json](https://core.telegram.org/bots/payments/currencies.json), it shows the number of digits past the decimal point for each currency (2 for the majority of currencies).
    """
    invoice_payload: str
    """
    Bot specified invoice payload
    """
    shipping_option_id: typing.Optional[str]
    """
    *Optional*. Identifier of the shipping option chosen by the user
    """
    order_info: typing.Optional[OrderInfo]
    telegram_payment_charge_id: str
    """
    Telegram payment identifier
    """
    provider_payment_charge_id: str
    """
    Provider payment identifier
    """


class OrderInfo(_BaseModel):
    """
    This object represents information about an order.
    """

    name: typing.Optional[str]
    """
    *Optional*. User name
    """
    phone_number: typing.Optional[str]
    """
    *Optional*. User&#39;s phone number
    """
    email: typing.Optional[str]
    """
    *Optional*. User email
    """
    shipping_address: typing.Optional[ShippingAddress]


class ShippingAddress(_BaseModel):
    """
    This object represents a shipping address.
    """

    country_code: str
    """
    ISO 3166-1 alpha-2 country code
    """
    state: str
    """
    State, if applicable
    """
    city: str
    """
    City
    """
    street_line1: str
    """
    First line for the address
    """
    street_line2: str
    """
    Second line for the address
    """
    post_code: str
    """
    Address post code
    """


class PassportData(_BaseModel):
    """
    Contains information about Telegram Passport data shared with the bot by the user.
    """

    data: list[EncryptedPassportElement]
    """
    Array with information about documents and other Telegram Passport elements that was shared with the bot
    """
    credentials: EncryptedCredentials


class EncryptedPassportElement(_BaseModel):
    """
    Contains information about documents or other Telegram Passport elements shared with the bot by the user.
    """

    type: str
    """
    Element type. One of “personal_details”, “passport”, “driver_license”, “identity_card”, “internal_passport”, “address”, “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration”, “temporary_registration”, “phone_number”, “email”.
    """
    data: typing.Optional[str]
    """
    *Optional*. Base64-encoded encrypted Telegram Passport element data provided by the user, available for “personal_details”, “passport”, “driver_license”, “identity_card”, “internal_passport” and “address” types. Can be decrypted and verified using the accompanying [EncryptedCredentials](https://core.telegram.org/bots/api/#encryptedcredentials).
    """
    phone_number: typing.Optional[str]
    """
    *Optional*. User&#39;s verified phone number, available only for “phone_number” type
    """
    email: typing.Optional[str]
    """
    *Optional*. User&#39;s verified email address, available only for “email” type
    """
    files: typing.Optional[list[PassportFile]]
    """
    *Optional*. Array of encrypted files with documents provided by the user, available for “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration” and “temporary_registration” types. Files can be decrypted and verified using the accompanying [EncryptedCredentials](https://core.telegram.org/bots/api/#encryptedcredentials).
    """
    front_side: typing.Optional[PassportFile]
    reverse_side: typing.Optional[PassportFile]
    selfie: typing.Optional[PassportFile]
    translation: typing.Optional[list[PassportFile]]
    """
    *Optional*. Array of encrypted files with translated versions of documents provided by the user. Available if requested for “passport”, “driver_license”, “identity_card”, “internal_passport”, “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration” and “temporary_registration” types. Files can be decrypted and verified using the accompanying [EncryptedCredentials](https://core.telegram.org/bots/api/#encryptedcredentials).
    """
    hash: str
    """
    Base64-encoded element hash for using in [PassportElementErrorUnspecified](https://core.telegram.org/bots/api/#passportelementerrorunspecified)
    """


class PassportFile(_BaseModel):
    """
    This object represents a file uploaded to Telegram Passport. Currently all Telegram Passport files are in JPEG format when decrypted and don&#39;t exceed 10MB.
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    file_size: int
    """
    File size in bytes
    """
    file_date: int
    """
    Unix time when the file was uploaded
    """


class EncryptedCredentials(_BaseModel):
    """
    Contains data required for decrypting and authenticating [EncryptedPassportElement](https://core.telegram.org/bots/api/#encryptedpassportelement). See the [Telegram Passport Documentation](https://core.telegram.org/passport#receiving-information) for a complete description of the data decryption and authentication processes.
    """

    data: str
    """
    Base64-encoded encrypted JSON-serialized data with unique user&#39;s payload, data hashes and secrets required for [EncryptedPassportElement](https://core.telegram.org/bots/api/#encryptedpassportelement) decryption and authentication
    """
    hash: str
    """
    Base64-encoded data hash for data authentication
    """
    secret: str
    """
    Base64-encoded secret, encrypted with the bot&#39;s public RSA key, required for data decryption
    """


class ProximityAlertTriggered(_BaseModel):
    """
    This object represents the content of a service message, sent whenever a user in the chat triggers a proximity alert set by another user.
    """

    traveler: User
    watcher: User
    distance: int
    """
    The distance between the users
    """


class VoiceChatScheduled(_BaseModel):
    """
    This object represents a service message about a voice chat scheduled in the chat.
    """

    start_date: int
    """
    Point in time (Unix timestamp) when the voice chat is supposed to be started by a chat administrator
    """


class VoiceChatStarted(_BaseModel):
    """
    This object represents a service message about a voice chat started in the chat. Currently holds no information.
    """

    pass


class VoiceChatEnded(_BaseModel):
    """
    This object represents a service message about a voice chat ended in the chat.
    """

    duration: int
    """
    Voice chat duration in seconds
    """


class VoiceChatParticipantsInvited(_BaseModel):
    """
    This object represents a service message about new members invited to a voice chat.
    """

    users: typing.Optional[list[User]]
    """
    *Optional*. New members that were invited to the voice chat
    """


class InlineKeyboardMarkup(_BaseModel):
    """
    This object represents an [inline keyboard](https://core.telegram.org/bots#inline-keyboards-and-on-the-fly-updating) that appears right next to the message it belongs to.
    """

    inline_keyboard: list[list[InlineKeyboardButton]]
    """
    Array of button rows, each represented by an Array of [InlineKeyboardButton](https://core.telegram.org/bots/api/#inlinekeyboardbutton) objects
    """


class InlineKeyboardButton(_BaseModel):
    """
    This object represents one button of an inline keyboard. You **must** use exactly one of the optional fields.
    """

    text: str
    """
    Label text on the button
    """
    url: typing.Optional[str]
    """
    *Optional*. HTTP or tg:// url to be opened when button is pressed
    """
    login_url: typing.Optional[LoginUrl]
    callback_data: typing.Optional[str]
    """
    *Optional*. Data to be sent in a [callback query](https://core.telegram.org/bots/api/#callbackquery) to the bot when button is pressed, 1-64 bytes
    """
    switch_inline_query: typing.Optional[str]
    """
    *Optional*. If set, pressing the button will prompt the user to select one of their chats, open that chat and insert the bot&#39;s username and the specified inline query in the input field. Can be empty, in which case just the bot&#39;s username will be inserted.  

**Note:** This offers an easy way for users to start using your bot in [inline mode](/bots/inline) when they are currently in a private chat with it. Especially useful when combined with [*switch_pm…*](https://core.telegram.org/bots/api/#answerinlinequery) actions – in this case the user will be automatically returned to the chat they switched from, skipping the chat selection screen.
    """
    switch_inline_query_current_chat: typing.Optional[str]
    """
    *Optional*. If set, pressing the button will insert the bot&#39;s username and the specified inline query in the current chat&#39;s input field. Can be empty, in which case only the bot&#39;s username will be inserted.  

This offers a quick way for the user to open your bot in inline mode in the same chat – good for selecting something from multiple options.
    """
    callback_game: typing.Optional[CallbackGame]
    pay: typing.Optional[bool]
    """
    *Optional*. Specify True, to send a [Pay button](https://core.telegram.org/bots/api/#payments).  

**NOTE:** This type of button **must** always be the first button in the first row.
    """


class LoginUrl(_BaseModel):
    """
    This object represents a parameter of the inline keyboard button used to automatically authorize a user. Serves as a great replacement for the [Telegram Login Widget](https://core.telegram.org/widgets/login) when the user is coming from Telegram. All the user needs to do is tap/click a button and confirm that they want to log in:

Telegram apps support these buttons as of [version 5.7](https://telegram.org/blog/privacy-discussions-web-bots#meet-seamless-web-bots).

Sample bot: [@discussbot](https://t.me/discussbot)
    """

    url: str
    """
    An HTTP URL to be opened with user authorization data added to the query string when the button is pressed. If the user refuses to provide authorization data, the original URL without information about the user will be opened. The data added is the same as described in [Receiving authorization data](https://core.telegram.org/widgets/login#receiving-authorization-data).  

**NOTE:** You **must** always check the hash of the received data to verify the authentication and the integrity of the data as described in [Checking authorization](https://core.telegram.org/widgets/login#checking-authorization).
    """
    forward_text: typing.Optional[str]
    """
    *Optional*. New text of the button in forwarded messages.
    """
    bot_username: typing.Optional[str]
    """
    *Optional*. Username of a bot, which will be used for user authorization. See [Setting up a bot](https://core.telegram.org/widgets/login#setting-up-a-bot) for more details. If not specified, the current bot&#39;s username will be assumed. The *url*&#39;s domain must be the same as the domain linked with the bot. See [Linking your domain to the bot](https://core.telegram.org/widgets/login#linking-your-domain-to-the-bot) for more details.
    """
    request_write_access: typing.Optional[bool]
    """
    *Optional*. Pass True to request the permission for your bot to send messages to the user.
    """


class CallbackGame(_BaseModel):
    """
    A placeholder, currently holds no information. Use [BotFather](https://t.me/botfather) to set up your game.
    """

    pass


class InlineQuery(_BaseModel):
    """
    This object represents an incoming inline query. When the user sends an empty query, your bot could return some default or trending results.
    """

    id: str
    """
    Unique identifier for this query
    """
    from_: User = pydantic.Field(None, alias='from')
    query: str
    """
    Text of the query (up to 256 characters)
    """
    offset: str
    """
    Offset of the results to be returned, can be controlled by the bot
    """
    chat_type: typing.Optional[str]
    """
    *Optional*. Type of the chat, from which the inline query was sent. Can be either “sender” for a private chat with the inline query sender, “private”, “group”, “supergroup”, or “channel”. The chat type should be always known for requests sent from official clients and most third-party clients, unless the request was sent from a secret chat
    """
    location: typing.Optional[Location]


class ChosenInlineResult(_BaseModel):
    """
    Represents a [result](https://core.telegram.org/bots/api/#inlinequeryresult) of an inline query that was chosen by the user and sent to their chat partner.
    """

    result_id: str
    """
    The unique identifier for the result that was chosen
    """
    from_: User = pydantic.Field(None, alias='from')
    location: typing.Optional[Location]
    inline_message_id: typing.Optional[str]
    """
    *Optional*. Identifier of the sent inline message. Available only if there is an [inline keyboard](https://core.telegram.org/bots/api/#inlinekeyboardmarkup) attached to the message. Will be also received in [callback queries](https://core.telegram.org/bots/api/#callbackquery) and can be used to [edit](https://core.telegram.org/bots/api/#updating-messages) the message.
    """
    query: str
    """
    The query that was used to obtain the result
    """


class CallbackQuery(_BaseModel):
    """
    This object represents an incoming callback query from a callback button in an [inline keyboard](/bots#inline-keyboards-and-on-the-fly-updating). If the button that originated the query was attached to a message sent by the bot, the field *message* will be present. If the button was attached to a message sent via the bot (in [inline mode](https://core.telegram.org/bots/api/#inline-mode)), the field *inline_message_id* will be present. Exactly one of the fields *data* or *game_short_name* will be present.
    """

    id: str
    """
    Unique identifier for this query
    """
    from_: User = pydantic.Field(None, alias='from')
    message: typing.Optional[Message]
    inline_message_id: typing.Optional[str]
    """
    *Optional*. Identifier of the message sent via the bot in inline mode, that originated the query.
    """
    chat_instance: str
    """
    Global identifier, uniquely corresponding to the chat to which the message with the callback button was sent. Useful for high scores in [games](https://core.telegram.org/bots/api/#games).
    """
    data: typing.Optional[str]
    """
    *Optional*. Data associated with the callback button. Be aware that a bad client can send arbitrary data in this field.
    """
    game_short_name: typing.Optional[str]
    """
    *Optional*. Short name of a [Game](https://core.telegram.org/bots/api/#games) to be returned, serves as the unique identifier for the game
    """


class ShippingQuery(_BaseModel):
    """
    This object contains information about an incoming shipping query.
    """

    id: str
    """
    Unique query identifier
    """
    from_: User = pydantic.Field(None, alias='from')
    invoice_payload: str
    """
    Bot specified invoice payload
    """
    shipping_address: ShippingAddress


class PreCheckoutQuery(_BaseModel):
    """
    This object contains information about an incoming pre-checkout query.
    """

    id: str
    """
    Unique query identifier
    """
    from_: User = pydantic.Field(None, alias='from')
    currency: str
    """
    Three-letter ISO 4217 [currency](/bots/payments#supported-currencies) code
    """
    total_amount: int
    """
    Total price in the *smallest units* of the currency (integer, **not** float/double). For example, for a price of `US$ 1.45` pass `amount = 145`. See the *exp* parameter in [currencies.json](https://core.telegram.org/bots/payments/currencies.json), it shows the number of digits past the decimal point for each currency (2 for the majority of currencies).
    """
    invoice_payload: str
    """
    Bot specified invoice payload
    """
    shipping_option_id: typing.Optional[str]
    """
    *Optional*. Identifier of the shipping option chosen by the user
    """
    order_info: typing.Optional[OrderInfo]


class PollAnswer(_BaseModel):
    """
    This object represents an answer of a user in a non-anonymous poll.
    """

    poll_id: str
    """
    Unique poll identifier
    """
    user: User
    option_ids: list[int]
    """
    0-based identifiers of answer options, chosen by the user. May be empty if the user retracted their vote.
    """


class ChatMemberUpdated(_BaseModel):
    """
    This object represents changes in the status of a chat member.
    """

    chat: Chat
    from_: User = pydantic.Field(None, alias='from')
    date: int
    """
    Date the change was done in Unix time
    """
    old_chat_member: ChatMember
    new_chat_member: ChatMember
    invite_link: typing.Optional[ChatInviteLink]


class ChatMember(_BaseModel):
    """
    This object contains information about one member of a chat. Currently, the following 6 types of chat members are supported:
    """

    pass


class ChatInviteLink(_BaseModel):
    """
    Represents an invite link for a chat.
    """

    invite_link: str
    """
    The invite link. If the link was created by another chat administrator, then the second part of the link will be replaced with “…”.
    """
    creator: User
    is_primary: bool
    """
    True, if the link is primary
    """
    is_revoked: bool
    """
    True, if the link is revoked
    """
    expire_date: typing.Optional[int]
    """
    *Optional*. Point in time (Unix timestamp) when the link will expire or has been expired
    """
    member_limit: typing.Optional[int]
    """
    *Optional*. Maximum number of users that can be members of the chat simultaneously after joining the chat via this invite link; 1-99999
    """


class WebhookInfo(_BaseModel):
    """
    Contains information about the current status of a webhook.
    """

    url: str
    """
    Webhook URL, may be empty if webhook is not set up
    """
    has_custom_certificate: bool
    """
    True, if a custom certificate was provided for webhook certificate checks
    """
    pending_update_count: int
    """
    Number of updates awaiting delivery
    """
    ip_address: typing.Optional[str]
    """
    *Optional*. Currently used webhook IP address
    """
    last_error_date: typing.Optional[int]
    """
    *Optional*. Unix time for the most recent error that happened when trying to deliver an update via webhook
    """
    last_error_message: typing.Optional[str]
    """
    *Optional*. Error message in human-readable format for the most recent error that happened when trying to deliver an update via webhook
    """
    max_connections: typing.Optional[int]
    """
    *Optional*. Maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery
    """
    allowed_updates: typing.Optional[list[str]]
    """
    *Optional*. A list of update types the bot is subscribed to. Defaults to all update types except *chat_member*
    """


class MessageId(_BaseModel):
    """
    This object represents a unique message identifier.
    """

    message_id: int
    """
    Unique message identifier
    """


class UserProfilePhotos(_BaseModel):
    """
    This object represent a user&#39;s profile pictures.
    """

    total_count: int
    """
    Total number of profile pictures the target user has
    """
    photos: list[list[PhotoSize]]
    """
    Requested profile pictures (in up to 4 sizes each)
    """


class File(_BaseModel):
    """
    This object represents a file ready to be downloaded. The file can be downloaded via the link `https://api.telegram.org/file/bot&lt;token&gt;/&lt;file_path&gt;`. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling [getFile](https://core.telegram.org/bots/api/#getfile).

Maximum file size to download is 20 MB
    """

    file_id: str
    """
    Identifier for this file, which can be used to download or reuse the file
    """
    file_unique_id: str
    """
    Unique identifier for this file, which is supposed to be the same over time and for different bots. Can&#39;t be used to download or reuse the file.
    """
    file_size: typing.Optional[int]
    """
    *Optional*. File size in bytes, if known
    """
    file_path: typing.Optional[str]
    """
    *Optional*. File path. Use `https://api.telegram.org/file/bot&lt;token&gt;/&lt;file_path&gt;` to get the file.
    """


class ReplyKeyboardMarkup(_BaseModel):
    """
    This object represents a [custom keyboard](https://core.telegram.org/bots#keyboards) with reply options (see [Introduction to bots](https://core.telegram.org/bots#keyboards) for details and examples).
    """

    keyboard: list[list[KeyboardButton]]
    """
    Array of button rows, each represented by an Array of [KeyboardButton](https://core.telegram.org/bots/api/#keyboardbutton) objects
    """
    resize_keyboard: bool = False
    """
    *Optional*. Requests clients to resize the keyboard vertically for optimal fit (e.g., make the keyboard smaller if there are just two rows of buttons). Defaults to *false*, in which case the custom keyboard is always of the same height as the app&#39;s standard keyboard.
    """
    one_time_keyboard: bool = False
    """
    *Optional*. Requests clients to hide the keyboard as soon as it&#39;s been used. The keyboard will still be available, but clients will automatically display the usual letter-keyboard in the chat – the user can press a special button in the input field to see the custom keyboard again. Defaults to *false*.
    """
    input_field_placeholder: typing.Optional[str] = pydantic.Field(
        None,
        min_length=1,
        max_length=64,
    )
    """
    *Optional*. The placeholder to be shown in the input field when the keyboard is active; 1-64 characters
    """
    selective: typing.Optional[bool]
    """
    *Optional*. Use this parameter if you want to show the keyboard to specific users only. Targets: 1) users that are @mentioned in the *text* of the [Message](https://core.telegram.org/bots/api/#message) object; 2) if the bot&#39;s message is a reply (has *reply_to_message_id*), sender of the original message.  

*Example:* A user requests to change the bot&#39;s language, bot replies to the request with a keyboard to select the new language. Other users in the group don&#39;t see the keyboard.
    """


class KeyboardButton(_BaseModel):
    """
    This object represents one button of the reply keyboard. For simple text buttons *String* can be used instead of this object to specify text of the button. Optional fields *request_contact*, *request_location*, and *request_poll* are mutually exclusive.
    """

    text: str
    """
    Text of the button. If none of the optional fields are used, it will be sent as a message when the button is pressed
    """
    request_contact: typing.Optional[bool]
    """
    *Optional*. If *True*, the user&#39;s phone number will be sent as a contact when the button is pressed. Available in private chats only
    """
    request_location: typing.Optional[bool]
    """
    *Optional*. If *True*, the user&#39;s current location will be sent when the button is pressed. Available in private chats only
    """
    request_poll: typing.Optional[KeyboardButtonPollType]


class KeyboardButtonPollType(_BaseModel):
    """
    This object represents type of a poll, which is allowed to be created and sent when the corresponding button is pressed.
    """

    type: typing.Optional[str]
    """
    *Optional*. If *quiz* is passed, the user will be allowed to create only polls in the quiz mode. If *regular* is passed, only regular polls will be allowed. Otherwise, the user will be allowed to create a poll of any type.
    """


class ReplyKeyboardRemove(_BaseModel):
    """
    Upon receiving a message with this object, Telegram clients will remove the current custom keyboard and display the default letter-keyboard. By default, custom keyboards are displayed until a new keyboard is sent by a bot. An exception is made for one-time keyboards that are hidden immediately after the user presses a button (see [ReplyKeyboardMarkup](https://core.telegram.org/bots/api/#replykeyboardmarkup)).
    """

    remove_keyboard: bool
    """
    Requests clients to remove the custom keyboard (user will not be able to summon this keyboard; if you want to hide the keyboard from sight but keep it accessible, use *one_time_keyboard* in [ReplyKeyboardMarkup](https://core.telegram.org/bots/api/#replykeyboardmarkup))
    """
    selective: typing.Optional[bool]
    """
    *Optional*. Use this parameter if you want to remove the keyboard for specific users only. Targets: 1) users that are @mentioned in the *text* of the [Message](https://core.telegram.org/bots/api/#message) object; 2) if the bot&#39;s message is a reply (has *reply_to_message_id*), sender of the original message.  

*Example:* A user votes in a poll, bot returns confirmation message in reply to the vote and removes the keyboard for that user, while still showing the keyboard with poll options to users who haven&#39;t voted yet.
    """


class ForceReply(_BaseModel):
    """
    Upon receiving a message with this object, Telegram clients will display a reply interface to the user (act as if the user has selected the bot&#39;s message and tapped &#39;Reply&#39;). This can be extremely useful if you want to create user-friendly step-by-step interfaces without having to sacrifice [privacy mode](/bots#privacy-mode).
    """

    force_reply: bool
    """
    Shows reply interface to the user, as if they manually selected the bot&#39;s message and tapped &#39;Reply&#39;
    """
    input_field_placeholder: typing.Optional[str] = pydantic.Field(
        None,
        min_length=1,
        max_length=64,
    )
    """
    *Optional*. The placeholder to be shown in the input field when the reply is active; 1-64 characters
    """
    selective: typing.Optional[bool]
    """
    *Optional*. Use this parameter if you want to force reply from specific users only. Targets: 1) users that are @mentioned in the *text* of the [Message](https://core.telegram.org/bots/api/#message) object; 2) if the bot&#39;s message is a reply (has *reply_to_message_id*), sender of the original message.
    """


class ChatMemberOwner(_BaseModel):
    """
    Represents a [chat member](https://core.telegram.org/bots/api/#chatmember) that owns the chat and has all administrator privileges.
    """

    status: str = "creator"
    """
    The member&#39;s status in the chat, always “creator”
    """
    user: User
    is_anonymous: bool
    """
    True, if the user&#39;s presence in the chat is hidden
    """
    custom_title: typing.Optional[str]
    """
    *Optional*. Custom title for this user
    """


class ChatMemberAdministrator(_BaseModel):
    """
    Represents a [chat member](https://core.telegram.org/bots/api/#chatmember) that has some additional privileges.
    """

    status: str = "administrator"
    """
    The member&#39;s status in the chat, always “administrator”
    """
    user: User
    can_be_edited: bool
    """
    True, if the bot is allowed to edit administrator privileges of that user
    """
    is_anonymous: bool
    """
    True, if the user&#39;s presence in the chat is hidden
    """
    can_manage_chat: bool
    """
    True, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege
    """
    can_delete_messages: bool
    """
    True, if the administrator can delete messages of other users
    """
    can_manage_voice_chats: bool
    """
    True, if the administrator can manage voice chats
    """
    can_restrict_members: bool
    """
    True, if the administrator can restrict, ban or unban chat members
    """
    can_promote_members: bool
    """
    True, if the administrator can add new administrators with a subset of their own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user)
    """
    can_change_info: bool
    """
    True, if the user is allowed to change the chat title, photo and other settings
    """
    can_invite_users: bool
    """
    True, if the user is allowed to invite new users to the chat
    """
    can_post_messages: typing.Optional[bool]
    """
    *Optional*. True, if the administrator can post in the channel; channels only
    """
    can_edit_messages: typing.Optional[bool]
    """
    *Optional*. True, if the administrator can edit messages of other users and can pin messages; channels only
    """
    can_pin_messages: typing.Optional[bool]
    """
    *Optional*. True, if the user is allowed to pin messages; groups and supergroups only
    """
    custom_title: typing.Optional[str]
    """
    *Optional*. Custom title for this user
    """


class ChatMemberMember(_BaseModel):
    """
    Represents a [chat member](https://core.telegram.org/bots/api/#chatmember) that has no additional privileges or restrictions.
    """

    status: str = "member"
    """
    The member&#39;s status in the chat, always “member”
    """
    user: User


class ChatMemberRestricted(_BaseModel):
    """
    Represents a [chat member](https://core.telegram.org/bots/api/#chatmember) that is under certain restrictions in the chat. Supergroups only.
    """

    status: str = "restricted"
    """
    The member&#39;s status in the chat, always “restricted”
    """
    user: User
    is_member: bool
    """
    True, if the user is a member of the chat at the moment of the request
    """
    can_change_info: bool
    """
    True, if the user is allowed to change the chat title, photo and other settings
    """
    can_invite_users: bool
    """
    True, if the user is allowed to invite new users to the chat
    """
    can_pin_messages: bool
    """
    True, if the user is allowed to pin messages
    """
    can_send_messages: bool
    """
    True, if the user is allowed to send text messages, contacts, locations and venues
    """
    can_send_media_messages: bool
    """
    True, if the user is allowed to send audios, documents, photos, videos, video notes and voice notes
    """
    can_send_polls: bool
    """
    True, if the user is allowed to send polls
    """
    can_send_other_messages: bool
    """
    True, if the user is allowed to send animations, games, stickers and use inline bots
    """
    can_add_web_page_previews: bool
    """
    True, if the user is allowed to add web page previews to their messages
    """
    until_date: int
    """
    Date when restrictions will be lifted for this user; unix time. If 0, then the user is restricted forever
    """


class ChatMemberLeft(_BaseModel):
    """
    Represents a [chat member](https://core.telegram.org/bots/api/#chatmember) that isn&#39;t currently a member of the chat, but may join it themselves.
    """

    status: str = "left"
    """
    The member&#39;s status in the chat, always “left”
    """
    user: User


class ChatMemberBanned(_BaseModel):
    """
    Represents a [chat member](https://core.telegram.org/bots/api/#chatmember) that was banned in the chat and can&#39;t return to the chat or view chat messages.
    """

    status: str = "kicked"
    """
    The member&#39;s status in the chat, always “kicked”
    """
    user: User
    until_date: int
    """
    Date when restrictions will be lifted for this user; unix time. If 0, then the user is banned forever
    """


class BotCommand(_BaseModel):
    """
    This object represents a bot command.
    """

    command: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=32,
    )
    """
    Text of the command, 1-32 characters. Can contain only lowercase English letters, digits and underscores.
    """
    description: str = pydantic.Field(
        ...,
        min_length=3,
        max_length=256,
    )
    """
    Description of the command, 3-256 characters.
    """


class BotCommandScope(_BaseModel):
    """
    This object represents the scope to which bot commands are applied. Currently, the following 7 scopes are supported:
    """

    pass


class BotCommandScopeDefault(_BaseModel):
    """
    Represents the default [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands. Default commands are used if no commands with a [narrower scope](https://core.telegram.org/bots/api/#determining-list-of-commands) are specified for the user.
    """

    type: str = "default"
    """
    Scope type, must be *default*
    """


class BotCommandScopeAllPrivateChats(_BaseModel):
    """
    Represents the [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands, covering all private chats.
    """

    type: str = "all_private_chats"
    """
    Scope type, must be *all_private_chats*
    """


class BotCommandScopeAllGroupChats(_BaseModel):
    """
    Represents the [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands, covering all group and supergroup chats.
    """

    type: str = "all_group_chats"
    """
    Scope type, must be *all_group_chats*
    """


class BotCommandScopeAllChatAdministrators(_BaseModel):
    """
    Represents the [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands, covering all group and supergroup chat administrators.
    """

    type: str = "all_chat_administrators"
    """
    Scope type, must be *all_chat_administrators*
    """


class BotCommandScopeChat(_BaseModel):
    """
    Represents the [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands, covering a specific chat.
    """

    type: str = "chat"
    """
    Scope type, must be *chat*
    """
    chat_id: typing.Union[int, str]
    """
    Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
    """


class BotCommandScopeChatAdministrators(_BaseModel):
    """
    Represents the [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands, covering all administrators of a specific group or supergroup chat.
    """

    type: str = "chat_administrators"
    """
    Scope type, must be *chat_administrators*
    """
    chat_id: typing.Union[int, str]
    """
    Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
    """


class BotCommandScopeChatMember(_BaseModel):
    """
    Represents the [scope](https://core.telegram.org/bots/api/#botcommandscope) of bot commands, covering a specific member of a group or supergroup chat.
    """

    type: str = "chat_member"
    """
    Scope type, must be *chat_member*
    """
    chat_id: typing.Union[int, str]
    """
    Unique identifier for the target chat or username of the target supergroup (in the format `@supergroupusername`)
    """
    user_id: int
    """
    Unique identifier of the target user
    """


class InputMedia(_BaseModel):
    """
    This object represents the content of a media message to be sent. It should be one of
    """

    pass


class InputMediaPhoto(_BaseModel):
    """
    Represents a photo to be sent.
    """

    type: str = "photo"
    """
    Type of the result, must be *photo*
    """
    media: str
    """
    File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://\&lt;file_attach_name\&gt;” to upload a new one using multipart/form-data under \&lt;file_attach_name\&gt; name. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the photo to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the photo caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """


class InputMediaVideo(_BaseModel):
    """
    Represents a video to be sent.
    """

    type: str = "video"
    """
    Type of the result, must be *video*
    """
    media: str
    """
    File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://\&lt;file_attach_name\&gt;” to upload a new one using multipart/form-data under \&lt;file_attach_name\&gt; name. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    thumb: typing.Optional[typing.Union[InputFile, str]]
    """
    *Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail&#39;s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can&#39;t be reused and can be only uploaded as a new file, so you can pass “attach://\&lt;file_attach_name\&gt;” if the thumbnail was uploaded using multipart/form-data under \&lt;file_attach_name\&gt;. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the video caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    width: typing.Optional[int]
    """
    *Optional*. Video width
    """
    height: typing.Optional[int]
    """
    *Optional*. Video height
    """
    duration: typing.Optional[int]
    """
    *Optional*. Video duration in seconds
    """
    supports_streaming: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if the uploaded video is suitable for streaming
    """


class InputFile(_BaseModel):
    """
    This object represents the contents of a file to be uploaded. Must be posted using multipart/form-data in the usual way that files are uploaded via the browser.
    """

    path: str

    # @pydantic.root_validator(pre=True)
    # def check_card_number_omitted(cls, values):
    #     assert 'path' in values or 'io' in values, 'either path or io should be specified'
    #     return values


class InputMediaAnimation(_BaseModel):
    """
    Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound) to be sent.
    """

    type: str = "animation"
    """
    Type of the result, must be *animation*
    """
    media: str
    """
    File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://\&lt;file_attach_name\&gt;” to upload a new one using multipart/form-data under \&lt;file_attach_name\&gt; name. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    thumb: typing.Optional[typing.Union[InputFile, str]]
    """
    *Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail&#39;s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can&#39;t be reused and can be only uploaded as a new file, so you can pass “attach://\&lt;file_attach_name\&gt;” if the thumbnail was uploaded using multipart/form-data under \&lt;file_attach_name\&gt;. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the animation to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the animation caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    width: typing.Optional[int]
    """
    *Optional*. Animation width
    """
    height: typing.Optional[int]
    """
    *Optional*. Animation height
    """
    duration: typing.Optional[int]
    """
    *Optional*. Animation duration in seconds
    """


class InputMediaAudio(_BaseModel):
    """
    Represents an audio file to be treated as music to be sent.
    """

    type: str = "audio"
    """
    Type of the result, must be *audio*
    """
    media: str
    """
    File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://\&lt;file_attach_name\&gt;” to upload a new one using multipart/form-data under \&lt;file_attach_name\&gt; name. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    thumb: typing.Optional[typing.Union[InputFile, str]]
    """
    *Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail&#39;s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can&#39;t be reused and can be only uploaded as a new file, so you can pass “attach://\&lt;file_attach_name\&gt;” if the thumbnail was uploaded using multipart/form-data under \&lt;file_attach_name\&gt;. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the audio to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the audio caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    duration: typing.Optional[int]
    """
    *Optional*. Duration of the audio in seconds
    """
    performer: typing.Optional[str]
    """
    *Optional*. Performer of the audio
    """
    title: typing.Optional[str]
    """
    *Optional*. Title of the audio
    """


class InputMediaDocument(_BaseModel):
    """
    Represents a general file to be sent.
    """

    type: str = "document"
    """
    Type of the result, must be *document*
    """
    media: str
    """
    File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://\&lt;file_attach_name\&gt;” to upload a new one using multipart/form-data under \&lt;file_attach_name\&gt; name. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    thumb: typing.Optional[typing.Union[InputFile, str]]
    """
    *Optional*. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail&#39;s width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can&#39;t be reused and can be only uploaded as a new file, so you can pass “attach://\&lt;file_attach_name\&gt;” if the thumbnail was uploaded using multipart/form-data under \&lt;file_attach_name\&gt;. [More info on Sending Files »](https://core.telegram.org/bots/api/#sending-files)
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the document to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the document caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    disable_content_type_detection: typing.Optional[bool]
    """
    *Optional*. Disables automatic server-side content type detection for files uploaded using multipart/form-data. Always true, if the document is sent as part of an album.
    """


class StickerSet(_BaseModel):
    """
    This object represents a sticker set.
    """

    name: str
    """
    Sticker set name
    """
    title: str
    """
    Sticker set title
    """
    is_animated: bool
    """
    *True*, if the sticker set contains [animated stickers](https://telegram.org/blog/animated-stickers)
    """
    contains_masks: bool
    """
    *True*, if the sticker set contains masks
    """
    stickers: list[Sticker]
    """
    List of all set stickers
    """
    thumb: typing.Optional[PhotoSize]


class InlineQueryResult(_BaseModel):
    """
    This object represents one result of an inline query. Telegram clients currently support results of the following 20 types:
    """

    pass


class InlineQueryResultArticle(_BaseModel):
    """
    Represents a link to an article or web page.
    """

    type: str = "article"
    """
    Type of the result, must be *article*
    """
    id: str
    """
    Unique identifier for this result, 1-64 Bytes
    """
    title: str
    """
    Title of the result
    """
    input_message_content: InputMessageContent
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    url: typing.Optional[str]
    """
    *Optional*. URL of the result
    """
    hide_url: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if you don&#39;t want the URL to be shown in the message
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    thumb_url: typing.Optional[str]
    """
    *Optional*. Url of the thumbnail for the result
    """
    thumb_width: typing.Optional[int]
    """
    *Optional*. Thumbnail width
    """
    thumb_height: typing.Optional[int]
    """
    *Optional*. Thumbnail height
    """


class InputMessageContent(_BaseModel):
    """
    This object represents the content of a message to be sent as a result of an inline query. Telegram clients currently support the following 5 types:
    """

    pass


class InlineQueryResultPhoto(_BaseModel):
    """
    Represents a link to a photo. By default, this photo will be sent by the user with optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the photo.
    """

    type: str = "photo"
    """
    Type of the result, must be *photo*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    photo_url: str
    """
    A valid URL of the photo. Photo must be in **JPEG** format. Photo size must not exceed 5MB
    """
    thumb_url: str
    """
    URL of the thumbnail for the photo
    """
    photo_width: typing.Optional[int]
    """
    *Optional*. Width of the photo
    """
    photo_height: typing.Optional[int]
    """
    *Optional*. Height of the photo
    """
    title: typing.Optional[str]
    """
    *Optional*. Title for the result
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the photo to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the photo caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultGif(_BaseModel):
    """
    Represents a link to an animated GIF file. By default, this animated GIF file will be sent by the user with optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the animation.
    """

    type: str = "gif"
    """
    Type of the result, must be *gif*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    gif_url: str
    """
    A valid URL for the GIF file. File size must not exceed 1MB
    """
    gif_width: typing.Optional[int]
    """
    *Optional*. Width of the GIF
    """
    gif_height: typing.Optional[int]
    """
    *Optional*. Height of the GIF
    """
    gif_duration: typing.Optional[int]
    """
    *Optional*. Duration of the GIF in seconds
    """
    thumb_url: str
    """
    URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result
    """
    thumb_mime_type: str = "image/jpeg"
    """
    *Optional*. MIME type of the thumbnail, must be one of “image/jpeg”, “image/gif”, or “video/mp4”. Defaults to “image/jpeg”
    """
    title: typing.Optional[str]
    """
    *Optional*. Title for the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the GIF file to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultMpeg4Gif(_BaseModel):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound). By default, this animated MPEG-4 file will be sent by the user with optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the animation.
    """

    type: str = "mpeg4_gif"
    """
    Type of the result, must be *mpeg4_gif*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    mpeg4_url: str
    """
    A valid URL for the MP4 file. File size must not exceed 1MB
    """
    mpeg4_width: typing.Optional[int]
    """
    *Optional*. Video width
    """
    mpeg4_height: typing.Optional[int]
    """
    *Optional*. Video height
    """
    mpeg4_duration: typing.Optional[int]
    """
    *Optional*. Video duration in seconds
    """
    thumb_url: str
    """
    URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result
    """
    thumb_mime_type: str = "image/jpeg"
    """
    *Optional*. MIME type of the thumbnail, must be one of “image/jpeg”, “image/gif”, or “video/mp4”. Defaults to “image/jpeg”
    """
    title: typing.Optional[str]
    """
    *Optional*. Title for the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the MPEG-4 file to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultVideo(_BaseModel):
    """
    Represents a link to a page containing an embedded video player or a video file. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the video.

If an InlineQueryResultVideo message contains an embedded video (e.g., YouTube), you **must** replace its content using *input_message_content*.
    """

    type: str = "video"
    """
    Type of the result, must be *video*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    video_url: str
    """
    A valid URL for the embedded video player or video file
    """
    mime_type: str
    """
    Mime type of the content of video url, “text/html” or “video/mp4”
    """
    thumb_url: str
    """
    URL of the thumbnail (JPEG only) for the video
    """
    title: str
    """
    Title for the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the video caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    video_width: typing.Optional[int]
    """
    *Optional*. Video width
    """
    video_height: typing.Optional[int]
    """
    *Optional*. Video height
    """
    video_duration: typing.Optional[int]
    """
    *Optional*. Video duration in seconds
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultAudio(_BaseModel):
    """
    Represents a link to an MP3 audio file. By default, this audio file will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the audio.
    """

    type: str = "audio"
    """
    Type of the result, must be *audio*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    audio_url: str
    """
    A valid URL for the audio file
    """
    title: str
    """
    Title
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the audio caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    performer: typing.Optional[str]
    """
    *Optional*. Performer
    """
    audio_duration: typing.Optional[int]
    """
    *Optional*. Audio duration in seconds
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultVoice(_BaseModel):
    """
    Represents a link to a voice recording in an .OGG container encoded with OPUS. By default, this voice recording will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the the voice message.
    """

    type: str = "voice"
    """
    Type of the result, must be *voice*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    voice_url: str
    """
    A valid URL for the voice recording
    """
    title: str
    """
    Recording title
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the voice message caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    voice_duration: typing.Optional[int]
    """
    *Optional*. Recording duration in seconds
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultDocument(_BaseModel):
    """
    Represents a link to a file. By default, this file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the file. Currently, only **.PDF** and **.ZIP** files can be sent using this method.
    """

    type: str = "document"
    """
    Type of the result, must be *document*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    title: str
    """
    Title for the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the document to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the document caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    document_url: str
    """
    A valid URL for the file
    """
    mime_type: str
    """
    Mime type of the content of the file, either “application/pdf” or “application/zip”
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]
    thumb_url: typing.Optional[str]
    """
    *Optional*. URL of the thumbnail (JPEG only) for the file
    """
    thumb_width: typing.Optional[int]
    """
    *Optional*. Thumbnail width
    """
    thumb_height: typing.Optional[int]
    """
    *Optional*. Thumbnail height
    """


class InlineQueryResultLocation(_BaseModel):
    """
    Represents a location on a map. By default, the location will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the location.
    """

    type: str = "location"
    """
    Type of the result, must be *location*
    """
    id: str
    """
    Unique identifier for this result, 1-64 Bytes
    """
    latitude: Decimal
    """
    Location latitude in degrees
    """
    longitude: Decimal
    """
    Location longitude in degrees
    """
    title: str
    """
    Location title
    """
    horizontal_accuracy: typing.Optional[Decimal]
    """
    *Optional*. The radius of uncertainty for the location, measured in meters; 0-1500
    """
    live_period: typing.Optional[int]
    """
    *Optional*. Period in seconds for which the location can be updated, should be between 60 and 86400.
    """
    heading: typing.Optional[int]
    """
    *Optional*. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
    """
    proximity_alert_radius: typing.Optional[int]
    """
    *Optional*. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]
    thumb_url: typing.Optional[str]
    """
    *Optional*. Url of the thumbnail for the result
    """
    thumb_width: typing.Optional[int]
    """
    *Optional*. Thumbnail width
    """
    thumb_height: typing.Optional[int]
    """
    *Optional*. Thumbnail height
    """


class InlineQueryResultVenue(_BaseModel):
    """
    Represents a venue. By default, the venue will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the venue.
    """

    type: str = "venue"
    """
    Type of the result, must be *venue*
    """
    id: str
    """
    Unique identifier for this result, 1-64 Bytes
    """
    latitude: Decimal
    """
    Latitude of the venue location in degrees
    """
    longitude: Decimal
    """
    Longitude of the venue location in degrees
    """
    title: str
    """
    Title of the venue
    """
    address: str
    """
    Address of the venue
    """
    foursquare_id: typing.Optional[str]
    """
    *Optional*. Foursquare identifier of the venue if known
    """
    foursquare_type: typing.Optional[str]
    """
    *Optional*. Foursquare type of the venue, if known. (For example, “arts_entertainment/default”, “arts_entertainment/aquarium” or “food/icecream”.)
    """
    google_place_id: typing.Optional[str]
    """
    *Optional*. Google Places identifier of the venue
    """
    google_place_type: typing.Optional[str]
    """
    *Optional*. Google Places type of the venue. (See [supported types](https://developers.google.com/places/web-service/supported_types).)
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]
    thumb_url: typing.Optional[str]
    """
    *Optional*. Url of the thumbnail for the result
    """
    thumb_width: typing.Optional[int]
    """
    *Optional*. Thumbnail width
    """
    thumb_height: typing.Optional[int]
    """
    *Optional*. Thumbnail height
    """


class InlineQueryResultContact(_BaseModel):
    """
    Represents a contact with a phone number. By default, this contact will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the contact.
    """

    type: str = "contact"
    """
    Type of the result, must be *contact*
    """
    id: str
    """
    Unique identifier for this result, 1-64 Bytes
    """
    phone_number: str
    """
    Contact&#39;s phone number
    """
    first_name: str
    """
    Contact&#39;s first name
    """
    last_name: typing.Optional[str]
    """
    *Optional*. Contact&#39;s last name
    """
    vcard: typing.Optional[str]
    """
    *Optional*. Additional data about the contact in the form of a [vCard](https://en.wikipedia.org/wiki/VCard), 0-2048 bytes
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]
    thumb_url: typing.Optional[str]
    """
    *Optional*. Url of the thumbnail for the result
    """
    thumb_width: typing.Optional[int]
    """
    *Optional*. Thumbnail width
    """
    thumb_height: typing.Optional[int]
    """
    *Optional*. Thumbnail height
    """


class InlineQueryResultGame(_BaseModel):
    """
    Represents a [Game](https://core.telegram.org/bots/api/#games).
    """

    type: str = "game"
    """
    Type of the result, must be *game*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    game_short_name: str
    """
    Short name of the game
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]


class InlineQueryResultCachedPhoto(_BaseModel):
    """
    Represents a link to a photo stored on the Telegram servers. By default, this photo will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the photo.
    """

    type: str = "photo"
    """
    Type of the result, must be *photo*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    photo_file_id: str
    """
    A valid file identifier of the photo
    """
    title: typing.Optional[str]
    """
    *Optional*. Title for the result
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the photo to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the photo caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedGif(_BaseModel):
    """
    Represents a link to an animated GIF file stored on the Telegram servers. By default, this animated GIF file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with specified content instead of the animation.
    """

    type: str = "gif"
    """
    Type of the result, must be *gif*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    gif_file_id: str
    """
    A valid file identifier for the GIF file
    """
    title: typing.Optional[str]
    """
    *Optional*. Title for the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the GIF file to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedMpeg4Gif(_BaseModel):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound) stored on the Telegram servers. By default, this animated MPEG-4 file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the animation.
    """

    type: str = "mpeg4_gif"
    """
    Type of the result, must be *mpeg4_gif*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    mpeg4_file_id: str
    """
    A valid file identifier for the MP4 file
    """
    title: typing.Optional[str]
    """
    *Optional*. Title for the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the MPEG-4 file to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedSticker(_BaseModel):
    """
    Represents a link to a sticker stored on the Telegram servers. By default, this sticker will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the sticker.
    """

    type: str = "sticker"
    """
    Type of the result, must be *sticker*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    sticker_file_id: str
    """
    A valid file identifier of the sticker
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedDocument(_BaseModel):
    """
    Represents a link to a file stored on the Telegram servers. By default, this file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the file.
    """

    type: str = "document"
    """
    Type of the result, must be *document*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    title: str
    """
    Title for the result
    """
    document_file_id: str
    """
    A valid file identifier for the file
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the document to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the document caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedVideo(_BaseModel):
    """
    Represents a link to a video file stored on the Telegram servers. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the video.
    """

    type: str = "video"
    """
    Type of the result, must be *video*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    video_file_id: str
    """
    A valid file identifier for the video file
    """
    title: str
    """
    Title for the result
    """
    description: typing.Optional[str]
    """
    *Optional*. Short description of the result
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption of the video to be sent, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the video caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedVoice(_BaseModel):
    """
    Represents a link to a voice message stored on the Telegram servers. By default, this voice message will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the voice message.
    """

    type: str = "voice"
    """
    Type of the result, must be *voice*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    voice_file_id: str
    """
    A valid file identifier for the voice message
    """
    title: str
    """
    Voice message title
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the voice message caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InlineQueryResultCachedAudio(_BaseModel):
    """
    Represents a link to an MP3 audio file stored on the Telegram servers. By default, this audio file will be sent by the user. Alternatively, you can use *input_message_content* to send a message with the specified content instead of the audio.
    """

    type: str = "audio"
    """
    Type of the result, must be *audio*
    """
    id: str
    """
    Unique identifier for this result, 1-64 bytes
    """
    audio_file_id: str
    """
    A valid file identifier for the audio file
    """
    caption: typing.Optional[str] = pydantic.Field(
        None,
        min_length=0,
        max_length=1024,
    )
    """
    *Optional*. Caption, 0-1024 characters after entities parsing
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the audio caption. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    caption_entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in the caption, which can be specified instead of *parse_mode*
    """
    reply_markup: typing.Optional[InlineKeyboardMarkup]
    input_message_content: typing.Optional[InputMessageContent]


class InputTextMessageContent(_BaseModel):
    """
    Represents the [content](https://core.telegram.org/bots/api/#inputmessagecontent) of a text message to be sent as the result of an inline query.
    """

    message_text: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=4096,
    )
    """
    Text of the message to be sent, 1-4096 characters
    """
    parse_mode: typing.Optional[str]
    """
    *Optional*. Mode for parsing entities in the message text. See [formatting options](https://core.telegram.org/bots/api/#formatting-options) for more details.
    """
    entities: typing.Optional[list[MessageEntity]]
    """
    *Optional*. List of special entities that appear in message text, which can be specified instead of *parse_mode*
    """
    disable_web_page_preview: typing.Optional[bool]
    """
    *Optional*. Disables link previews for links in the sent message
    """


class InputLocationMessageContent(_BaseModel):
    """
    Represents the [content](https://core.telegram.org/bots/api/#inputmessagecontent) of a location message to be sent as the result of an inline query.
    """

    latitude: Decimal
    """
    Latitude of the location in degrees
    """
    longitude: Decimal
    """
    Longitude of the location in degrees
    """
    horizontal_accuracy: typing.Optional[Decimal]
    """
    *Optional*. The radius of uncertainty for the location, measured in meters; 0-1500
    """
    live_period: typing.Optional[int]
    """
    *Optional*. Period in seconds for which the location can be updated, should be between 60 and 86400.
    """
    heading: typing.Optional[int]
    """
    *Optional*. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
    """
    proximity_alert_radius: typing.Optional[int]
    """
    *Optional*. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
    """


class InputVenueMessageContent(_BaseModel):
    """
    Represents the [content](https://core.telegram.org/bots/api/#inputmessagecontent) of a venue message to be sent as the result of an inline query.
    """

    latitude: Decimal
    """
    Latitude of the venue in degrees
    """
    longitude: Decimal
    """
    Longitude of the venue in degrees
    """
    title: str
    """
    Name of the venue
    """
    address: str
    """
    Address of the venue
    """
    foursquare_id: typing.Optional[str]
    """
    *Optional*. Foursquare identifier of the venue, if known
    """
    foursquare_type: typing.Optional[str]
    """
    *Optional*. Foursquare type of the venue, if known. (For example, “arts_entertainment/default”, “arts_entertainment/aquarium” or “food/icecream”.)
    """
    google_place_id: typing.Optional[str]
    """
    *Optional*. Google Places identifier of the venue
    """
    google_place_type: typing.Optional[str]
    """
    *Optional*. Google Places type of the venue. (See [supported types](https://developers.google.com/places/web-service/supported_types).)
    """


class InputContactMessageContent(_BaseModel):
    """
    Represents the [content](https://core.telegram.org/bots/api/#inputmessagecontent) of a contact message to be sent as the result of an inline query.
    """

    phone_number: str
    """
    Contact&#39;s phone number
    """
    first_name: str
    """
    Contact&#39;s first name
    """
    last_name: typing.Optional[str]
    """
    *Optional*. Contact&#39;s last name
    """
    vcard: typing.Optional[str]
    """
    *Optional*. Additional data about the contact in the form of a [vCard](https://en.wikipedia.org/wiki/VCard), 0-2048 bytes
    """


class InputInvoiceMessageContent(_BaseModel):
    """
    Represents the [content](https://core.telegram.org/bots/api/#inputmessagecontent) of an invoice message to be sent as the result of an inline query.
    """

    title: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=32,
    )
    """
    Product name, 1-32 characters
    """
    description: str = pydantic.Field(
        ...,
        min_length=1,
        max_length=255,
    )
    """
    Product description, 1-255 characters
    """
    payload: str
    """
    Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
    """
    provider_token: str
    """
    Payment provider token, obtained via [Botfather](https://t.me/botfather)
    """
    currency: str
    """
    Three-letter ISO 4217 currency code, see [more on currencies](/bots/payments#supported-currencies)
    """
    prices: list[LabeledPrice]
    """
    Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
    """
    max_tip_amount: int
    """
    *Optional*. The maximum accepted amount for tips in the *smallest units* of the currency (integer, **not** float/double). For example, for a maximum tip of `US$ 1.45` pass `max_tip_amount = 145`. See the *exp* parameter in [currencies.json](https://core.telegram.org/bots/payments/currencies.json), it shows the number of digits past the decimal point for each currency (2 for the majority of currencies). Defaults to 0
    """
    suggested_tip_amounts: typing.Optional[list[int]]
    """
    *Optional*. A JSON-serialized array of suggested amounts of tip in the *smallest units* of the currency (integer, **not** float/double). At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed *max_tip_amount*.
    """
    provider_data: typing.Optional[str]
    """
    *Optional*. A JSON-serialized object for data about the invoice, which will be shared with the payment provider. A detailed description of the required fields should be provided by the payment provider.
    """
    photo_url: typing.Optional[str]
    """
    *Optional*. URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
    """
    photo_size: typing.Optional[int]
    """
    *Optional*. Photo size
    """
    photo_width: typing.Optional[int]
    """
    *Optional*. Photo width
    """
    photo_height: typing.Optional[int]
    """
    *Optional*. Photo height
    """
    need_name: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if you require the user&#39;s full name to complete the order
    """
    need_phone_number: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if you require the user&#39;s phone number to complete the order
    """
    need_email: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if you require the user&#39;s email address to complete the order
    """
    need_shipping_address: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if you require the user&#39;s shipping address to complete the order
    """
    send_phone_number_to_provider: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if user&#39;s phone number should be sent to provider
    """
    send_email_to_provider: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if user&#39;s email address should be sent to provider
    """
    is_flexible: typing.Optional[bool]
    """
    *Optional*. Pass *True*, if the final price depends on the shipping method
    """


class LabeledPrice(_BaseModel):
    """
    This object represents a portion of the price for goods or services.
    """

    label: str
    """
    Portion label
    """
    amount: int
    """
    Price of the product in the *smallest units* of the [currency](/bots/payments#supported-currencies) (integer, **not** float/double). For example, for a price of `US$ 1.45` pass `amount = 145`. See the *exp* parameter in [currencies.json](https://core.telegram.org/bots/payments/currencies.json), it shows the number of digits past the decimal point for each currency (2 for the majority of currencies).
    """


class ShippingOption(_BaseModel):
    """
    This object represents one shipping option.
    """

    id: str
    """
    Shipping option identifier
    """
    title: str
    """
    Option title
    """
    prices: list[LabeledPrice]
    """
    List of price portions
    """


class PassportElementError(_BaseModel):
    """
    This object represents an error in the Telegram Passport element which was submitted that should be resolved by the user. It should be one of:
    """

    pass


class PassportElementErrorDataField(_BaseModel):
    """
    Represents an issue in one of the data fields that was provided by the user. The error is considered resolved when the field&#39;s value changes.
    """

    source: str = "data"
    """
    Error source, must be *data*
    """
    type: str
    """
    The section of the user&#39;s Telegram Passport which has the error, one of “personal_details”, “passport”, “driver_license”, “identity_card”, “internal_passport”, “address”
    """
    field_name: str
    """
    Name of the data field which has the error
    """
    data_hash: str
    """
    Base64-encoded data hash
    """
    message: str
    """
    Error message
    """


class PassportElementErrorFrontSide(_BaseModel):
    """
    Represents an issue with the front side of a document. The error is considered resolved when the file with the front side of the document changes.
    """

    source: str = "front_side"
    """
    Error source, must be *front_side*
    """
    type: str
    """
    The section of the user&#39;s Telegram Passport which has the issue, one of “passport”, “driver_license”, “identity_card”, “internal_passport”
    """
    file_hash: str
    """
    Base64-encoded hash of the file with the front side of the document
    """
    message: str
    """
    Error message
    """


class PassportElementErrorReverseSide(_BaseModel):
    """
    Represents an issue with the reverse side of a document. The error is considered resolved when the file with reverse side of the document changes.
    """

    source: str = "reverse_side"
    """
    Error source, must be *reverse_side*
    """
    type: str
    """
    The section of the user&#39;s Telegram Passport which has the issue, one of “driver_license”, “identity_card”
    """
    file_hash: str
    """
    Base64-encoded hash of the file with the reverse side of the document
    """
    message: str
    """
    Error message
    """


class PassportElementErrorSelfie(_BaseModel):
    """
    Represents an issue with the selfie with a document. The error is considered resolved when the file with the selfie changes.
    """

    source: str = "selfie"
    """
    Error source, must be *selfie*
    """
    type: str
    """
    The section of the user&#39;s Telegram Passport which has the issue, one of “passport”, “driver_license”, “identity_card”, “internal_passport”
    """
    file_hash: str
    """
    Base64-encoded hash of the file with the selfie
    """
    message: str
    """
    Error message
    """


class PassportElementErrorFile(_BaseModel):
    """
    Represents an issue with a document scan. The error is considered resolved when the file with the document scan changes.
    """

    source: str = "file"
    """
    Error source, must be *file*
    """
    type: str
    """
    The section of the user&#39;s Telegram Passport which has the issue, one of “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration”, “temporary_registration”
    """
    file_hash: str
    """
    Base64-encoded file hash
    """
    message: str
    """
    Error message
    """


class PassportElementErrorFiles(_BaseModel):
    """
    Represents an issue with a list of scans. The error is considered resolved when the list of files containing the scans changes.
    """

    source: str = "files"
    """
    Error source, must be *files*
    """
    type: str
    """
    The section of the user&#39;s Telegram Passport which has the issue, one of “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration”, “temporary_registration”
    """
    file_hashes: list[str]
    """
    List of base64-encoded file hashes
    """
    message: str
    """
    Error message
    """


class PassportElementErrorTranslationFile(_BaseModel):
    """
    Represents an issue with one of the files that constitute the translation of a document. The error is considered resolved when the file changes.
    """

    source: str = "translation_file"
    """
    Error source, must be *translation_file*
    """
    type: str
    """
    Type of element of the user&#39;s Telegram Passport which has the issue, one of “passport”, “driver_license”, “identity_card”, “internal_passport”, “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration”, “temporary_registration”
    """
    file_hash: str
    """
    Base64-encoded file hash
    """
    message: str
    """
    Error message
    """


class PassportElementErrorTranslationFiles(_BaseModel):
    """
    Represents an issue with the translated version of a document. The error is considered resolved when a file with the document translation change.
    """

    source: str = "translation_files"
    """
    Error source, must be *translation_files*
    """
    type: str
    """
    Type of element of the user&#39;s Telegram Passport which has the issue, one of “passport”, “driver_license”, “identity_card”, “internal_passport”, “utility_bill”, “bank_statement”, “rental_agreement”, “passport_registration”, “temporary_registration”
    """
    file_hashes: list[str]
    """
    List of base64-encoded file hashes
    """
    message: str
    """
    Error message
    """


class PassportElementErrorUnspecified(_BaseModel):
    """
    Represents an issue in an unspecified place. The error is considered resolved when new data is added.
    """

    source: str = "unspecified"
    """
    Error source, must be *unspecified*
    """
    type: str
    """
    Type of element of the user&#39;s Telegram Passport which has the issue
    """
    element_hash: str
    """
    Base64-encoded element hash
    """
    message: str
    """
    Error message
    """


class GameHighScore(_BaseModel):
    """
    This object represents one row of the high scores table for a game.
    """

    position: int
    """
    Position in high score table for the game
    """
    user: User
    score: int
    """
    Score
    """


ResponseParameters.update_forward_refs()
Update.update_forward_refs()
Message.update_forward_refs()
User.update_forward_refs()
Chat.update_forward_refs()
ChatPhoto.update_forward_refs()
ChatPermissions.update_forward_refs()
ChatLocation.update_forward_refs()
Location.update_forward_refs()
MessageEntity.update_forward_refs()
Animation.update_forward_refs()
PhotoSize.update_forward_refs()
Audio.update_forward_refs()
Document.update_forward_refs()
Sticker.update_forward_refs()
MaskPosition.update_forward_refs()
Video.update_forward_refs()
VideoNote.update_forward_refs()
Voice.update_forward_refs()
Contact.update_forward_refs()
Dice.update_forward_refs()
Game.update_forward_refs()
Poll.update_forward_refs()
PollOption.update_forward_refs()
Venue.update_forward_refs()
MessageAutoDeleteTimerChanged.update_forward_refs()
Invoice.update_forward_refs()
SuccessfulPayment.update_forward_refs()
OrderInfo.update_forward_refs()
ShippingAddress.update_forward_refs()
PassportData.update_forward_refs()
EncryptedPassportElement.update_forward_refs()
PassportFile.update_forward_refs()
EncryptedCredentials.update_forward_refs()
ProximityAlertTriggered.update_forward_refs()
VoiceChatScheduled.update_forward_refs()
VoiceChatStarted.update_forward_refs()
VoiceChatEnded.update_forward_refs()
VoiceChatParticipantsInvited.update_forward_refs()
InlineKeyboardMarkup.update_forward_refs()
InlineKeyboardButton.update_forward_refs()
LoginUrl.update_forward_refs()
CallbackGame.update_forward_refs()
InlineQuery.update_forward_refs()
ChosenInlineResult.update_forward_refs()
CallbackQuery.update_forward_refs()
ShippingQuery.update_forward_refs()
PreCheckoutQuery.update_forward_refs()
PollAnswer.update_forward_refs()
ChatMemberUpdated.update_forward_refs()
ChatMember.update_forward_refs()
ChatInviteLink.update_forward_refs()
WebhookInfo.update_forward_refs()
MessageId.update_forward_refs()
UserProfilePhotos.update_forward_refs()
File.update_forward_refs()
ReplyKeyboardMarkup.update_forward_refs()
KeyboardButton.update_forward_refs()
KeyboardButtonPollType.update_forward_refs()
ReplyKeyboardRemove.update_forward_refs()
ForceReply.update_forward_refs()
ChatMemberOwner.update_forward_refs()
ChatMemberAdministrator.update_forward_refs()
ChatMemberMember.update_forward_refs()
ChatMemberRestricted.update_forward_refs()
ChatMemberLeft.update_forward_refs()
ChatMemberBanned.update_forward_refs()
BotCommand.update_forward_refs()
BotCommandScope.update_forward_refs()
BotCommandScopeDefault.update_forward_refs()
BotCommandScopeAllPrivateChats.update_forward_refs()
BotCommandScopeAllGroupChats.update_forward_refs()
BotCommandScopeAllChatAdministrators.update_forward_refs()
BotCommandScopeChat.update_forward_refs()
BotCommandScopeChatAdministrators.update_forward_refs()
BotCommandScopeChatMember.update_forward_refs()
InputMedia.update_forward_refs()
InputMediaPhoto.update_forward_refs()
InputMediaVideo.update_forward_refs()
InputFile.update_forward_refs()
InputMediaAnimation.update_forward_refs()
InputMediaAudio.update_forward_refs()
InputMediaDocument.update_forward_refs()
StickerSet.update_forward_refs()
InlineQueryResult.update_forward_refs()
InlineQueryResultArticle.update_forward_refs()
InputMessageContent.update_forward_refs()
InlineQueryResultPhoto.update_forward_refs()
InlineQueryResultGif.update_forward_refs()
InlineQueryResultMpeg4Gif.update_forward_refs()
InlineQueryResultVideo.update_forward_refs()
InlineQueryResultAudio.update_forward_refs()
InlineQueryResultVoice.update_forward_refs()
InlineQueryResultDocument.update_forward_refs()
InlineQueryResultLocation.update_forward_refs()
InlineQueryResultVenue.update_forward_refs()
InlineQueryResultContact.update_forward_refs()
InlineQueryResultGame.update_forward_refs()
InlineQueryResultCachedPhoto.update_forward_refs()
InlineQueryResultCachedGif.update_forward_refs()
InlineQueryResultCachedMpeg4Gif.update_forward_refs()
InlineQueryResultCachedSticker.update_forward_refs()
InlineQueryResultCachedDocument.update_forward_refs()
InlineQueryResultCachedVideo.update_forward_refs()
InlineQueryResultCachedVoice.update_forward_refs()
InlineQueryResultCachedAudio.update_forward_refs()
InputTextMessageContent.update_forward_refs()
InputLocationMessageContent.update_forward_refs()
InputVenueMessageContent.update_forward_refs()
InputContactMessageContent.update_forward_refs()
InputInvoiceMessageContent.update_forward_refs()
LabeledPrice.update_forward_refs()
ShippingOption.update_forward_refs()
PassportElementError.update_forward_refs()
PassportElementErrorDataField.update_forward_refs()
PassportElementErrorFrontSide.update_forward_refs()
PassportElementErrorReverseSide.update_forward_refs()
PassportElementErrorSelfie.update_forward_refs()
PassportElementErrorFile.update_forward_refs()
PassportElementErrorFiles.update_forward_refs()
PassportElementErrorTranslationFile.update_forward_refs()
PassportElementErrorTranslationFiles.update_forward_refs()
PassportElementErrorUnspecified.update_forward_refs()
GameHighScore.update_forward_refs()

# Some helpers
SomeUpdate = typing.Union[
    Message,
    InlineQuery,
    ChosenInlineResult,
    CallbackQuery,
    ShippingQuery,
    PreCheckoutQuery,
    Poll,
    PollAnswer,
    ChatMemberUpdated
]
