# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.util as pu 
import pox.lib.packet as pk
log = core.getLogger()

ip_to_mac = {
    "10.0.0.1": pk.EthAddr("00:00:00:00:00:01"),
    "10.0.0.2": pk.EthAddr("00:00:00:00:00:02"),
    "10.0.0.3": pk.EthAddr("00:00:00:00:00:03"),
    "10.0.0.4": pk.EthAddr("00:00:00:00:00:04")
}

class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection
    log.debug("Pdi {}".format(pu.dpid_to_str(connection.dpid)))
     # This binds our PacketIn event listener
    dpid = pu.dpid_to_str(connection.dpid) 
    print(dpid) 
    iden =int(dpid[len(dpid) - 1]) 

    if iden == 1:
        # a to b 
        self.install_flow(1, "10.0.0.2", "10.0.0.1") 
        self.install_flow(0, "10.0.0.1", "10.0.0.2")

        # a to c 
        self.install_flow(2, "10.0.0.3", "10.0.0.1") 
        self.install_flow(0, "10.0.0.1", "10.0.0.3")

        log.debug("One is up")
    elif iden == 2:
        #b to d 
        self.install_flow(2, "10.0.0.4", "10.0.0.2") 
        self.install_flow(1, "10.0.0.2", "10.0.0.4") 

        #b to a 
        self.install_flow(0, "10.0.0.1", "10.0.0.2")
        self.install_flow(1, "10.0.0.2", "10.0.0.1") 

        log.debug("Two is online") 
    else:
        #d to b 
        self.install_flow(2, "10.0.0.4", "10.0.0.2")
        self.install_flow(1, "10.0.0.2", "10.0.0.4")
        
        #c to a 
        self.install_flow(0, "10.0.0.1", "10.0.0.3")
        self.install_flow(3, "10.0.0.3", "10.0.0.1") 

        log.debug("three online") 

        
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}
    
  def install_flow(self, port, ip, src_ip):
    self.connection.send(of.ofp_flow_mod(action=of.ofp_action_output(port=port),
                                        match=of.ofp_match(nw_dst=ip, nw_src=src_ip, dl_type=0x0800)))
  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """

    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """

    """ # DELETE THIS LINE TO START WORKING ON THIS (AND THE ONE BELOW!) #

    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    self.mac_to_port ... <add or update entry>

    if the port associated with the destination MAC of the packet is known:
      # Send packet out the associated port
      self.resend_packet(packet_in, ...)

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      #msg = of.ofp_flow_mod()
      #
      ## Set fields to match received packet
      #msg.match = of.ofp_match.from_packet(packet)
      #
      #< Set other fields of flow_mod (timeouts? buffer_id?) >
      #
      #< Add an output action, and send -- similar to resend_packet() >

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.resend_packet(packet_in, of.OFPP_ALL)

    """ # DELETE THIS LINE TO START WORKING ON THIS #


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
   
    print(packet) 
    print(packet.type) 
    print(packet.payload)
    print(packet.src) 

            
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    packet_in = event.ofp # The actual ofp_packet_in message.

    if packet.type == packet.ARP_TYPE:
        if packet.payload.opcode == pk.arp.REQUEST:
            reply = pk.arp()
            dst_mac = ip_to_mac[str(packet.payload.protodst)] 

            reply.hwtype = packet.payload.hwtype 
            reply.prototype = packet.payload.prototype
            reply.hwlen = packet.payload.hwlen 
            reply.protolen = packet.payload.protolen
            reply.hwsrc = dst_mac 
            reply.hwdst = packet.payload.hwsrc 
            reply.opcode = pk.arp.REPLY
            reply.protosrc = packet.payload.protodst 
            reply.protodst = packet.payload.protosrc
            ether = pk.ethernet() 
            ether.type = pk.ethernet.ARP_TYPE
            ether.dst = packet.payload.hwsrc 
            ether.src = dst_mac 
            ether.set_payload(reply) 

            msg = of.ofp_packet_out()
            msg.in_port = event.port 
            msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT)) 
            msg.data = ether.pack() 
            
            self.connection.send(msg) 

            print(dst_mac) 


    # Comment out the following line and uncomment the one after
    # when starting the exercise.
#    self.act_like_hub(packet, packet_in)
    #self.act_like_switch(packet, packet_in)



def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
