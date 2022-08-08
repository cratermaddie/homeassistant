"""Support for getting data from websites with scraping."""
import logging
import re

from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import voluptuous as vol

from homeassistant.components.rest.data import RestData
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_HEADERS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCE,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_SELECT = "select"
CONF_INDEX = "index"

DEFAULT_NAME = "MV Rank scrape"
DEFAULT_VERIFY_SSL = True
DEFAULT_RESOURCE = "https://www.manyvids.com/Feed/Anything4Sir/1003286576"
DEFAULT_SELECT = "span.mv-model-ranking__ranking__value"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_RESOURCE, default=DEFAULT_RESOURCE): cv.string,
        vol.Optional(CONF_SELECT, default=DEFAULT_SELECT): cv.string,
        vol.Optional(CONF_INDEX, default=0): cv.positive_int,
        vol.Optional(CONF_AUTHENTICATION): vol.In(
            [HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]
        ),
        vol.Optional(CONF_HEADERS): vol.Schema({cv.string: cv.string}),
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Web scrape sensor."""
    name = config.get(CONF_NAME)
    resource = config.get(CONF_RESOURCE)
    method = "GET"
#    payload = None
    params = None
    data = None
    headers = config.get(CONF_HEADERS)
    verify_ssl = config.get(CONF_VERIFY_SSL)
    select = config.get(CONF_SELECT)
    index = config.get(CONF_INDEX)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    if username and password:
        if config.get(CONF_AUTHENTICATION) == HTTP_DIGEST_AUTHENTICATION:
            auth = HTTPDigestAuth(username, password)
        else:
            auth = HTTPBasicAuth(username, password)
    else:
        auth = None
#    rest = RestData(method, resource, auth, headers, payload, verify_ssl)
    rest = RestData(hass, method, resource, auth, headers, params, data, verify_ssl)
    rest.async_update()

    if rest.data is None:
        raise PlatformNotReady

    add_entities(
        [ScrapeSensor(hass, rest, name, select, index)]
    )
    return True


class ScrapeSensor(Entity):
    """Representation of a web scrape sensor."""

    def __init__(self, hass, rest, name, select, index):
        """Initialize a web scrape sensor."""
        self._hass = hass
        self.rest = rest
        self._name = name
        self._state = None
        self._rank = None
        self._followers = None
        self._select = select
        self._index = index


    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def rank(self):
        """Return rank."""
        return self._rank

    @property
    def followers(self):
        """Return followers."""
        return self._followers

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'rank': self._rank,
            'followers': self._followers,
        }

    def update(self):
        """Get the latest data from the source and updates the state."""
        self.rest.async_update()
        if self.rest.data is None:
            _LOGGER.error("Unable to retrieve data")
            return

        raw_data = BeautifulSoup(self.rest.data, "html.parser")
        _LOGGER.debug(raw_data)

        try:
            rank_value = raw_data.select(self._select)[0].text
            rank_match = re.search("[\d\.]+", rank_value)
            self._state = self._rank = (float(rank_match[0])*1000)
            _LOGGER.debug(rank_value)
        except IndexError:
            _LOGGER.error("Unable to extract rank from HTML")
            self._state = self._rank = None

        try:
            followers_value = raw_data.select(self._select)[1].text
            followers_match = re.search("\d+", followers_value)
            self._followers = followers_match[0]
            _LOGGER.debug(followers_value)
        except IndexError:
            _LOGGER.error("Unable to extract followers from HTML")
            self._followers = None