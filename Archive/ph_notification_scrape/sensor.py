"""Support for getting data from websites with scraping."""
import logging
import re

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import voluptuous as vol

from homeassistant.components.rest.data import RestData
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_HEADERS,
    CONF_NAME,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "PH Notification scrape"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Web scrape sensor."""
    name = config.get(CONF_NAME)
    resource = "https://www.pornhub.com/notifications"
    method = "GET"
#    payload = None
    params = None
    data = None
    headers = config.get(CONF_HEADERS)
    verify_ssl = True
    auth = None
#    rest = RestData(method, resource, auth, headers, payload, verify_ssl)
    rest = RestData(hass, method, resource, auth, headers, params, data, verify_ssl)
    rest.async_update()

    if rest.data is None:
        raise PlatformNotReady

    add_entities(
        [ScrapeSensor(hass, rest, name)]
    )
    return True


class ScrapeSensor(Entity):
    """Representation of a web scrape sensor."""

    def __init__(self, hass, rest, name):
        """Initialize a web scrape sensor."""
        self._hass = hass
        self._rest = rest
        self._name = name
        self._state = None

        self._first_feed_item_selector = "div.feedInfo"

        self._is_comment = False

        self._username = None
        self._username_selector = "div.userWidgetWrapperGrid.float-left>div.user-flag.large-avatar>a.userLink.clearfix>img.lazy.avatar.avatarTrigger" #alt

        self._video_title = None
        self._video_title_selector = "div.title>a"

        self._comment = None
        self._comment_selector = "div.feedCaption.float-left"

        self._purchase_caption = None
        self._purchase_caption_selector = "div.feedCaption.contentPadding>div"


    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def username(self):
        """Return username."""
        return self._username

    @property
    def video_title(self):
        """Return video_title."""
        return self._video_title

    @property
    def comment(self):
        """Return comment."""
        return self._comment

    @property
    def purchase_caption(self):
        """Return purchase_caption."""
        return self._purchase_caption

    @property
    def is_comment(self):
        """Return is_comment."""
        return self._is_comment

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'username': self._username,
            'video_title': self._video_title,
            'comment': self._comment,
            'purchase_caption': self._purchase_caption,
            'is_comment': self._is_comment,
        }

    def update(self):
        """Get the latest data from the source and updates the state."""
        self._rest.async_update()
        if self._rest.data is None:
            _LOGGER.error("Unable to retrieve data")
            return

        raw_data = BeautifulSoup(self._rest.data, "html.parser")
        _LOGGER.debug(raw_data)

        try:
            first_feed_item_value = raw_data.select(self._first_feed_item_selector)[0].text

            if "commented on" in first_feed_item_value:
                self._is_comment = True
            _LOGGER.debug(first_feed_item_value)
        except IndexError:
            _LOGGER.error("Unable to extract first feed item from HTML")

        try:
            username_value = raw_data.select(self._username_selector)[0]["alt"]
            self._username = username_value
            _LOGGER.debug(username_value)
        except IndexError:
            _LOGGER.error("Unable to extract username from HTML")
            self._username = None

        try:
            video_title_value = raw_data.select(self._video_title_selector)[0].text
            self._video_title = video_title_value
            _LOGGER.debug(video_title_value)
        except IndexError:
            _LOGGER.error("Unable to extract video title from HTML")
            self._video_title = None

        try:
            comment_value = raw_data.select(self._comment_selector)[0].text
            self._comment = comment_value
            _LOGGER.debug(comment_value)
        except IndexError:
            _LOGGER.error("Unable to extract comment from HTML")
            self._comment = None

        try:
            purchase_caption_value = raw_data.select(self._purchase_caption_selector)[0].text
            self._purchase_caption = purchase_caption_value
            _LOGGER.debug(purchase_caption_value)
        except IndexError:
            _LOGGER.error("Unable to extract purchase caption from HTML")
            self._purchase_caption = None

        if self._is_comment:
            self._state = (self._username + " commented on\n" + self._video_title + ":\n" + self._comment)
        else:
            self._state = self._purchase_caption