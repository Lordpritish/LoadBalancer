from tkinter import *
import subprocess

root = Tk()

root.title("Welcome to out load balancer")

root.geometry('350x200')

lb_algo_list = ['random', 'round robin', 'dynamic']
lb_algo_chosen = StringVar(root)
lb_algo_menu = OptionMenu(root, lb_algo_chosen, *lb_algo_list)
lb_algo_menu.pack()


def run_lb_simulation():
    run_button['state'] = DISABLED
    result = subprocess.run(['ping', 'google.com', '-c', '3'], stdout=subprocess.PIPE)
    print(result.stdout.decode('utf-8').split('\n')[-2])
    run_button['state'] = NORMAL

run_button = Button(root, text="run", command=run_lb_simulation)
run_button.pack()

root.mainloop()