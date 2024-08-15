from flask import Flask, request, send_file
import subprocess
import os

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_exe():
    data = request.get_json()
    device = data.get('device')
    idDevice = data.get('idDevice')

    if not idDevice or not device:
        return 'Missing device or idDevice', 400

    script_content = f"""
import requests
import hashlib
import getpass
import time
from datetime import datetime, timedelta
import serial
import json
import threading
from localStoragePy import localStoragePy
import os
from os import system

URL = "http://moneysenddb.com/api/ticket"
device = "{device}"
device_id = "{idDevice}"
accumulated_quantity = 0
accumulated_value = 0
quantity_in_queue = 0
panel_messages = {{
    'show_message_panel': True,
    'internet': '',
    'info': 'Esperando transacción',
    'status_device': '',
    'quantity_in_queue': 0
}}
#valid_tickets = [100000, 50000, 20000, 10000, 5000, 2000]
valid_tickets = [100, 50, 20, 10, 5, 1]
token = None
versionapp = '1.1'

def decrypt_phrase(p_phrase):
    try:    
        resp = ''
        for x in p_phrase:
            resp += chr(ord(x) - 10)  
    except:
        resp = ''
    return resp

def encrypt_phrase(p_phrase):
    try:
        resp = ''
        for x in p_phrase:
            resp += chr(ord(x) + 10)
    except:
        resp = ''
    return resp

def sync_offline():
    global device, quantity_in_queue, panel_messages, versionapp
    start1 = datetime.now()
    start2 = datetime.now()
    while True:
        try:
            current = datetime.now()
            if panel_messages['show_message_panel'] and abs(current.second - start1.second) >= 1:
                system('cls')
                print('Procesando...')
                print('result: '+panel_messages['quantity_in_queue'])
                quantity_in_queue = str(panel_messages['quantity_in_queue']) if panel_messages['quantity_in_queue'] > 0 else ''
                system('cls')
                print (current.strftime('%I:%M:%S %p') + ' | Versión App: ' + versionapp)
                print ('Dispositivo: ' + device)
                print ('Estado Internet: ' + panel_messages['internet'])
                print ('Estado dispositivo: ' + panel_messages['status_device'])               
                print ('Transacciones en cola: '+ quantity_in_queue)
                print ('Información: ' + panel_messages['info'])
                start1 = datetime.now()
            if abs(current.second - start2.second) >= 15:
                start2 = datetime.now()
                try:
                    panel_messages['internet'] = 'Conectado'
                except:
                    panel_messages['internet'] = 'Sin conexión'
                valid_localstorage()
                datetoday = current.strftime('%Y-%m-%d')
                try:
                    d = open('localdate.dat', 'r+')
                except IOError:
                    d.close()
                    d = open('localdate.dat', 'r+')

                ddata = d.read()
                if ddata != '':
                    ddata = decrypt_phrase(ddata)
                if ddata == datetoday:
                    while True:
                        try:
                            c = open('localcurrency.dat', 'r+')
                        except IOError:
                            c.close()
                            c = open('localcurrency.dat', 'r+')

                        localcurrency = c.read()
                        if localcurrency != '':
                            localcurrency = decrypt_phrase(localcurrency)
                        c.close()

                        try:
                            f = open('localstorage.dat', 'r+')
                        except IOError:
                            f.close()
                            f = open('localstorage.dat', 'r+')

                        fdata = f.read()
                        if (fdata) != '':
                            fdata = decrypt_phrase(fdata)
                            lista = fdata.split(',')
                            ticketvalue = lista[0]
                            if int(ticketvalue) not in valid_tickets:
                                ticketvalue = 0

                            headers = {{
                                'Content-Type': 'application/json',
                            }}

                            data = {{
                                'value': ticketvalue,
                                'currency': localcurrency,
                                'device_id': device_id
                            }}
                            try:
                                if ticketvalue > 0:
                                    response = requests.post(URL, headers=headers, json=data)
                                    if (response.status_code == 200):
                                        f.close()
                                        f = open('localstorage.dat', 'w')
                                        lista.pop(0)
                                        panel_messages['quantity_in_queue'] -= 1
                                        if len(lista) > 0:
                                            lista = ','.join(lista)
                                            fdata = encrypt_phrase(lista)
                                            f.write(fdata)
                                            f.close()
                                        else:
                                            f.close()
                                            break
                                    else:
                                        lista.pop(0)
                                else:
                                    lista.pop(0)

                            except:
                                panel_messages['internet'] = 'Sin conexión'
                                break
                        else:
                            f.close()
                            break
                d.close()
        except:
            panel_messages['info'] = 'Error sincronizando transacciones...'

def valid_localstorage():
    global accumulated_quantity, accumulated_value
    while True:
        try:
            if not os.path.exists('localcurrency.dat'):
                c = open('localcurrency.dat', 'x')
                c.close()

            if not os.path.exists('localdate.dat'):
                d = open('localdate.dat', 'x')
                d.close()

            try:
                d = open('localdate.dat', 'r+')
            except IOError:
                d.close()
                d = open('localdate.dat', 'r+')

            now = datetime.now()
            datetoday = now.date()
            datetoday = datetoday.strftime('%Y-%m-%d')
            ddata = d.read()
            ddata = decrypt_phrase(ddata)
            if ddata.find(datetoday) == -1 or len(ddata) > 10:
                d.close()
                try:
                    d = open('localdate.dat', 'w')
                except IOError:
                    d.close
                    d = open('localdate.dat', 'w')

                try:
                    f = open('localstorage.dat', 'w')
                except IOError:
                    f.close
                    f = open('localstorage.dat', 'w')
                f.close()

                try:
                    c = open('localcurrency.dat', 'w')
                except IOError:
                    c.close
                    c = open('localcurrency.dat', 'w')                
                c.close()

                ddata = encrypt_phrase(datetoday)
                d.write(ddata)
                accumulated_quantity = 0
                accumulated_value = 0
                panel_messages['quantity_in_queue'] = 0
            else:
                try:
                    f = open('localstorage.dat', 'r+')
                except IOError:
                    f.close
                    f = open('localstorage.dat', 'r+')
                panel_messages['quantity_in_queue'] = 0
                fdata = f.read()                
                if (fdata) != '':
                    fdata = decrypt_phrase(fdata)
                    lista = fdata.split(',')
                    for k in lista:
                        panel_messages['quantity_in_queue'] += 1
                f.close()

            d.close()
            break
        except:
            panel_messages['info'] = 'Error creando el localstorage'
    return True

valid_localstorage()
threading_sync = threading.Thread(target=sync_offline)
threading_sync.start()
conexion = False
while True:
    while not conexion:
        try:
            PuertoSerie = serial.Serial('com3',115200,8,'N',1)
            conexion = True
            panel_messages['status_device'] = 'Conectado'
            panel_messages['info'] = 'Esperando transacción...'
        except:
            panel_messages['status_device'] = 'Sin conexión'
    try:
        dev_accumulated_value = 0
        dev_accumulated_qty = 0
        currency = ''
        sw = True
        while sw:
            linea = PuertoSerie.readline()
            string = linea.decode()
            if string.find('CURRENCY:') >= 0:
                currency = string[9:12]
            if string.find('TOTAL AMOUNT:') >= 0:
                dev_accumulated_value = string[13:30]
            if string.find('TOTAL PIECES:') >= 0:
                dev_accumulated_qty = string[13:30]
            if string.find('END') >= 0:
                sw = False

        dev_accumulated_qty = int(dev_accumulated_qty.replace(',', ''))
        dev_accumulated_value = int(dev_accumulated_value.replace(',', ''))
        try:
            c = open('localcurrency.dat', 'r+')
        except IOError:
            c.close()
            c = open('localcurrency.dat', 'r+')

        localcurrency = c.read()
        c.close()
        if localcurrency == '':
            localcurrency = currency

        if localcurrency != currency:
            accumulated_quantity = 0
            accumulated_value = 0
            panel_messages['quantity_in_queue'] = 0

            try:
                f = open('localstorage.dat', 'w')
            except IOError:
                f.close
                f = open('localstorage.dat', 'w')

            fdata = ''
            f.write(fdata)
            f.close()

            try:
                c = open('localcurrency.dat', 'w')
            except IOError:
                c.close()
                c = open('localcurrency.dat', 'w')

            fdata = encrypt_phrase(currency)
            c.write(fdata)
            c.close()

        if dev_accumulated_value - accumulated_value > 0 and (dev_accumulated_value - accumulated_value) in valid_tickets:
            ticketvalue = dev_accumulated_value - accumulated_value
        else:
            ticketvalue = 0

        accumulated_quantity = dev_accumulated_qty
        accumulated_value = dev_accumulated_value

        try:
            response = requests.post(URL, headers=headers, json=data)
            if response.status_code == 200:
                panel_messages['info'] = 'Transacción enviada exitosamente'
            else:
                try:
                    f = open('localstorage.dat', 'r+')
                except IOError:
                    f.close()
                    f = open('localstorage.dat', 'r+')
                fdata = f.read()
                if (fdata) != '':
                    fdata = decrypt_phrase(fdata)
                    fdata += ','+str(ticketvalue)
                else:
                    fdata = str(ticketvalue)
                fdata = encrypt_phrase(fdata)
                f.write(fdata)
                panel_messages['info'] = 'Error enviando transacción'
                panel_messages['quantity_in_queue'] += 1
                f.close()
        except:
            try:
                f = open('localstorage.dat', 'r+')
            except IOError:
                f.close()
                f = open('localstorage.dat', 'r+')
            fdata = f.read()
            if (fdata) != '':
                fdata = decrypt_phrase(fdata)
                fdata += ','+str(ticketvalue)
            else:
                fdata = str(ticketvalue)
            fdata = encrypt_phrase(fdata)
            f.write(fdata)
            panel_messages['quantity_in_queue'] += 1
            panel_messages['info'] = 'Error enviando transacción'
            panel_messages['internet'] = 'Sin conexión'
            f.close()
    except:
        panel_messages['info'] = 'Error procesando transacción'
        panel_messages['status_device'] = 'Sin conexión'
        conexion = False
    panel_messages['info'] = 'Esperando transacción...'
    time.sleep(1)
"""

    script_path = "script.py"
    dist_path = "dist/script.exe"

    with open(script_path, "w") as file:
        file.write(script_content)

    try:
        result = subprocess.run(["pyinstaller", "--onefile", script_path], check=True, capture_output=True, text=True)
        print("PyInstaller stdout:")
        print(result.stdout)
        print("PyInstaller stderr:")
        print(result.stderr)

        if os.path.exists(dist_path):
            return send_file(dist_path, as_attachment=True)
        else:
            # List the contents of the dist directory for debugging purposes
            if os.path.exists("dist"):
                dist_files = os.listdir("dist")
                print("Contents of dist directory:", dist_files)
            return "Executable not found after pyinstaller run.", 500
    except subprocess.CalledProcessError as e:
        return f"PyInstaller error: {e.stderr}", 500
    finally:
        if os.path.exists(script_path):
            os.remove(script_path)
        if os.path.exists("script.spec"):
            os.remove("script.spec")
        # Clean up the dist directory only if the executable was not found
        if os.path.exists(dist_path):
            os.remove(dist_path)
        else:
            if os.path.exists("dist"):
                for file in os.listdir("dist"):
                    os.remove(os.path.join("dist", file))
                os.rmdir("dist")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
