from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, set_ev_cls
from ryu.app.simple_switch_13 import SimpleSwitch13

GAME_PORT = 5000
BOTTLENECK_PORT = 5   # s1-eth5, the link to s2
GAME_QUEUE = 1


class QosSwitch(SimpleSwitch13):

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def install_game_rule(self, ev):
        dp = ev.msg.datapath
        if dp.id != 1:      # only s1 needs the rule
            return
        ofp = dp.ofproto
        parser = dp.ofproto_parser
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=17,
                                udp_dst=GAME_PORT)
        actions = [parser.OFPActionSetQueue(GAME_QUEUE),
                   parser.OFPActionOutput(BOTTLENECK_PORT)]
        inst = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS,
                                             actions)]
        dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=100,
                                      match=match, instructions=inst))
        self.logger.info("Game rule installed on s1")
