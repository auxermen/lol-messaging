from lcu_driver import Connector
import tkinter
from tkinter import scrolledtext
import threading
import time

connector = Connector()

selected_option = ''
send_msg_button = False
set_status_msg_button = False
update_option_menu_interval = 3

def send_msg():
    global send_msg_button
    send_msg_button = True
    
def set_status_msg():
    global set_status_msg_button
    set_status_msg_button = True
    
def handle_option_menu_select(item):
    string_var.set(item)
    global selected_option
    selected_option = item

# setup GUI
root = tkinter.Tk()

scrolled_text = scrolledtext.ScrolledText(root)
scrolled_text.pack()

string_var = tkinter.StringVar(root)
string_var.set("Select conversation") # default value
options_menu = tkinter.OptionMenu(root, string_var, "", command=handle_option_menu_select)
options_menu.pack()

tkinter.Button(root, text="Send message", command=send_msg).pack()
tkinter.Button(root, text="Set status message", command=set_status_msg).pack()
    
# fired when LCU API is ready to be used
@connector.ready
async def connect(connection):
    global send_msg_button
    global set_status_msg_button
    url_dict = {}
    
    while True:
        r = await connection.request('get', '/lol-chat/v1/conversations/', data={})
        res = await r.json()
        options_list = []
        url_dict_new = {}
        for i in res:
            if i['gameName']:
                options_list.append(i['gameName'])
                url_dict_new[i['gameName']] = i['id']
            else:
                options_list.append(i['type'])
                url_dict_new[i['type']] = i['id']
            # print(i['gameName'] + ': ' + i['id'])
                
        # update option menu if new recipients are added
        if options_menu and url_dict_new != url_dict:
            url_dict = url_dict_new
            menu = options_menu['menu']
            menu.delete(0, 'end')
            for option in options_list:
                menu.add_command(label=option, command=lambda name=option: handle_option_menu_select(name))
        
        time_end = time.time() + update_option_menu_interval
        while time.time() < time_end:
            if send_msg_button:
                if selected_option in url_dict:
                    await connection.request('post', '/lol-chat/v1/conversations/' + url_dict[selected_option] + '/messages', data={'body': scrolled_text.get('1.0', tkinter.END)})
                send_msg_button = False
            if set_status_msg_button:
                await connection.request('put', '/lol-chat/v1/me', data={'statusMessage': scrolled_text.get('1.0', tkinter.END)})
                set_status_msg_button = False
            time.sleep(0.1)

# fired when League Client is closed (or disconnected from websocket)
@connector.close
async def disconnect(_):
    print('The client has been closed!')
    
# starts the connector
threading.Thread(target=connector.start, args=()).start()

# starts the UI loop
root.mainloop()
