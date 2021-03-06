# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------------
# Name:         sfp_template
# Purpose:      Example module to use for new modules.
#
# Author:      Steve Micallef <steve@binarypool.com>
#
# Created:     21/04/2020
# Copyright:   (c) Steve Micallef
# Licence:     GPL
# -------------------------------------------------------------------------------

from sflib import SpiderFoot, SpiderFootPlugin, SpiderFootEvent

class sfp_template(SpiderFootPlugin):
    #
    # Format of the below must be, in order, separated by ':'
    #
    # Module name: A very short but human readable name for the module.
    # Use cases: The use case(s) this module should be included in, options are Footprint, Investigate and Passive.
    #   - Passive means the user's scan target is not contacted at all
    #   - Footprint means that this module is useful when understanding the target's footprint on the Internet
    #   - Investigate means that this module is useful when investigating the danger/risk of a target
    # Category: The category this module belongs in, describing how it operates. Only one category is permitted.
    #   - Content Analysis: Analyses content found
    #   - Crawling and Scanning: Performs crawling or scanning of the target
    #   - DNS: Queries DNS
    #   - Leaks, Dumps and Breaches: Queries data dumps and breaches
    #   - Passive DNS: Analyses passive DNS sources
    #   - Public Registries: Queries open/public registries of information
    #   - Real World: Queries sources about the real world (addresses, names, etc.)
    #   - Reputation Systems: Queries systems that describe the reptuation of other systems
    #   - Search Engines: Searches public search engines with data about the whole Internet
    #   - Secondary Networks: Queries information about participation on secondary networks, like Bitcoin
    #   - Social Media: Searches social media data sources
    # Flags: Attributes about this module:
    #   - apikey: Needs an API key to function
    #   - slow: Can be slow to find information
    #   - errorprone: Might generate high false positives
    #   - invasive: Interrogates the target, might be intensive
    #   - tool: Runs an external tool to collect data
    # Description: A sentence briefly describing the module.
    #
    """Template Module:Footprint,Investigate,Passive:Search Engines:apikey:Obtain open port from SomeDataSource about identified IP addresses."""

    # Default options. Delete any options not applicable to this module. Descriptions for each option
    # are defined in optdescs below. Options won't show up in the UI if they don't have an entry in
    # optdescs. This can be useful when you want something configured in code but not by the user.
    #
    # Note that these are just dictionary entries. The logic for how you react to these settings
    # is entirely for you to define AND IMPLEMENT in this module - nothing comes for free! :)
    #
    # Look at other modules for examples for how these settings are handled and implemented.
    #
    opts = {
        # If the module needs an API key, ensure api_key is in the name so that it gets
        # picked up as such in the UI.
        'api_key': '',
        # If the module accepts CO_HOSTED_SITE as an event, it sometimes makes sense to make
        # that configurable since some users don't care about co-hosted sites.
        'checkcohosts': True,
        # As above, but for affiliates.
        'checkaffiliates': True,
        # As above, but for NETBLOCK_MEMBERs.
        'subnetlookup': False,
        # As abovem but for NETBLOCK_OWNER
        'netblocklookup': True,
        # If subnetlookup is true, what's the maximum size subnet to iterate through?
        'maxsubnet': 24,
        # As above but for netblocks owned.
        'maxnetblock': 24,
        # For modules reporting CO_HOSTED_SITE events, it makes sense to put a cap
        # on how many to return since a high number usually indicates hosting, and users
        # likely do not care about such cases.
        'maxcohost': 100,
        # When reporting hosts, perform DNS lookup to check if they still resolve, and
        # if not report INTERNET_NAME_UNRESOLVED instead, if appropriate.
        'verify': True,
        # If reporting co-hosted sites, consider a site co-hosted if its domain matches
        # the target?
        "cohostsamedomain": False
    }

    # Option descriptions. Delete any options not applicable to this module.
    optdescs = {
        "api_key": "SomeDataource API Key.",
        'checkcohosts': "Check co-hosted sites?",
        'checkaffiliates': "Check affiliates?",
        'netblocklookup': "Look up all IPs on netblocks deemed to be owned by your target for possible blacklisted hosts on the same target subdomain/domain?",
        'maxnetblock': "If looking up owned netblocks, the maximum netblock size to look up all IPs within (CIDR value, 24 = /24, 16 = /16, etc.)",
        'subnetlookup': "Look up all IPs on subnets which your target is a part of?",
        'maxsubnet': "If looking up subnets, the maximum subnet size to look up all the IPs within (CIDR value, 24 = /24, 16 = /16, etc.)",
        'maxcohost': "Stop reporting co-hosted sites after this many are found, as it would likely indicate web hosting.",
        "cohostsamedomain": "Treat co-hosted sites on the same target domain as co-hosting?",
        'verify': 'Verify that any hostnames found on the target domain still resolve?'

    }

    # Tracking results can be helpful to avoid reporting/processing duplicates
    results = None

    # Tracking the error state of the module can be useful to detect when a third party
    # has failed and you don't wish to process any more events.
    errorState = False

    def setup(self, sfc, userOpts=dict()):
        self.sf = sfc
        # self.tempStorage() basically returns a dict(), but we use self.tempStorage()
        # instead since on SpiderFoot HX, different mechanisms are used to persist
        # data for load distribution, avoiding excess memory consumption and fault 
        # tolerance. This keeps modules transparently compatible with both versions.
        self.results = self.tempStorage()

        # Clear / reset any other class member variables here
        # or you risk them persisting between threads.

        for opt in list(userOpts.keys()):
            self.opts[opt] = userOpts[opt]

    # What events is this module interested in for input
    # For a list of all events, check sfdb.py.
    def watchedEvents(self):
        return ["IP_ADDRESS", "NETBLOCK_OWNER", "DOMAIN_NAME", "WEB_ANALYTICS_ID"]

    # What events this module produces
    def producedEvents(self):
        return ["OPERATING_SYSTEM", "DEVICE_TYPE",
                "TCP_PORT_OPEN", "TCP_PORT_OPEN_BANNER",
                'RAW_RIR_DATA', 'GEOINFO', 'VULNERABILITY']

    # When querying third parties, it's best to have a dedicated function
    # to do so and avoid putting it in handleEvent()
    def query(self, qry):

        # This is an example of querying SHODAN. Note that the fetch timeout
        # is inherited from global options (options prefixed with _ will come
        # from global config), and the user agent is SpiderFoot so that the
        # provider knows the request comes from the tool. Many third parties
        # request that, so best to just be consistent anyway.
        res = self.sf.fetchUrl("https://api.shodan.io/shodan/host/" + qry +
                               "?key=" + self.opts['api_key'],
                               timeout=self.opts['_fetchtimeout'], 
                               useragent="SpiderFoot")

        # Report when unexpected things happen:
        # - debug(message) if it's only for debugging (user will see this if debugging is enabled)
        # - info(message) if it's not a bad thing
        # - error(message, False) if it's a bad thing but SpiderFoot can continue
        # - error(message) if it's a bad thing and should cause the scan to abort
        # - fatal(message) if it's a horrible thing and should kill SpiderFoot completely
        if res['content'] is None:
            self.sf.info("No SHODAN info found for " + qry)
            return None

        # Always always always process external data with try/except since we cannot
        # trust the data is as intended.
        try:
            info = json.loads(res['content'])
        except Exception as e:
            self.sf.error("Error processing JSON response from SHODAN.", False)
            return None

        return info

    # Handle events sent to this module
    def handleEvent(self, event):
        # The three most used fields in SpiderFootEvent are:
        # event.eventType - the event type, e.g. INTERNET_NAME, IP_ADDRESS, etc.
        # event.module - the name of the module that generated the event, e.g. sfp_dnsresolve
        # event.data - the actual data, e.g. 127.0.0.1. This can sometimes be megabytes in size (e.g. a PDF)
        eventName = event.eventType
        srcModuleName = event.module
        eventData = event.data

        # Once we are in this state, return immediately.
        if self.errorState:
            return None

        # Log this before complaining about a missing API key so we know the
        # event was received.
        self.sf.debug("Received event, " + eventName + ", from " + srcModuleName)

        # Always check if the API key is set and complain if it isn't, then set
        # self.errorState to avoid this being a continual complaint during the scan.
        if self.opts['api_key'] == "":
            self.sf.error("You enabled sfp_template but did not set an API key!", False)
            self.errorState = True
            return None

        # Don't look up stuff twice
        if eventData in self.results:
            self.sf.debug("Skipping " + eventData + " as already mapped.")
            return None
        else:
            # If eventData might be something large, set the key to a hash
            # of the value instead of the value, to avoid memory abuse.
            self.results[eventData] = True

        if eventName == 'NETBLOCK_OWNER':
            # Note here an example of handling the netblocklookup option
            if not self.opts['netblocklookup']:
                return None
            else:
                if IPNetwork(eventData).prefixlen < self.opts['maxnetblock']:
                    self.sf.debug("Network size bigger than permitted: " +
                                  str(IPNetwork(eventData).prefixlen) + " > " +
                                  str(self.opts['maxnetblock']))
                    return None

        # When handling netblocks/subnets, assuming the user set
        # netblocklookup/subnetlookup to True, we need to expand it
        # to the IPs for looking up.
        if eventName.startswith("NETBLOCK_"):
            for ipaddr in IPNetwork(eventData):
                qrylist.append(str(ipaddr))
                self.results[str(ipaddr)] = True
        else:
            qrylist.append(eventData)

        for addr in qrylist:
            # Perform the query to the third party; in this case for each IP
            # being queried.
            rec = self.query(addr)

            # Handle the response being empty/failing
            if rec is None:
                continue

            # For netblocks, we need to create the IP address event so that
            # the threat intel event is more meaningful and linked to the
            # IP address within the network, not the whole network.
            if eventName.startswith('NETBLOCK_'):
                # This is where the module generates an event for other modules
                # to process and is a fundamental part of the SpiderFoot architecture.
                # We are generating an event of type "IP_ADDRESS" here, the data being
                # the addr variable, the name of the module is the next argument
                # (self.__name__), and finally the event that is linked as the source
                # event of this event. This enables SpiderFoot to link events so users
                # can see what events generated other events, seeing a full chain of
                # discovery from their target to the data returned here.
                pevent = SpiderFootEvent("IP_ADDRESS", addr, self.__name__, event)
                # With the event created, we can now notify any other modules listening
                # for IP_ADDRESS events (which they define in their watchedEvents()
                # function).
                self.notifyListeners(pevent)
            else:
                # If the event received wasn't a netblock, then use that event
                # as the source event for later events.
                pevent = event

            # When querying a third party API, always ensure to generate
            # a RAW_RIR_DATA event. Note that here we are seeing the pevent
            # event as the source for this, since the IP address is actually
            # what was queried against the third party, not the netblock.
            # So now we have NETBLOCK_OWNER (event we received) -> IP_ADDRESS
            # (event we generated above) -> RAW_RIR_DATA (event from the third
            # party about the IP Address we queried).
            evt = SpiderFootEvent("RAW_RIR_DATA", str(rec), self.__name__, pevent)
            self.notifyListeners(evt)

            # Whenever operating in a loop, call this to check whether the user
            # requested the scan to be aborted.
            if self.checkForStop():
                return None

            # Note that we are using rec.get('os') instead of rec['os'] - this
            # means we won't get an exception if the 'os' key doesn't exist. In
            # general, you should always use .get() instead of accessing keys
            # directly in case the key doesn't exist.
            if rec.get('os') is not None:
                evt = SpiderFootEvent("OPERATING_SYSTEM", rec.get('os') +
                                      " (" + addr + ")", self.__name__, pevent)
                self.notifyListeners(evt)

# End of sfp_template class
