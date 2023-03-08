import sys
import math
import collections
import csv
import time
import json
import requests
import certifi
import datetime, dateutil.parser
import statistics
from decimal import Decimal
from datetime import datetime
from scipy.stats import skew

def mean(dict_of_values):
    return sum(dict_of_values.values()) / max(len(dict_of_values), 1)

def variance(dict_of_values, mean_of_values): 
    n = len(dict_of_values)
    deviations = [(x - mean_of_values) ** 2 for x in dict_of_values.values()]
    variance = sum(deviations) / max(n, 1)
    return variance

def sdev(dict_of_values, mean_of_values): 
    var = variance(dict_of_values, mean_of_values)
    std_dev = math.sqrt(var)
    return std_dev
    
# open csv
addrs= "addresses.csv"               
result = open("result.csv", "w+")   
writer = csv.writer(result, lineterminator = '\n') 
writer.writerow(['address', 'balance', 'N_maxpayment', 'investment_in', 'payment_out', 'mean_v1', 'sdev_v1', 'skew_v1', 'mean_v2', 'sdev_v2', 'skew_v2', 'known_rate', 'paid_rate', 'paid_one',])
addr_list = [] # lista che mantiene gli indirizzi degli smart contract

with open(addrs, 'r', encoding = 'utf-8-sig') as f: 
    reader = csv.reader(f, delimiter = ',', quotechar = '|')  
    for row in reader:
        addr = row[0] 
        addr_list.append(addr)

for addr in addr_list: 
    print("Retrieving transactions of contract ", addr)
    sys.stdout.flush() 

    count_in, count_out = 0, 0   
    eth_in, eth_out = 0, 0       
    dict_kr_in = {}
    dict_kr_out = {}
    dict_addr_tx_out = {}        
    dict_addr_tx_in = {}         
    dict_addr_eth_in = {}        
    dict_addr_eth_out = {}       
    
    print("Get normal transaction of contract ", addr)
    normal_tx_url = "https://api.etherscan.io/api?module=account&action=txlist&address=" + addr + \
                   "&startblock=0&endblock=99999999&page=1&offset=10000&sort=asc&apikey=insert_your_key"
    response_normal = requests.get(normal_tx_url, verify = certifi.where()) 
    address_content_normal = response_normal.json() 
    result_normal = address_content_normal.get('result') 

    for t in result_normal: 
        if (t['isError'] == '0'): 
            eth_val = int(t['value'])
            if t['from'] not in dict_kr_in:
                dict_kr_in[t['from']] = int(t['timeStamp']) 
            if (eth_val > 0): 
                if t['from'] in dict_addr_tx_in: 
                    dict_addr_tx_in[t['from']] += 1 
                    dict_addr_eth_in[t['from']] += round(Decimal(eth_val)/Decimal('1000000000000000000'), 6) 
                else:
                    dict_addr_tx_in[t['from']] = 1 
                    dict_addr_eth_in[t['from']] = round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                eth_in += eth_val 
                count_in += 1

    print("Get internal transaction of contract ", addr)
    internal_tx_url = "https://api.etherscan.io/api?module=account&action=txlistinternal&address=" + addr + \
                       "&startblock=0&endblock=99999999&page=1&offset=10000&sort=asc&apikey=insert_your_key"
    response_internal = requests.get(internal_tx_url, verify = certifi.where())
    address_content_internal = response_internal.json()
    result_internal = address_content_internal.get("result")

    for t in result_internal:
        if (t['isError'] != '0'): continue 
        eth_val = int(t['value'])
        if (t['from'].lower() == addr.lower()):                         
            if (eth_val > 0):
                if t['to'] in dict_addr_tx_out:
                    dict_addr_tx_out[t['to']] += 1
                    dict_addr_eth_out[t['to']] += round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                else:
                    dict_addr_tx_out[t['to']] = 1 
                    dict_addr_eth_out[t['to']] = round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                    dict_kr_out[t['to']] = int(t['timeStamp'])
                eth_out += eth_val
                count_out +=1
        else:  
            if t['from'] not in dict_kr_in:
                dict_kr_in[t['from']] = int(t['timeStamp'])
            if (eth_val > 0): 
                if t['from'] in dict_addr_tx_in: 
                    dict_addr_tx_in[t['from']] += 1 
                    dict_addr_eth_in[t['from']] += round(Decimal(eth_val)/Decimal('1000000000000000000'), 6) 
                else:
                    dict_addr_tx_in[t['from']] = 1 
                    dict_addr_eth_in[t['from']] = round(Decimal(eth_val)/Decimal('1000000000000000000'), 6)
                eth_in += eth_val 
                count_in += 1
    
    # statistics
    balance = round(Decimal(eth_in - eth_out)/Decimal('1000000000000000000'),6)                     
    
    if not list(dict_addr_tx_out.values()):
        N_maxpayment = 0
    else:
        N_maxpayment = max(dict_addr_tx_out.values())   
    
    paying_addresses = len(dict_addr_tx_in)          
    paid_addresses = len(dict_addr_tx_out)           
    
    v1 = {key: dict_addr_tx_out[key] - dict_addr_tx_in.get(key, 0) for key in dict_addr_tx_out} 
    for k in dict_addr_tx_in:
        if k not in dict_addr_tx_out:
	        v1[k] = - dict_addr_tx_in[k] 
    
    v2 = {key: dict_addr_eth_out[key] - dict_addr_eth_in.get(key, 0) for key in dict_addr_eth_out}
    for k in dict_addr_eth_in:
        if k not in dict_addr_eth_out:
	        v2[k] = - dict_addr_eth_in[k]
    
    mean_v1 = round(Decimal(mean(v1)), 6)   
    sdev_v1 = round(sdev(v1, mean_v1), 6)   
    l_v1 = list(v1.values())
    list_v1 = [float(i) for i in l_v1]
    if not list_v1:
        skew_v1 = 0
    else:
        skew_v1 = round(skew(list_v1, bias=False), 6)
    
    mean_v2 = round(Decimal(mean(v2)), 6)   
    sdev_v2 = round(sdev(v2, mean_v2), 6)   
    l_v2 = list(v2.values())
    list_v2 = [float(i) for i in l_v2]
    if not list_v2:
        skew_v2 = 0
    else:
        skew_v2 = round(skew(list_v2, bias=False), 6)
    
    paid_rate = round(Decimal(count_out)/Decimal(max(count_in, 1)), 4) 

    
    count_paid_investors = 0 
    for k in dict_addr_tx_out:
        if k in dict_addr_tx_in:
            count_paid_investors += 1 

    count_kr = 0
    for k in dict_kr_out:
        if k in dict_kr_in:
            if dict_kr_in[k] <= dict_kr_out[k]:
                count_kr+=1

    paid_one = round(Decimal(count_paid_investors)/Decimal(max(paying_addresses, 1)), 4)   
    known_rate = round(Decimal(count_kr)/Decimal(max(paid_addresses, 1)), 4)
    writer.writerow([addr, str(balance), str(N_maxpayment), str(count_in), str(count_out), str(mean_v1), str(sdev_v1), str(skew_v1), str(mean_v2), str(sdev_v2), str(skew_v2), str(known_rate), str(paid_rate), str(paid_one)]) 
    time.sleep(0.2)

result.close()
print("end")
