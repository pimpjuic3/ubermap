# Ubermap imports
from Ubermap import UbermapDevices
from Ubermap.UbermapLibs import log

# DeviceParameterComponent
from pushbase.device_parameter_component import DeviceParameterComponent

# DeviceParameterBank
from pushbase.device_parameter_bank import DeviceParameterBank

# BankingUtil
from pushbase import banking_util

# DeviceComponent
from pushbase.device_component import DeviceComponent
from pushbase.parameter_provider import generate_info

# Logging
import inspect

# Create singleton UbermapDevices instance
ubermap = UbermapDevices.UbermapDevices()

# "Monkey patch" Live methods to do fun things without having to mess with the original functionality :)
def apply_ubermap_patches():
    log.info("Applying UbermapDevices patches")

    apply_log_method_patches()
    apply_banking_util_patches()
    apply_device_component_patches()
    apply_device_parameter_bank_patches()

def apply_log_method_patches():
    # Log any method calls made to the object - useful for tracing execution flow
    # Use like: DeviceComponent.__getattribute__ = __getattribute__
    def __getattribute__(self, name):
        returned = object.__getattribute__(self, name)
        if inspect.isfunction(returned) or inspect.ismethod(returned):
            log.info('Called ' + self.__class__.__name__ + '::' + str(returned.__name__))
        return returned

def apply_banking_util_patches():
    # device_bank_names - return ubermap bank names if defined, otherwise use the default
    device_bank_names_orig = banking_util.device_bank_names

    def device_bank_names(device, bank_size = 8, definitions = None):
        ubermap_banks = ubermap.get_custom_device_banks(device)
        if ubermap_banks:
            return ubermap_banks
        ubermap.dump_device(device)

        return device_bank_names_orig(device, bank_size, definitions)

    banking_util.device_bank_names = device_bank_names

    # device_bank_count - return ubermap bank count if defined, otherwise use the default
    device_bank_count_orig = banking_util.device_bank_count

    def device_bank_count(device, bank_size = 8, definition = None, definitions = None):
        ubermap_banks = ubermap.get_custom_device_banks(device)
        if ubermap_banks:
            return len(ubermap_banks)

        return device_bank_count_orig(device, bank_size, definition, definitions)

    banking_util.device_bank_count = device_bank_count

def apply_device_component_patches():
    # _get_provided_parameters - return ubermap parameter names if defined, otherwise use the default
    _get_provided_parameters_orig = DeviceComponent._get_provided_parameters

    def _get_provided_parameters(self):
        ubermap_params = ubermap.get_custom_device_params(self._device)

        if ubermap_params:
            param_bank = ubermap_params[self._get_bank_index()]
            param_info = map(lambda param: generate_info(param, param.custom_name), param_bank)
            return param_info

        orig_params = _get_provided_parameters_orig(self)
        return orig_params

    DeviceComponent._get_provided_parameters = _get_provided_parameters

def apply_device_parameter_bank_patches():
    # DeviceParameterBank
    # _collect_parameters - this method is called by _update_parameters to determine whether we should
    # notify that parameters have been updated or not, but is hardcoded to use the default bank size
    # (i.e. full banks of 8), so ubermap banks with <8 parameters cause later banks to break. Instead return
    # the relevant ubermap bank if defined, otherwise use the default.
    _collect_parameters_orig = DeviceParameterBank._collect_parameters

    def _collect_parameters(self):
        ubermap_banks = ubermap.get_custom_device_banks(self._device)
        if ubermap_banks:
            bank = ubermap_banks[self._get_index()]
            return bank

        orig = _collect_parameters_orig(self)
        return orig

    DeviceParameterBank._collect_parameters = _collect_parameters