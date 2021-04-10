#!/usr/bin/python3
#
## obdii_logger.py
# 
# This python3 program sends out OBDII request then logs the reply to the sd card.
# For use with PiCAN boards on the Raspberry Pi
# http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-2-p-1475.html
#
# Make sure Python-CAN is installed first http://skpang.co.uk/blog/archives/1220
#
#  24-08-16 SK Pang
#

import can
import time
import datetime
import os
import queue
from threading import Thread

# For documentation of IDs see http://www.rec-bms.com/datasheet/UserManual9R_SMA.pdf
CHARGE_DISCHARGE_LIMITS_ID 		= 0x351
SOC_SOH_ID						= 0x355
BATTERY_VOLT_CURRENT_TEMP_ID	= 0x356
ALARM_WARNING_ID				= 0x35A
MANUFACTURER_ID					= 0x35E
CHEM_HWVERS_CAPACITY_SWVERS_ID	= 0x35F
# Unknown						= 0x370
MIN_MAX_CELL_VOLT_TEMP_ID		= 0x373
# Unknown						= 0x374
# Unknown						= 0x375
# Unknown						= 0x376
# Unknown						= 0x377
# Unknown						= 0x379
# Unknown						= 0x380


ENGINE_RPM          = 0x0C
VEHICLE_SPEED       = 0x0D
MAF_SENSOR          = 0x10
O2_VOLTAGE          = 0x14
THROTTLE            = 0x11

PID_REQUEST         = 0x7DF
PID_REPLY           = 0x7E8

outfile = open('log.txt','w')


print('Bring up CAN0....')

# Bring up can0 interface at 250kbps
os.system("sudo /sbin/ip link set can0 up type can bitrate 250000")

time.sleep(0.1)	
print('Ready')

try:
	bus = can.interface.Bus(channel='can0', bustype='socketcan')
except OSError:
	print('Cannot find PiCAN board.')
	exit()

def can_rx_task():	# Receive thread
	while True:
		message = bus.recv()
		q.put(message)			# Put message into queue
						
						
q = queue.Queue()
rx = Thread(target = can_rx_task)  
rx.start()

charge_voltage_limit = 0
charge_current_limit = 0
discharge_current_limit = 0
discharge_voltage_limit = 0

state_of_charge = 0
state_of_health = 0
state_of_charge_hi_res = 0

battery_voltage = 0
battery_current = 0
battery_temperature = 0

min_cell_voltage = 0
max_cell_voltage = 0
min_temperature = 0
max_temperature = 0

c = ''
count = 0

headers = '| {0:27s} | {1:3s} '.format('Time Stamp', 'cnt')
headers += '| {0:4s} | {1:4s} | {2:3s} | {3:3s} | {4:3s} | {5:3s} | {6:3s} | {7:3s} | {8:3s} | {9:3s} | {10:3s} | {11:3s} | {12:3s} | {13:3s} |'.format('CVL', 'CCL', 'DCL', 'DVL', 'SOC', 'SOH', 'SOC', 'BaV', 'BaC', 'BaT', 'MiV', 'MaV', 'MiT', 'MaT')
print('\r {} '.format(headers))
# Main loop
try:
	while True:
		for i in range(14):
			while(q.empty() == True):	# Wait until there is a message
				pass
			message = q.get()
			ts = datetime.datetime.fromtimestamp(message.timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')

			c = '| {0:27s} | {1:3d} '.format(ts,count)


			if message.arbitration_id == CHARGE_DISCHARGE_LIMITS_ID:
				charge_voltage_limit = 0.1 * int.from_bytes(message.data[0:2], 'little')
				charge_current_limit = 0.1 * int.from_bytes(message.data[2:4], 'little')
				discharge_current_limit = 0.1 * int.from_bytes(message.data[4:6], 'little')
				discharge_voltage_limit = 0.1 * int.from_bytes(message.data[6:8], 'little')

			if message.arbitration_id == SOC_SOH_ID:
				state_of_charge = int.from_bytes(message.data[0:2], 'little')
				state_of_health = int.from_bytes(message.data[2:4], 'little')
				state_of_charge_hi_res = 0.01 * int.from_bytes(message.data[4:6], 'little')
					
			if message.arbitration_id == BATTERY_VOLT_CURRENT_TEMP_ID:
				battery_voltage = 0.01 * int.from_bytes(message.data[0:2], 'little')
				battery_current = 0.1 * int.from_bytes(message.data[2:4], 'little')
				battery_temperature = 0.1 * int.from_bytes(message.data[4:6], 'little')

			if message.arbitration_id == MIN_MAX_CELL_VOLT_TEMP_ID:
				min_cell_voltage = 0.001 * int.from_bytes(message.data[0:2], 'little')
				max_cell_voltage = 0.001 * int.from_bytes(message.data[2:4], 'little')
				min_temperature = int.from_bytes(message.data[4:6], 'little')
				max_temperature = int.from_bytes(message.data[6:8], 'little')

		#c += '{0:.1f},{1:.1f},{2:.1f},{3:.1f},{4:.0f},{5:.0f},{6:.2f},{7:.2f},{8:.1f},{9:.1f},{10:.3f},{11:.3f},{12:.0f},{13:.0f}'.format(charge_voltage_limit, charge_current_limit, discharge_current_limit, discharge_voltage_limit, state_of_charge, state_of_health, state_of_charge_hi_res, battery_voltage, battery_current, battery_temperature, min_cell_voltage, max_cell_voltage, min_temperature, max_temperature)
		c += '| {0:.1f} | {1:.1f} | {2:.1f} | {3:.1f} | {4: >3d} | {5:0>3d} | {6:.2f} | {7:.2f} | {8:.1f} | {9:.1f} | {10:.3f} | {11:.3f} | {12:.0f} | {13:.0f} |'.format(charge_voltage_limit, charge_current_limit, discharge_current_limit, discharge_voltage_limit, state_of_charge, state_of_health, state_of_charge_hi_res, battery_voltage, battery_current, battery_temperature, min_cell_voltage, max_cell_voltage, min_temperature, max_temperature)
		print('\r {} '.format(c))
		#print(c, file=outfile) # Save data to file
		count += 1
			

 
	
except KeyboardInterrupt:
	#Catch keyboard interrupt
	outfile.close()		# Close logger file
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrtupt')	