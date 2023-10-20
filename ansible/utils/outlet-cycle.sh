#!/usr/bin/expect -f

# Parse command line arguments
set timeout 10
set ip [lindex $argv 0]
set user [lindex $argv 1]
set pass [lindex $argv 2]

# Start the telnet session
spawn telnet $ip

# Expect the "User>" prompt and send the username
expect "User>"
send "$user\r"

# Expect the "Password>" prompt and send the password
expect "Password>"
send "$pass\r"

# Expect the "iBoot>" prompt and send the command
expect "iBoot>"
send "set outlet cycle\r"

# Close the telnet session
expect eof
