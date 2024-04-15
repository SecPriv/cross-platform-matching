from dataclasses import dataclass
from typing import Optional


@dataclass(kw_only=True)
class Plist:

    path: Optional[str] = None
    raw_data: Optional[dict] = None
    en_strings: Optional[dict] = None
    de_strings: Optional[dict] = None
    permissions: Optional[list[dict]] = None
    # for reference: 
    # https://developer.apple.com/library/archive/documentation/General/Reference/InfoPlistKeyReference/Introduction/Introduction.html
    # https://developer.apple.com/documentation/bundleresources/information_property_list
    supported_platforms: Optional[list[str]] = None # CFBundleSupportedPlatforms
    build_version: Optional[str] = None # CFBundleVersion
    app_version: Optional[str] = None # CFBundleShortVersionString
    minimum_ios_version: Optional[str] = None # MinimumOSVersion
    app_transport_security_changes: Optional[list[dict]] = None # NSAppTransportSecurity - A description of changes made to the default security for HTTP connections.
    ad_network_ids: Optional[list[str]] = None # SKAdNetworkItems
    custom_url_schemes: Optional[list[dict]] = None
    local_network_usage_description: Optional[str] = None
    bonjour_services: Optional[list[str]] = None
    api_keys: Optional[list[dict]] = None
    