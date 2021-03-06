#!/usr/bin/python3
#
## obdii_logger.py
# 
# This python3 program translates and formats CAN messages into readable data
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
RATED_CAPACITY					= 0x379
# Unknown						= 0x380

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

rated_capacity = 0

remaining_capacity = 0

c = ''
count = 0

headers = '| {0:27s} | {1:3s} '.format('Time Stamp', 'cnt')
headers += '| {0:4s} | {1:5s} | {2:5s} | {3:4s} | {4:3s} | {5:3s} | {6:6s} | {7:5s} | {8:5s} | {9:4s} | {10:5s} | {11:5s} | {12:3s} | {13:3s} | {14:4s} | {15:4s} |'.format(
	'CVL', 'CCL', 'DCL', 'DVL', 'SOC', 'SOH', 'SOC', 'BaV', 'BaC', 'BaT', 'MiV', 'MaV', 'MiT', 'MaT', ' CAP', 'RCAP')
print('\r {} '.format(headers))
# Main loop

cdl_updated = False
soc_soh_updated = False
bvct_updated = False
min_max_cell_updated = False
rated_capacity_updated = False
chem_hwvers_cap_updated = False

try:
	while True:
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
			cdl_updated = True

		if message.arbitration_id == SOC_SOH_ID:
			state_of_charge = int.from_bytes(message.data[0:2], 'little')
			state_of_health = int.from_bytes(message.data[2:4], 'little')
			state_of_charge_hi_res = 0.01 * int.from_bytes(message.data[4:6], 'little')
			soc_soh_updated = True
				
		if message.arbitration_id == BATTERY_VOLT_CURRENT_TEMP_ID:
			battery_voltage = 0.01 * int.from_bytes(message.data[0:2], 'little')
			battery_current = 0.1 * int.from_bytes(message.data[2:4], 'little')
			battery_temperature = 0.1 * int.from_bytes(message.data[4:6], 'little')
			bvct_updated = True

		if message.arbitration_id == MIN_MAX_CELL_VOLT_TEMP_ID:
			min_cell_voltage = 0.001 * int.from_bytes(message.data[0:2], 'little')
			max_cell_voltage = 0.001 * int.from_bytes(message.data[2:4], 'little')
			min_temperature = int.from_bytes(message.data[4:6], 'little')
			max_temperature = int.from_bytes(message.data[6:8], 'little')
			min_max_cell_updated = True

		if message.arbitration_id == RATED_CAPACITY:
			rated_capacity = int.from_bytes(message.data[0:2], 'little')
			if rated_capacity > 250:
				rated_capacity += 1
			rated_capacity_updated = True
		
		if message.arbitration_id == CHEM_HWVERS_CAPACITY_SWVERS_ID:
			remaining_capacity = int.from_bytes(message.data[4:6], 'little')
			chem_hwvers_cap_updated = True

		if cdl_updated and soc_soh_updated and bvct_updated and min_max_cell_updated and rated_capacity_updated:
			c += '| {0: >4.1f} | {1: >5.1f} | {2: >5.1f} | {3: >4.1f} | {4: >3d} | {5: >3d} | {6: >6.2f} | {7: >5.2f} | {8: >5.1f} | {9: >4.1f} | {10: >5.3f} | {11: >5.3f} | {12: >3.0f} | {13: >3.0f} | {14: >4d} | {15: >4d} |'.format(
				charge_voltage_limit, charge_current_limit, discharge_current_limit, discharge_voltage_limit, state_of_charge, state_of_health, state_of_charge_hi_res, battery_voltage, battery_current, battery_temperature, min_cell_voltage, max_cell_voltage, min_temperature, max_temperature, rated_capacity, remaining_capacity)
			print('\r {} '.format(c))
			print('\r {} '.format(headers), end="\r")
			count += 1
			cdl_updated = False
			soc_soh_updated = False
			bvct_updated = False
			min_max_cell_updated = False
			rated_capacity_updated = False
			chem_hwvers_cap_updated = False


 
	
except KeyboardInterrupt:
	#Catch keyboard interrupt
	outfile.close()		# Close logger file
	os.system("sudo /sbin/ip link set can0 down")
	print('\n\rKeyboard interrtupt')	
