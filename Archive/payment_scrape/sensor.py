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
    CONF_UNIT_OF_MEASUREMENT,
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

DEFAULT_NAME = "Payment scrape"
DEFAULT_VERIFY_SSL = True
DEFAULT_RESOURCE = "https://www.pornhub.com/model/payments"
DEFAULT_SELECT = "div.sectionWrapper.topPayWrapper"
DEAFULT_VALUE_TEMPLATE = "{{ value.replace('Current Balance: $','') }}"
DEFAULT_UNIT_OF_MEASUREMENT = "$"

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
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE, default=DEAFULT_VALUE_TEMPLATE): cv.template,
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
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass

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
        [ScrapeSensor(rest, name, select, attr, index, value_template, unit)]
    )

    return True


class ScrapeSensor(Entity):
    """Representation of a web scrape sensor."""

    def __init__(self, rest, name, select, attr, index, value_template, unit):
        """Initialize a web scrape sensor."""
        self.rest = rest
        self._name = name
        self._state = None
        self._table = None
        self._select = select
        self._table_select = "#tableDataEarnings"
        self._attr = attr
        self._index = index
        self._value_template = value_template
        self._unit_of_measurement = unit

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def table(self):
        """Return the latitude of the device."""
        return self._table

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            'table': self._table
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

        if self._value_template is not None:

            match = re.search("Current Balance: \$[0-9\.]+", value)

            self._state = self._value_template.render_with_possible_json_value(
                match.group(0), None
            )
        else:
            self._state = value

        self._table = raw_data.select(self._table_select)[self._index].text