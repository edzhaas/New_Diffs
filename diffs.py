import os
from tkinter import *
from tkinter import ttk
import threading
import shutil
import subprocess
import datetime
import math
from skimage import color
import xml.etree.ElementTree as ET


### Software take a diffs file and outputs a new coloursys file with modified chips

def lab_to_hex_rgb(lab):
    rgb_color = color.lab2rgb([[lab]], illuminant='D65', observer='2')
    r = round(rgb_color[0,0,0] * 255)
    g = round(rgb_color[0,0,1] * 255)
    b = round(rgb_color[0,0,2] * 255)

    # Format up as hex string, i.e. #ECF0EF
    res = f'#{r:02X}{g:02X}{b:02X}'
    print(res)
    return res

def get_delta_e(lab1, lab2) -> float:
    diff_1 = lab1[0] - lab2[0]
    diff_2 = lab1[1] - lab2[1]
    diff_3 = lab1[2] - lab2[2]
    return math.sqrt((diff_1*diff_1) + (diff_2*diff_2) + (diff_3*diff_3))

root = Tk()
root.title("Diffs =)")
root.geometry("300x300")

l_entry  = Entry(root,width=20)
l_entry.grid(row=0,column=0)
a_entry  = Entry(root,width=20)
a_entry.grid(row=1,column=0)
b_entry  = Entry(root,width=20)
b_entry.grid(row=2,column=0)

def update_col_display(event=None):
    col_display.config(bg=(lab_to_hex_rgb((float(l_entry.get()),float(a_entry.get()),float(b_entry.get())))))

update_button = Button(root,text="Update", command=update_col_display)
update_button.grid(row=2,column=1)

col_display = Label(root,width=20,bg="white",height=4)
col_display.grid(row=4,column=0)

tree = ET.parse('colourway_file.cway')
root_tree = tree.getroot()
count = [["i",0],["j",0],["k",0],["l",0],["m",0],["n",0],["o",0]]
for i in root_tree:
    print("i",i.tag,i.text)
    count[0][1] += 1
    for j in i:
        print("j","\t",j.tag,j.text)
        count[1][1] += 1
        for k in j:
            print("k","\t\t",k.tag,k.text)
            count[2][1] += 1
            for l in k:
                print("l","\t\t\t",l.tag,l.text)
                count[3][1] += 1
                for m in l:
                    print("m","\t\t\t\t",m.tag,m.text)
                    count[4][1] += 1
                    for n in m:
                        print("n","\t\t\t\t\t",n.tag,n.text)
                        count[5][1] += 1
                        for o in n:
                            print("o","\t\t\t\t\t\t",o.tag,o.text)
                            count[6][1] += 1
print(count)
root.bind("<Return>",update_col_display)
root.bind("<Escape>",exit)
root.mainloop()