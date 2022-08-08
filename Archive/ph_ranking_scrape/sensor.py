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
    CONF_VALUE_TEMPLATE,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_ATTR = "attribute"
CONF_SELECT = "select"
CONF_INDEX = "index"

DEFAULT_NAME = "PH Ranking scrape"
DEFAULT_VERIFY_SSL = True
DEFAULT_RESOURCE = "https://www.pornhub.com/model/anything4sir"
DEFAULT_SELECT = "div.infoBoxes"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_RESOURCE, default=DEFAULT_RESOURCE): cv.string,
        vol.Optional(CONF_SELECT, default=DEFAULT_SELECT): cv.string,
        vol.Optional(CONF_ATTR): cv.string,
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
    attr = config.get(CONF_ATTR)
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
        [ScrapeSensor(rest, name, select, attr, index)]
    )

    return True


class ScrapeSensor(Entity):
    """Representation of a web scrape sensor."""

    def __init__(self, rest, name, select, attr, index):
        """Initialize a web scrape sensor."""
        self.rest = rest
        self._name = name
        self._state = None
        self._model_rank = None
        self._weekly_rank = None
        self._monthly_rank = None
        self._last_month_rank = None
        self._yearly_rank = None
        self._video_views = None
        self._subscribers = None
        self._select = select
        self._attr = attr
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
    def model_rank(self):
        """Return model_rank."""
        return self._model_rank

    @property
    def weekly_rank(self):
        """Return weekly_rank."""
        return self._weekly_rank

    @property
    def monthly_rank(self):
        """Return monthly_rank."""
        return self._monthly_rank

    @property
    def last_month_rank(self):
        """Return last_month_rank."""
        return self._last_month_rank

    @property
    def yearly_rank(self):
        """Return yearly_rank."""
        return self._yearly_rank

    @property
    def video_views(self):
        """Return video_views."""
        return self._video_views

    @property
    def subscribers(self):
        """Return subscribers."""
        return self._subscribers

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'model_rank': self._model_rank,
            'weekly_rank': self._weekly_rank,
            'monthly_rank': self._monthly_rank,
            'last_month_rank': self._last_month_rank,
            'yearly_rank': self._yearly_rank,
            'video_views': self._video_views,
            'subscribers': self._subscribers,
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
            if self._attr is not None:
                value = raw_data.select(self._select)[self._index][self._attr]
            else:
                value = raw_data.select(self._select)[self._index].text
            _LOGGER.debug(value)
        except IndexError:
            _LOGGER.error("Unable to extract data from HTML")
            return
            
        match = re.findall("[0-9]+\.*,*[0-9]*K*", value)
        try:
            self._state = match[0].replace(',','').replace('K','000').replace('.','')
            self._model_rank = match[0].replace(',','').replace('K','000').replace('.','')
            self._weekly_rank = match[1].replace(',','').replace('K','000').replace('.','')
            self._monthly_rank = match[2].replace(',','').replace('K','000').replace('.','')
            self._last_month_rank = match[3].replace(',','').replace('K','000').replace('.','')
            self._yearly_rank = match[4].replace(',','').replace('K','000').replace('.','')
            self._video_views = match[5].replace(',','').replace('K','000').replace('.','')
            self._subscribers = match[6].replace(',','').replace('K','000').replace('.','')
        except IndexError:
            self._state = None
            _LOGGER.error("Unexpected value: " + str(match))
            return