from requests import get as requests_get
from json import loads as json_loads
import pandas as pd
from datetime import datetime as dt
from datetime import timedelta as tdt


class GreenbyteSDK:

    # Setup the initial API connection, cache JSON for all devices and signals, generate initial SiteList,
    # populate each site with devices
    # Add attribute for default time period so someone can GreenbyteSDK.set_time('1w') as a new default
    def __init__(self, url, api_token):
        print('INITIALIZING GREENBYTE API')
        # Set up header
        self.__url = url
        self.__header = {"Breeze-ApiToken": api_token}

        # Load JSON via API call
        self.__connection = False
        self.__json_device_cache = self._get_devices()
        self.__json_signal_cache = self._get_data_signals()

        # Create Sites
        self.__sites = {(i['site']['title'], i['site']['siteId']) for i in self.__json_device_cache}
        self.__sites = SiteList([Site(site, self) for site in self.__sites], self)

        self.__signals_dict = {i['title']: i['dataSignalId'] for i in self.__json_signal_cache}

        today = dt.now()
        self.__start = dt(today.year, today.month, today.day, 0, 0, 0) - tdt(days=7)
        self.__end = today



        # Populate sites with associated devices
        for device in self.__json_device_cache:
            self.__sites.add_device(Device(device, self))

        self.__cached_signals = set()

    def connected(self):
        return self.__connection

    def _get_devices(self, device_type_ids='', fields='', page='', page_size=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('devices', **kwargs)

    def _get_data(self, deviceIds, dataSignalIds, timestampStart,
                 timestampEnd, resolution='', aggregate='', calculation=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('data', **kwargs)

    def _get_real_time_data(self, deviceIds, dataSignalIds, aggregate='', calculation=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('realtimedata', **kwargs)

    def _get_status_events(self, deviceIds, timestampStart, timestampEnd, category='', fields='',
                          sortBy='', sortAsc='', page='', pageSize=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('activestatus', **kwargs)

    def _get_active_status_events(self, deviceIds, category='', fields='', sortBy='', sortAsc='',
                                 page='', pageSize=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('status', **kwargs)

    def _get_alerts(self, deviceIds, timestampStart, timestampEnd, ruleIds='', fields='', sortBy='',
                   sortAsc='', page='', pageSize=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('alerts', **kwargs)

    def _get_active_alerts(self, deviceIds, ruleIds='', sortBy='', sortAsc='', page='', pageSize=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('activealerts', **kwargs)

    def _get_power_curves(self, deviceIds, timestamp='', learned=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('powercurves', **kwargs)

    def _get_data_signals(self, deviceIds=''):
        kwargs = locals()
        del kwargs['self']
        return self._api_call('datasignals', **kwargs)

    def _api_call(self, call, **kwargs):
        url = self.__url + str(call) + '.json?' + '&'.join([str(key) + '=' + str(value) for key, value in kwargs.items() if value != ''])\
            .replace('\'', '').replace('[', '').replace(']', '')
        print('calling:', url)
        response = requests_get(url, headers=self.__header)
        print('response: ', response)
        if response.status_code == 200:
            self.__connection = True
            return json_loads(response.text)
        else:
            return {response.status_code: response.text}

    # Call to return SiteList object given nothing, a list of sites, a single site, or a string
    # To-Do: standardize method with SiteList.devices() method, add SiteList case
    def sites(self, sites='all'):
        if sites == 'all':
            return self.__sites
        elif isinstance(sites, list):
            return SiteList([site for site in self.__sites if site.title() in sites or site in sites], self)
        elif isinstance(sites, Site) and sites in self.__sites:
            return SiteList(sites, self)
        elif isinstance(sites, str):
            return self.sites([sites])

    # Get time series data via API call
    # To-Do: Fix signal_dict so it's not hardcoded (or hardcoded with better options)
    def signals(self, device_ids, signal_keys, start_date=None, end_date=None, aggregate='', calculation=''):
        if start_date is None:
            start_date = self.__start

        if end_date is None:
            end_date = self.__end

        if not isinstance(signal_keys, list):
            signal_keys = [signal_keys]
        signal_ids = [self.__signals_dict[signal_key] for signal_key in signal_keys]

        try:
            signals = self._get_data(device_ids, signal_ids, start_date, end_date, aggregate=aggregate, calculation=calculation)

            data_list = []
            for signal in signals:
                name = signal['dataSignal']['title']
                obj_id = signal['aggregateId']
                data = signal['data']
                data = pd.Series(data, name=name)
                data = pd.DataFrame(data)
                data.index = pd.to_datetime(data.index)
                data.index.name = 'time'
                data_list.append((name, data[name], obj_id))

            return data_list

        except ValueError:
            return 'ValueError'

    def cached_signals(self):
        return self.__cached_signals

    def update_cached_signals(self, signal):
        self.__cached_signals.add(signal)

    def signal_list(self):
        return self.__signals_dict.keys()


class SiteList:
    def __init__(self, sites, api):
        if isinstance(sites, list):
            sites = sorted(sites)
            self.__sites = sites

        elif isinstance(sites, Site):
            self.__sites = [sites]

        self.__api = api
        self.__site_dict = {site.id(): site for site in self.__sites}

    def __iter__(self):
        return iter(self.__sites)

    def __str__(self):
        return str([site.__str__() for site in self.__sites])

    def __len__(self):
        return len(self.__sites)

    def titles(self):
        return sorted([site.title() for site in self.__sites])

    def ids(self):
        return sorted([site.id() for site in self.__sites])
    
    def locations(self):
        return sorted([site.location() for site in self.__sites])

    def get_site(self, site_id):
        return (self.__site_dict[site_id])

    def types(self):
        return sorted([site.id() for site in self.__sites])

    def type(self):
        if len(self.__sites) == 1:
            [type] = [site.type() for site in self.__sites]
            return type

    # Harmonize arguments and return GreenbyteSDK.sites()
    def devices(self, devices='all', flat=True):
        if devices == 'all':
            if len(self.__sites) == 1:
                return self.__sites[0].devices()
            elif flat:
                temp = [site.devices() for site in self.__sites]
                return DeviceList([i for s in temp for i in s], self.__api)
            else:
                return DeviceList([site.devices() for site in self.__sites], self.__api)

        # Need to take a string or list of strings and return a device list of those devices
        elif isinstance(devices, list):
            temp = [site.devices() for site in self.__sites]
            temp = [i for s in temp for i in s]
            temp = DeviceList(temp, self.__api)
            return DeviceList([device for device in temp if device.title() in devices or device in devices], self.__api)

        elif isinstance(devices, Device):  # and sites in self.__sites:
            return
        elif isinstance(devices, str):
            return self.devices([devices])

    # Add devices to SiteList and automatically associate them with correct site
    def add_device(self, device):
        self.__sites[self.titles().index(device.site())].add_device(device)


    def signals(self, signal_keys='Power'):
        if isinstance(signal_keys, str):
            signal_keys = [signal_keys]

        api_calls = dict()

        for key in signal_keys:
            for site in self.__sites:
                if hash((key, site)) not in self.__api.cached_signals():
                    try:
                        api_calls[key].append(site.devices().ids())
                    except KeyError:
                        api_calls[key] = site.devices().ids()

        for signal_key in api_calls.keys():
            signals = self.__api.signals([key for key in api_calls[signal_key]], signal_key, aggregate='site')
            for signal in signals:
                (title, data, aggregate_id) = signal
                site = self.get_site(aggregate_id)

                site.add_signal(Signal(signal, site, self.__api))

        s = [device.signals(signal_keys) for device in self.__sites]

        signals = []
        for i in s:
            for j in i:
                signals.append(j)

        return signals


class Site:
    def __init__(self, attr, api):
        (self.__title, self.__id) = attr
        self.__devices = None
        self.__signals = None
        self.__api = api

    def __eq__(self, other):
        if isinstance(other, Site):
            return (self.__title == other.__title) & (self.__id == other.__id)

    def __gt__(self, other):
        return self.__title > other.__title

    def __str__(self):
        return self.__title + ': ' + str(self.__id)

    def __hash__(self):
        return hash((self.__title, self.__id))

    def title(self):
        return self.__title

    def id(self):
        return self.__id

    def location(self):
        return tuple(sum(x)/len(x) for x in zip(*self.__devices.locations()))

    def devices(self):
        return self.__devices

    def type(self):
        for device in self.__devices:
            if device.type() == 'turbine':
                return 'Wind'
            elif device.type() == 'inverter':
                return 'Solar'
            else:
                return ''

    def add_device(self, device):
        if self.__devices is None and isinstance(device, Device):
            self.__devices = DeviceList(device, self.__api)
        elif device not in self.__devices:
            self.__devices.add_device(device)

    def signals(self, signal_keys='Power'):
        for key in signal_keys:
                if key not in self.__signals.keys():
                    self.add_signal(Signal(self.__api.signal(self.__devices.ids(), key, aggregate='site'), self, self.__api))

        return [self.__signals[key].data() for key in signal_keys]

    def add_signal(self, signal):
        if isinstance(signal, Signal):
            if self.__signals is None:
                self.__signals = {signal.title(): signal}
            elif signal.title() not in self.__signals.keys():
                self.__signals[signal.title()] = signal

class DeviceList:
    def __init__(self, devices, api):
        if isinstance(devices, list):
            devices = sorted(devices)
            self.__devices = devices

        elif isinstance(devices, Device):
            self.__devices = [devices]

        self.__api = api
        self.__device_dict = {device.id(): device for device in self.__devices}

    def __iter__(self):
        return iter(self.__devices)

    def __len__(self):
        return len(self.__devices)

    def __str__(self):
        return str([site.__str__() for site in self.__devices])

    def titles(self):
        return sorted([device.title() for device in self.__devices])

    def ids(self):
        return sorted([device.id() for device in self.__devices])

    def types(self):
        return sorted({device.type() for device in self.__devices})

    def locations(self):
        return sorted({device.location() for device in self.__devices})

    def devices(self):
        if not self.__devices:
            return []
        elif isinstance(self.__devices, DeviceList):
            return sorted([device.title() for device in self.__devices])

    def get_device(self, id):
        return self.__device_dict[id]

    def add_device(self, device):
        self.__devices.append(device)
        self.__device_dict[device.id()] = device

    # To-Do: Aggregate multiple devices into a single API call
    def signals(self, signal_keys='Power'):
        if isinstance(signal_keys, str):
            signal_keys = [signal_keys]

        api_calls = dict()

        for key in signal_keys:
            for device in self.__devices:
                if hash((key, device)) not in self.__api.cached_signals():
                    try:
                        api_calls[key].append(device)
                    except KeyError:
                        api_calls[key] = [device]


        for signal_key in api_calls.keys():
            signals = self.__api.signals([key.id() for key in api_calls[signal_key]], signal_key)
            for signal in signals:
                (title, data, aggregate_id) = signal
                device = self.get_device(aggregate_id)
                device.add_signal(Signal(signal, device, self.__api))

        s = [device.signals(signal_keys) for device in self.__devices]

        signals = []
        for i in s:
            for j in i:
                signals.append(j)


        return signals


class Device:
    def __init__(self, device, api):
        self.__title = device['title']
        self.__id = device['deviceId']
        self.__site = device['site']['title']
        self.__type = device['deviceType']
        self.__location = (float(device['latitude']), float(device['longitude']))
        self.__signals = None
        self.__api = api

    def __eq__(self, other):
        if isinstance(other, Device):
            return (self.__title == other.__title) & (self.__id == other.__id)

    def __gt__(self, other):
        return self.__title > other.__title

    def __str__(self):
        return self.__title + ': ' + str(self.__id)

    def __hash__(self):
        return hash((self.__title, self.__id))

    def title(self):
        return self.__title

    def id(self):
        return self.__id

    def site(self):
        return self.__site

    def type(self):
        return self.__type

    def location(self):
        return self.__location

    def signals(self, signal_keys='Power'):
        for key in signal_keys:
                if key not in self.__signals.keys():
                    self.add_signal(Signal(self.__api.signal(self.id(), key), self, self.__api))

        return [self.__signals[key].data() for key in signal_keys]

    def add_signal(self, signal):
        if isinstance(signal, Signal):
            if self.__signals is None:
                self.__signals = {signal.title(): signal}
            elif signal.title() not in self.__signals.keys():
                self.__signals[signal.title()] = signal


class Signal:
    def __init__(self, signal, obj, api):
        (self.__title, self.__data, _) = signal
        self.__obj = obj
        self.__api = api


        self._update_api_cache()

    def __eq__(self, other):
        if isinstance(other, Signal):
            return (self.__title == other.__title) & (self.__obj == other.__obj)

    def __gt__(self, other):
        return self.__title > other.__title

    def __str__(self):
        return str(self.__obj) + ': ' + self.__title + ':\n' + self.__data.to_string()

    def __hash__(self):
        return hash((self.__title, self.__obj))

    def data(self): 
        return  (self.__obj.title(), self.__data)

    def title(self):
        return self.__title

    def _update_api_cache(self):
        self.__api.update_cached_signals(hash(self))