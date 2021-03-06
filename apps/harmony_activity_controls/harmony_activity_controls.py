import appdaemon.plugins.hass.hassapi as hass
import voluptuous as vol
import json
import os
import shutil

MODULE = 'harmony_activity_controls'
CLASS = 'ActivityControls'

CONF_ACTIVITIES = 'activities'
CONF_ACTIVITY = 'activity'
CONF_CLASS = 'class'
CONF_COLOR = 'color'
CONF_COMMAND = 'command'
CONF_COMMANDS = 'commands'
CONF_CUSTOM_EVENTS = 'custom_events'
CONF_DEVICE = 'device'
CONF_ENTITY_PICTURE = 'entity_picture'
CONF_EVENT = 'event'
CONF_ICON = 'icon'
CONF_LOG_LEVEL = 'log_level'
CONF_MAKE_SCRIPTS = 'make_scripts'
CONF_MODULE = 'module'
CONF_NAME = 'name'
CONF_REMOTE = 'remote'

LOG_DEBUG = 'DEBUG'
LOG_ERROR = 'ERROR'
LOG_INFO = 'INFO'
LOG_WARNING = 'WARNING'

HARMONY_ACTIVITIES = 'Activities'
HARMONY_COMMANDS = 'commands'
HARMONY_DEVICES = 'Devices'
HARMONY_ID = 'id'

ATTRIBUTE_ACTIVITY = 'activity'
ATTRIBUTE_COLOR = 'color'
ATTRIBUTE_COMMAND = 'command'
ATTRIBUTE_CURRENT_ACTIVITY = 'current_activity'
ATTRIBUTE_DEVICE = 'device'
ATTRIBUTE_ENTITY_PICTURE = 'entity_picture'
ATTRIBUTE_FRIENDLY_NAME = 'friendly_name'
ATTRIBUTE_ICON = 'icon'

ICON_GROUP = 'icon_group'

ACTIVITY_GROUP = 'activity_group'
ACTIVITY_OFF = 'PowerOff'

SENSOR = 'binary_sensor'

STATE_ON = 'on'
STATE_OFF = 'off'

ACTIVITY_SCHEMA = {
    vol.Required(CONF_ACTIVITY): str,
    vol.Required(CONF_DEVICE): str,
}

EVENT_ACTIVITY_SCHEMA = {
    vol.Required(CONF_ACTIVITY): str,
    vol.Required(CONF_DEVICE): str,
    vol.Required(CONF_COMMAND): str,
    vol.Optional(CONF_NAME): str,
    vol.Optional(CONF_COLOR): str,
    vol.Exclusive(CONF_ICON, ICON_GROUP): str,
    vol.Exclusive(CONF_ENTITY_PICTURE, ICON_GROUP): str,
}

EVENT_SCHEMA = {
    vol.Required(CONF_EVENT): str,
    vol.Required(CONF_ACTIVITIES): [EVENT_ACTIVITY_SCHEMA],
    vol.Optional(CONF_NAME): str,
    vol.Optional(CONF_COLOR): str,
    vol.Exclusive(CONF_ICON, ICON_GROUP): str,
    vol.Exclusive(CONF_ENTITY_PICTURE, ICON_GROUP): str,
}

COMMAND_SCHEMA = {
    vol.Required(CONF_COMMAND): str,
    vol.Optional(CONF_NAME): str,
    vol.Optional(CONF_COLOR): str,
    vol.Exclusive(CONF_ICON, ICON_GROUP): str,
    vol.Exclusive(CONF_ENTITY_PICTURE, ICON_GROUP): str,
}

APP_SCHEMA = vol.Schema({
    vol.Required(CONF_MODULE): MODULE,
    vol.Required(CONF_CLASS): CLASS,
    vol.Required(CONF_REMOTE): str,
    vol.Inclusive(CONF_ACTIVITIES, ACTIVITY_GROUP): [ACTIVITY_SCHEMA],
    vol.Inclusive(CONF_COMMANDS, ACTIVITY_GROUP): [vol.Any(str, COMMAND_SCHEMA)],
    vol.Optional(CONF_CUSTOM_EVENTS, default=[]): [EVENT_SCHEMA],
    vol.Optional(CONF_MAKE_SCRIPTS, default=False): bool,
    vol.Optional(CONF_LOG_LEVEL, default=LOG_DEBUG): vol.Any(LOG_INFO, LOG_DEBUG),
})

COMMAND_ICONS = {
    'PowerOff': 'mdi:power-off',
    'PowerOn': 'mdi:power-on',
    'PowerToggle': 'mdi:power',
    'Mute': 'mdi:volume-mute',
    'VolumeDown': 'mdi:volume-minus',
    'VolumeUp': 'mdi:volume-plus',
    'ChannelDown': 'mdi:menu-down',
    'ChannelUp': 'mdi:menu-up',
    'DirectionDown': 'mdi:arrow-down-bold',
    'DirectionLeft': 'mdi:arrow-left-bold',
    'DirectionRight': 'mdi:arrow-right-bold',
    'DirectionUp': 'mdi:arrow-up-bold',
    'OK': 'mdi:check-bold',
    'Stop': 'mdi:stop',
    'Play': 'mdi:play',
    'Rewind': 'mdi:rewind',
    'Eject': 'mdi:eject',
    'Pause': 'mdi:pause',
    'FastForward': 'mdi:fast-forward',
    'Record': 'mdi:record',
    'SkipBack': 'mdi:skip-backward',
    'SkipForward': 'mdi:skip-forward',
    'Menu': 'mdi:menu',
    'Subtitle': 'mdi:subtitles',
    'Back': 'mdi:arrow-left',
    'Green': 'mdi:rectangle',
    'Red': 'mdi:rectangle',
    'Blue': 'mdi:rectangle',
    'Yellow': 'mdi:rectangle',
    'Info': 'mdi:information',
    'Movies': 'mdi:filmstrip',
    'Play/Pause': 'mdi:play-pause',
    'Replay': 'mdi:replay',
    'Standby': 'mdi:power-standby',
    'Search': 'mdi:movie-search',
    'Sleep': 'mdi:sleep',
    'Exit': 'mdi:exit-to-app',
    'Home': 'mdi:home',
    'Share': 'mdi:share'
}

COMMAND_NAMES = {
    'DirectionDown': 'Down',
    'DirectionLeft': 'Left',
    'DirectionRight': 'Right',
    'DirectionUp': 'Up',
    'VolumeDown': 'Down',
    'VolumeUp': 'Up',
    'ChannelDown': 'Down',
    'ChannelUp': 'Up',
}

DEFAULT_ICON = 'mdi:eye'
DEFAULT_IMAGE_NAME = 'transparent.png'
DEFAULT_IMAGE_ABS_PATH = '/config/www/harmony_activity_controls'
DEFAULT_IMAGE_PATH = '/local/harmony_activity_controls'


class ActivityControls(hass.Hass):
    def initialize(self):

        args = APP_SCHEMA(self.args)

        # Set Lazy Logging (to not have to restart appdaemon)
        self._level = args.get(CONF_LOG_LEVEL)
        self.log(args, level=self._level)

        self._absolute_module_path = os.path.split(
            os.path.abspath(__file__))[0]
        self._absolute_default_image = os.path.join(
            DEFAULT_IMAGE_ABS_PATH, DEFAULT_IMAGE_NAME)

        self._remote = args.get(CONF_REMOTE)
        self._event_name = self._remote.replace('.', '_')

        self._harmony_config = self._get_harmony_config(self._remote)
        self.log(
            f"{self._harmony_config_dir}: {self._harmony_config}", level=self._level)

        # build 2 dictionaries of activities for quick access
        self._build_activities()

        # build 2 dictionaries of devices for quick access
        self._build_devices()

        # build a list of available commands on all devices
        self._build_commands()
        self.log(f"{CONF_COMMANDS}: {self._commands}", level=self._level)

        self._get_event_list(args)
        self.log(f"{CONF_EVENT}s: {list(self._events.keys())}",
                 level=self._level)
        for event in self._events.values():
            self.log(f'Creating Listener {event}', level=self._level)
            self.listen_event(self.harmony_event,
                              self._event_name, **event.data)

        self.handle = self.listen_state(
            self.update_sensors_callback, self._remote, attribute=ATTRIBUTE_CURRENT_ACTIVITY)

        activity = self.get_state(
            self._remote, attribute=ATTRIBUTE_CURRENT_ACTIVITY)
        self.update_sensors_callback(
            self._remote, ATTRIBUTE_CURRENT_ACTIVITY, 'AppStartUp', activity, {})

        if args.get(CONF_MAKE_SCRIPTS):
            self._make_scripts_yaml()

    def _make_scripts_yaml(self):
        lines = []
        for event in self._events.values():
            lines.append(f"{event.entity_id.split('.')[-1]}:")
            lines.append(f"  sequence:")
            lines.append(f"  - event: {self._event_name}")
            lines.append(f"    event_data: {event.data}")
            lines.append(f"")
        pth = os.path.join(self._absolute_module_path,
                           f'{self.name}_scripts_yaml.txt')
        self.log(f"Creating script yaml ({pth})", level=self._level)
        with open(pth, 'w') as fh:
            fh.write('\n'.join(lines))

    def update_sensors_callback(self, entity, attribute, old, new, kwargs):
        self.log(
            f'update_sensors_callback: {entity}.{attribute} {old} -> {new}', level=self._level)
        control_state = STATE_OFF
        for event in self._events.values():
            sensor = event.get(new)
            if sensor is not None:
                self.set_state(event.entity_id, state=sensor.state,
                               attributes=sensor.attributes)
                if control_state == STATE_OFF and sensor.state == STATE_ON:
                    control_state = STATE_ON
            else:
                off_sensor = event.get(ACTIVITY_OFF)
                self.set_state(event.entity_id, state=STATE_OFF,
                               attributes=off_sensor.attributes)

        sensor = f"{SENSOR}.{self._event_name}_control"
        attributes = {
            ATTRIBUTE_FRIENDLY_NAME: sensor.replace('_', ' ').title()
        }
        self.set_state(sensor, state=control_state, attributes=attributes)

    def harmony_event(self, event_name, data, kwargs):
        event = data.get(CONF_COMMAND)
        if event is None:
            self.log(
                f"{CONF_COMMAND} not found in event data ({data})! ", level=LOG_ERROR)
        else:
            self.log(f"Got {event_name}: {event}", level=self._level)
            event = self._events[event]

            current_activity = self.get_state(
                self._remote, attribute=ATTRIBUTE_CURRENT_ACTIVITY)

            if current_activity is None:
                self.log(
                    f"Canceling {event.event}, remote is {self.get_state(self._remote)}!", level=self._level)
            else:
                event_activity = event.get(current_activity)
                if event_activity is None:
                    self.log(
                        f"Canceling {event.event}, activity '{current_activity}' does not support event!")
                else:
                    data = {
                        CONF_DEVICE: self.get_device(event_activity.device).id,
                        CONF_COMMAND: event_activity.command,
                    }
                    self.log(
                        f"Call service: 'remote.send_command', data={data}.", level=self._level)
                    self.call_service('remote/send_command',
                                      entity_id=self._remote, **data)

    def harmony_service(self):
        self.log(kwargs, level=self._level)

    def _get_event_list(self, args):
        events = {}
        if CONF_ACTIVITIES in args and CONF_COMMANDS in args:
            unknown = []
            for commanddict in args.get(CONF_COMMANDS):
                if isinstance(commanddict, dict):
                    command = commanddict.get(CONF_COMMAND)
                    name = commanddict.get(CONF_NAME, command)
                    icon = commanddict.get(
                        CONF_ICON, COMMAND_ICONS.get(command, DEFAULT_ICON))
                    image = commanddict.get(CONF_ENTITY_PICTURE)
                    color = commanddict.get(CONF_COLOR)
                else:
                    command = commanddict
                    name = COMMAND_NAMES.get(command, command)
                    icon = COMMAND_ICONS.get(command, DEFAULT_ICON)
                    image = None
                    color = None

                if command not in self._commands:
                    self.log(
                        f"'{CONF_COMMAND}: {command}' in '{CONF_COMMANDS}' not found in {self._harmony_config_dir}", level=LOG_WARNING)

                events[command] = Event(
                    self, command, name, icon, image)
                for activitydict in args.get(CONF_ACTIVITIES):
                    in_activity = activitydict.get(CONF_ACTIVITY)
                    out_activity = self.get_activity(in_activity)

                    in_device = activitydict.get(CONF_DEVICE)
                    out_device = self.get_device(in_device)

                    if out_activity is not None and out_device is not None:
                        events[command][out_activity.name] = EventActivity(
                            events[command],
                            out_activity.name,
                            out_device.name,
                            command,
                            name,
                            icon,
                            image,
                            color)
                    else:
                        if out_activity is None:
                            activity = (CONF_ACTIVITY, in_activity)
                            if activity not in unknown:
                                unknown.append(activity)
                        if out_device is None:
                            device = (CONF_DEVICE, in_device)
                            if device not in unknown:
                                unknown.append(device)

                if events[command].finalize():
                    self._create_default_image()

            for field, result in unknown:
                self.log(
                    f"'{field}: {result}' in '{CONF_ACTIVITIES}' not found in {self._harmony_config_dir}", level=LOG_WARNING)

        for custom_event in args.get(CONF_CUSTOM_EVENTS):
            event = custom_event.get(CONF_EVENT)

            eventicon = custom_event.get(
                CONF_ICON, COMMAND_ICONS.get(command, DEFAULT_ICON))
            eventname = custom_event.get(CONF_NAME, event)
            eventimage = custom_event.get(CONF_ENTITY_PICTURE)
            eventcolor = custom_event.get(CONF_COLOR)

            events[event] = Event(self, event, eventname,
                                  eventicon, eventimage)

            for activitydict in custom_event.get(CONF_ACTIVITIES):
                in_activity = activitydict.get(CONF_ACTIVITY)
                out_activity = self.get_activity(in_activity)

                in_device = activitydict.get(CONF_DEVICE)
                out_device = self.get_device(in_device)

                command = activitydict.get(CONF_COMMAND)
                if out_activity is not None and out_device is not None and command in self._commands:
                    name = activitydict.get(
                        CONF_NAME, COMMAND_NAMES.get(command, eventname))
                    icon = activitydict.get(
                        CONF_ICON, COMMAND_ICONS.get(command, eventicon))
                    image = activitydict.get(CONF_ENTITY_PICTURE, eventimage)
                    color = activitydict.get(CONF_COLOR, eventcolor)
                    events[event][out_activity.name] = EventActivity(
                        events[event], out_activity.name, out_device.name, command, name, icon, image, color)
                else:
                    if out_activity is None:
                        self.log(
                            f"'{CONF_ACTIVITY}: {in_activity}' in '{CONF_EVENT}: {events[event].event}' not found in {self._harmony_config_dir}", level=LOG_WARNING)
                    if out_device is None:
                        self.log(
                            f"'{CONF_DEVICE}: {in_device}' in '{CONF_EVENT}: {events[event].event}' not found in {self._harmony_config_dir}", level=LOG_WARNING)
                    if command not in self._commands:
                        self.log(
                            f"'{CONF_COMMAND}: {command}' in '{CONF_EVENT}: {events[event].event}, {CONF_ACTIVITY}: {in_activity}' not found in {self._harmony_config_dir}", level=LOG_WARNING)

            if events[event].finalize():
                self._create_default_image()

        self._events = events

    def _create_default_image(self):
        if not os.path.exists(self._absolute_default_image):
            if not os.path.exists(DEFAULT_IMAGE_ABS_PATH):
                try:
                    os.mkdir(DEFAULT_IMAGE_ABS_PATH)
                except FileNotFoundError:
                    self.log(
                        f"Could not make {DEFAULT_IMAGE_ABS_PATH}!  Make sure /config/www exists!", level=LOG_WARNING)

            src = os.path.join(self._absolute_module_path, DEFAULT_IMAGE_NAME)
            shutil.copyfile(src, self._absolute_default_image)

    def _get_harmony_config(self, remote):
        """ Gets the harmony configuration """
        domain, object_id = remote.split('.')
        path = os.path.join(
            os.path.split(self.AD.config_dir)[0],
            f'harmony_{object_id}.conf'
        )
        self._harmony_config_dir = path

        data = {}
        with open(path) as fh:
            data = json.load(fh)

        return data

    def _build_activities(self):
        activity_ids, activity_names = {}, {}
        if HARMONY_ACTIVITIES in self._harmony_config:
            for activity_id, activity_name in self._harmony_config[HARMONY_ACTIVITIES].items():
                activity = Activity(activity_id, activity_name)
                activity_ids[activity_id] = activity
                activity_names[activity_name] = activity
        # make the 2 dicts
        self._activity_ids = activity_ids
        self._activity_names = activity_names

    def get_activity(self, key):
        """ Get the activity based on the provided key."""
        if key in self._activity_ids:
            return self._activity_ids.get(key)
        else:
            # assume it's in the name dict.
            return self._activity_names.get(key)

    def _build_devices(self):
        device_ids, device_names = {}, {}
        if HARMONY_DEVICES in self._harmony_config:
            for name, device_dict in self._harmony_config[HARMONY_DEVICES].items():
                commands = device_dict.get(HARMONY_COMMANDS)
                device_id = device_dict.get(HARMONY_ID)

                device = Device(device_id, name, commands)
                device_ids[device_id] = device
                device_names[name] = device
        # make the 2 device dicts
        self._device_ids = device_ids
        self._device_names = device_names

    def get_device(self, key):
        """ Get the activity based on the provided key."""
        if key in self._device_ids:
            return self._device_ids.get(key)
        else:
            # assume it's in the name dict.
            return self._device_names.get(key)

    def _build_commands(self):
        """ get the current command lists in all devices """
        commands = []
        for device in self._device_names.values():
            for command in device.commands:
                if command not in commands:
                    commands.append(command)
        self._commands = commands


class Activity(object):
    def __init__(self, activity_id, name):
        self.id = activity_id
        self.name = name


class Device(object):
    def __init__(self, device_id, name, commands):
        self.id = device_id
        self.name = name
        self.commands = commands


class EventActivity(object):
    def __init__(self, parent, activity, device, command, name, icon, image, color):
        self._parent = parent
        self.activity = activity
        self.device = device
        self.command = command
        self.name = name
        self.icon = icon
        self.image = image
        self.color = color

    @property
    def state(self):
        return STATE_OFF if self.activity == ACTIVITY_OFF else STATE_ON

    @property
    def attributes(self):
        ret = {
            ATTRIBUTE_ACTIVITY: self.activity,
            ATTRIBUTE_COMMAND: self.command,
            ATTRIBUTE_DEVICE: self.device,
            ATTRIBUTE_FRIENDLY_NAME: self.name,
        }
        if self.image is not None:
            ret[ATTRIBUTE_ENTITY_PICTURE] = self.image
        if self.icon is not None:
            ret[ATTRIBUTE_ICON] = self.icon
        if self.color is not None:
            ret[ATTRIBUTE_COLOR] = self.color
        return ret

    def __repr__(self):
        meat = ', '.join([f'"{k}":"{v}"' for k, v in self.attributes.items()])
        return f"{{{meat}}}"

    def __str__(self):
        meat = ', '.join([f'{k}<{v}>' for k, v in self.attributes.items() if k not in [
                         ATTRIBUTE_FRIENDLY_NAME, ATTRIBUTE_ICON, ATTRIBUTE_ENTITY_PICTURE]])
        return f"Activity({meat})"


class Event(object):
    def __init__(self, parent, event, name, icon, image):
        self._parent = parent
        self.event = event
        self._activities = {}
        self._activities[ACTIVITY_OFF] = EventActivity(
            self, ACTIVITY_OFF, None, None, name, icon, image, None)

    def finalize(self):
        has_image = [
            activity.image is not None for activity in self._activities.values()]
        if all(has_image) or any(has_image):
            for activity in self._activities.values():
                activity.icon = None
                if activity.image is None:
                    activity.image = os.path.join(
                        DEFAULT_IMAGE_PATH, DEFAULT_IMAGE_NAME)
            return True
        return False

    @property
    def entity_id(self):
        return f"{SENSOR}.{self._parent._event_name}_{self.event.lower()}"

    @property
    def data(self):
        return {
            CONF_COMMAND: self.event
        }

    def __getitem__(self, activity):
        return self._activities[activity]

    def __setitem__(self, key, activity):
        self._activities[key] = activity

    def get(self, activity):
        return self._activities.get(activity)

    def __repr__(self):
        meat = ','.join([a.__repr__() for a in self._activities.values()])
        return f'{{"{CONF_EVENT}":"{self.event}","attributes": [{meat}]}}'

    def __repr__(self):
        meat = ','.join([a.__str__() for a in self._activities.values()])
        return f'{CONF_EVENT}<{self.event}>({meat})'
