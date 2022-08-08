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

DEFAULT_NAME = "MV Notification scrape"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Web scrape sensor."""
    name = config.get(CONF_NAME)
    resource = "https://www.manyvids.com/View-my-earnings/"
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

        self._first_feed_item_selector = "tr[id^='earnings_video']"

        self._is_rating = False

        self._username = None
        self._username_selector = "tr[id^='earnings_video']>td>a>b"

        self._video_title = None
        self._video_title_selector = "tr[id^='earnings_video']>td>a[class='is-link']"

        self._rating = None
        self._rating_selector = "tr[id^='earnings_video']>td>span.star-rating.toolTip-container"


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
    def rating(self):
        """Return rating."""
        return self._rating

    @property
    def is_rating(self):
        """Return is_rating."""
        return self._is_rating

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'username': self._username,
            'video_title': self._video_title,
            'rating': self._rating,
            'is_rating': self._is_rating,
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

            if "Read review" in first_feed_item_value:
                self._is_rating = True
            _LOGGER.debug(first_feed_item_value)
        except IndexError:
            _LOGGER.error("Unable to extract first feed item from HTML")

        try:
            username_value = raw_data.select(self._username_selector)[0].text
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
            rating_value = raw_data.select(self._rating_selector)[0].text
            rating_match = re.search("[●]+", rating_value)
            self._rating = rating_match[0].replace('●','★')
            _LOGGER.debug(rating_value)
        except IndexError:
            _LOGGER.error("Unable to extract rating from HTML")
            self._rating = None

        if self._is_rating:
            self._state = (self._username + " rated\n" + self._video_title + "\n" + self._rating)
        else:
            self._state = (self._username + " purchased\n" + self._video_title)