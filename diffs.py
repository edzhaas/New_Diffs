import os
import tkinter as tk
from tkinter import ttk
import threading
import shutil
import subprocess
import datetime
import math
from skimage import color
BACKGROUND = "white"
FOREGROUND = "black"

class AVAColourway:
    def __init__(self, *colours, name="", locked="false", ):
        self.name = name
        self.locked = locked
        self.colours = []
        if colours:
            self.colours = colours[0]
    
    def add_AVAColour(self, col):
        self.colours.append(col)
    
    def get_colours(self):
        return self.colours
    
    def print(self):
        print("Colourway:", self.name, "Locked:", self.locked)
        for each in self.colours:
            each.print()

class AVAColour:
    def __init__(self, name="", rgb=None, xyz="", ref="", lab=None, uuid=""):
        self.name = name
        self.uuid = uuid
        self.values = {}
        
        if xyz:
            self.values['xyz'] = xyz
        if ref:
            self.values['ref'] = ref
        else:
            self.values['ref'] = ""
        if rgb:
            self.values['rgb'] = rgb
            small_rgb = []
            for i in range(3):
                small_rgb.append(rgb[i]/65536)
            convertedtolab = color.rgb2lab(small_rgb)
            convertedtoxyz = color.rgb2xyz(small_rgb)
            newxyz = []
            newlab = []
            for each in convertedtolab:
                newlab.append(float(each))
            for i in range(3):
                newxyz.append(float(convertedtoxyz[i]))
            self.values['lab'] = newlab
            self.values['xyz'] = newxyz
        elif lab:
            raw_rgb = color.lab2rgb(lab)
            new_rgb = []
            raw_xyz = color.lab2xyz(lab)
            new_xyz = []
            for i in range(3):
                new_rgb.append(int(raw_rgb[i]*65536))
                new_xyz.append(float(raw_xyz[i]))
            self.values['rgb'] = new_rgb
            self.values['xyz'] = new_xyz
            self.values['lab'] = lab

    def print(self):
        print("Colour Name:", self.name, "LAB:",self.values['lab'],"RGB:", self.values['rgb'])
        
    def set(self,key,value=0):
        print("Setting colour", self.name, "::" + key + ":: =", value)
        if key == 'lab': # value is a tuple (L,A,B)
            raw_rgb = color.lab2rgb(value)
            new_rgb = []
            raw_xyz = color.lab2xyz(value)
            new_xyz = []
            for i in range(3):
                new_rgb.append(int(raw_rgb[i]*65536))
                new_xyz.append(float(raw_xyz[i]))
            self.values['rgb'] = new_rgb
            self.values['xyz'] = new_xyz
            self.values['lab'] = value
        if key == 'rgb':
            self.values['rgb'] = value
            small_rgb = []
            for i in range(3):
                small_rgb.append(value[i]/65536)
            convertedtolab = color.rgb2lab(small_rgb)
            convertedtoxyz = color.rgb2xyz(small_rgb)
            newxyz = []
            newlab = []
            for each in convertedtolab:
                newlab.append(float(each))
            for i in range(3):
                newxyz.append(float(convertedtoxyz[i]))
            self.values['lab'] = newlab
            self.values['xyz'] = newxyz
        if key == 'name':
            self.name = value
        if key == 'uuid':
            self.uuid = value

class AVAXML:
    def extract_value(data, chosen_value="name", start="<string>",end="</string>"):
        if chosen_value in data:
            temp = data.split(chosen_value+"</key>"+start)
            temp2 = temp[1].split(end)
            if temp2[0]:
                return temp2[0]
            else:
                return ""

    def get_data_between(line, key, end):
        if key in line and end in line:
            temp = line.split(key)
            temp2 = temp[1].split(end)
            return temp2[0]

    def get_colourdata_from_line(line):
        name = line.split("rgb:")[0] # gets name
        rgb = AVAXML.get_data_between(line,"rgb:", "xyz:")
        if "ref" in line:
            xyz = AVAXML.get_data_between(line,"xyz:","ref:")
            ref = AVAXML.get_data_between(line,"ref:","cfu")
        else:
            xyz = AVAXML.get_data_between(line,"xyz:","cfu")
            ref = ""
        return (name, rgb, xyz, ref)

    def extract_colourways_from_xml(filename):
        colourways = []
        with open(filename, 'r') as file:
            header = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>AVA_Colourway_Info</key><string>2.0</string><key>colourways</key><array>'
            footer = '</array><key>docInfo</key><dict><key>doc-UUID</key><string>432E04AE-2159-4EFF-BB38-B790F53B6FCF</string></dict></dict></plist>'
            raw_file = file.read().replace("\n", "").replace("\t","").replace(header,"").replace(footer,"") #file with removed header + footer
            stripped_colourways = raw_file.split("<dict><key>layers</key><array>")
            for colway in stripped_colourways:
                if colway:
                    cway_name = AVAXML.extract_value(colway,"name","<string>","</string>")
                    cway_locked = AVAXML.extract_value(colway,"locked","<","/>")
                    colours = []
                    test = colway.split("<dict><key>colour</key><string>")
                    for each in test:
                        if each:
                            coldata = AVAXML.get_colourdata_from_line(each)
                            cname = coldata[0]
                            cuuid = AVAXML.extract_value(each,"uuid","<string>","</string>")
                            splitrgb = coldata[1].split(",")
                            splitxyz = coldata[2].split(",")
                            if len(coldata[3])>0:
                                splitref = coldata[3].split(",")
                            else:
                                splitref = ""
                            temprgb = []
                            tempxyz = []
                            tempref = []
                            for i in range(3):
                                temprgb.append(int(splitrgb[i]))
                                tempxyz.append(splitxyz[i])
                            for i in range(len(splitref)):
                                tempref.append(splitref[i])
                            if splitref == "":
                                tempref = ""
                            new = AVAColour(name=cname,rgb=temprgb,uuid=cuuid, xyz=tempxyz, ref=tempref)
                            colours.append(new)
                    new = AVAColourway(colours, name=cway_name,locked=cway_locked)
                    colourways.append(new)
            return colourways

    def create_AVA_colourway_file(*colourways, name):
        header = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>AVA_Colourway_Info</key><string>2.0</string><key>colourways</key><array>'
        footer = '</array><key>docInfo</key><dict><key>doc-UUID</key><string>432E04AE-2159-4EFF-BB38-B790F53B6FCF</string></dict></dict></plist>'
        current_text = header
        cways = colourways[0]
        for each in cways:
            current_text += AVAXML.format_xml_colourway_string(each)
        current_text += footer
        with open(name, "w") as text_file:
            text_file.write(current_text)

    def format_xml_colourway_string(colway):
        format = "<dict><key>layers</key><array>\n"
        for each in colway.get_colours():
            if each.values['ref'] == "":
                ref = ""
            else:
                ref = ""
                for nums in each.values['ref']:
                    ref += nums + ','
            new = "<dict><key>colour</key><string>" + each.name +  \
            "\trgb:" + str(each.values['rgb'][0]) + "," + str(each.values['rgb'][1]) + "," + str(each.values['rgb'][2]) + \
            "\txyz:" + str(each.values['xyz'][0]) + "," + str(each.values['xyz'][1]) + "," + str(each.values['xyz'][2]) + \
            "\tref:" + ref + \
            "\tcfu:1</string><key>uuid</key><string>" + \
            each.uuid + "</string></dict>\n"
            format += new
        format += "</array><key>locked</key><" + colway.locked + "/><key>name</key><string>" + colway.name + "</string></dict>\n"
        return format

class AVADiffs:
    def load_diffs(filename):  # Returns a tuple containing master and sample colours ((MASTER1,MASTER2,....),(SAMPLE1,SAMPLE2,.....))
        cols = []
        with open(filename, 'r') as file:
            raw_read = file.read().replace("\t",",")
            lines = raw_read.split("\n")
            remove_header = lines[2:]
            remove_footer = remove_header[:-5]
            for line in remove_footer:
                cells = line.split(",")
                new_sample = AVAColour(name=cells[0],lab=(float(cells[1]),float(cells[2]),float(cells[3])))
                new_master = AVAColour(name=cells[4],lab=(float(cells[5]),float(cells[6]),float(cells[7])))
                cols.append(new_sample)
                cols.append(new_master)
        return cols
                
def lab_to_hex_rgb(lab):
    rgb_color = color.lab2rgb([[lab]], illuminant='D65', observer='2')
    r = round(rgb_color[0,0,0] * 255)
    g = round(rgb_color[0,0,1] * 255)
    b = round(rgb_color[0,0,2] * 255)

    # Format up as hex string, i.e. #ECF0EF
    res = f'#{r:02X}{g:02X}{b:02X}'
    return res

def get_delta_e(lab1, lab2) -> float:
    diff_1 = lab1[0] - lab2[0]
    diff_2 = lab1[1] - lab2[1]
    diff_3 = lab1[2] - lab2[2]
    return math.sqrt((diff_1*diff_1) + (diff_2*diff_2) + (diff_3*diff_3))

class Application(tk.Tk):
    def __init__(self,*args,**kwargs):
        tk.Tk.__init__(self,*args,**kwargs)
        container = tk.Frame(self)
        m = self.maxsize()
        self.geometry('800x200')
        self.attributes("-fullscreen", False)
        container.pack(side="top",fill="both",expand=True)
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)    
        self.frames = {}
        self.colourways = []
        for each in (MainScreen, ColourScreen):
            frame = each(container, self)
            self.frames[each] = frame
            frame.grid(row=0,column=0,sticky="nsew")
        self.show_frame(MainScreen)
        self.mainloop()
    
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.tkraise()
    
    def load_colourway_pressed(self):
        string = self.frames[MainScreen].load_entry.get()
        if string == "":
            return
        else:
            self.colourways = AVAXML.extract_colourways_from_xml(string)
        self.show_frame(ColourScreen)
        self.frames[ColourScreen].display_colourways(self.colourways)
    
    def save_colourway_pressed(self):
        string = self.frames[MainScreen].save_entry.get()
        if string == "":
            return
        else:
            AVAXML.create_AVA_colourway_file(self.colourways,name=string)

    def load_diffs_pressed(self):
        string = self.frames[ColourScreen].diff_entry.get()
        if string == "":
            return
        else:
            ColourScreen.display_diffs(self.frames[ColourScreen],AVADiffs.load_diffs(string))

    def add_multiple_diffs_pressed(self):
        if len(self.frames[ColourScreen].diffs) < 1:
            print("no diffs loaded to apply")
            return
        selection = self.frames[ColourScreen].selected_cway.get()
        index = int(selection.split(".")[0])
        print(index)
        num_of_new_colways = 4
        if self.frames[ColourScreen].diff_num_added_entry.get():
            num_of_new_colways = int(self.frames[ColourScreen].diff_num_added_entry.get())
        for j in range(num_of_new_colways):
            multiplier = 1/(j+1)
            print(multiplier)
            newcolourway = AVAColourway()
            for i in range(len(self.colourways[index-1].get_colours())):
                original = self.colourways[index-1].get_colours()[i]
                orig_l = float(original.values['lab'][0])
                orig_a = float(original.values['lab'][1])
                orig_b = float(original.values['lab'][2])
                
                diffs = self.frames[ColourScreen].diffs[i]
                diff_l = diffs[0].cget('text') * multiplier
                diff_a = diffs[1].cget('text') * multiplier
                diff_b = diffs[2].cget('text') * multiplier
                

                
                newcol = [orig_l+diff_l,orig_a+diff_a,orig_b+diff_b]
                if newcol[0] > 100:
                    newcol[0] = 100
                if newcol[0] < 0:
                    newcol[0] = 0.00
                if newcol[1] > 127:
                    newcol[1] = 127
                if newcol[1] < -128:
                    newcol[1] = -128
                if newcol[2] > 127:
                    newcol[2] = 127
                if newcol[2] < -128:
                    newcol[2] = -128
                    
                newcolour = AVAColour(lab = newcol)
                newcolourway.add_AVAColour(newcolour)
            self.colourways.append(newcolourway)
        self.frames[ColourScreen].display_colourways(self.colourways)

    def add_new_colourway(self,original,diffs,multiplier):
        pass

    def apply_diffs_to_layer_pressed(self):
        if len(self.frames[ColourScreen].diffs) < 1:
            print("no diffs loaded to apply")
            return
        selection = self.frames[ColourScreen].selected_cway.get()
        index = int(selection.split(".")[0])
        print(index)
        for i in range(len(self.colourways[index-1].get_colours())):
            original = self.colourways[index-1].get_colours()[i]
            orig_l = float(original.values['lab'][0])
            orig_a = float(original.values['lab'][1])
            orig_b = float(original.values['lab'][2])
            
            diffs = self.frames[ColourScreen].diffs[i]
            diff_l = diffs[0].cget('text')
            diff_a = diffs[1].cget('text')
            diff_b = diffs[2].cget('text')
            
            newcol = [orig_l+diff_l,orig_a+diff_a,orig_b+diff_b]
            if newcol[0] > 100:
                newcol[0] = 100
            if newcol[0] < 0:
                newcol[0] = 0.00
            if newcol[1] > 127:
                newcol[1] = 127
            if newcol[1] < -128:
                newcol[1] = -128
            if newcol[2] > 127:
                newcol[2] = 127
            if newcol[2] < -128:
                newcol[2] = -128
            self.colourways[index-1].get_colours()[i].set("lab",newcol)
            self.frames[ColourScreen].display_colourways(self.colourways)

class MainScreen(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        load_button = tk.Button(self,text="Load Colourway",command=lambda param=self:Application.load_colourway_pressed(controller))
        self.load_entry = tk.Entry(self)
        self.load_entry.grid(row=0,column=0)
        load_button.grid(row=0,column=1)
        
        self.save_entry = tk.Entry(self)
        self.save_entry.grid(row=1,column=1)
        save_button = tk.Button(self,text="Save Colourway File As", command=lambda param=self:Application.save_colourway_pressed(controller))
        save_button.grid(row=1,column=0)

class ColourScreen(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self.stored_cways = []
        self.selected_cway = tk.StringVar()
        self.boxes = []
        self.diffs = []
        
        self.diff_entry = tk.Entry(self)
        self.diff_entry.grid(row=0,column=2)
        self.diff_entry.config(width=10)
        self.diff_load_button = tk.Button(self,text="Load Diffs",command=lambda param=self:Application.load_diffs_pressed(controller))
        self.diff_load_button.grid(row=0,column=1)
        self.diff_multi_add_button = tk.Button(self,text="Add multiple",command=lambda param=self:Application.add_multiple_diffs_pressed(controller))
        self.diff_multi_add_button.grid(row=0,column=4)
        self.diff_multi_add_button.config(state='disabled')
        self.diff_apply_button = tk.Button(self,text="Apply Diffs",command=lambda param=self:Application.apply_diffs_to_layer_pressed(controller))
        self.diff_apply_button.grid(row=0,column=3)
        self.diff_apply_button.config(state='disabled')
        self.diff_num_added_entry = tk.Entry(self)
        self.diff_num_added_entry.grid(row=0,column=5)
        self.diff_num_added_entry.config(width=5)

    def cway_selected(self,event):
        self.select_cway(self.selected_cway.get())

    def clear_colourway_display(self):
        if len(self.stored_cways) > 0:
            self.stored_cways = []

    def display_colourways(self,colways):
        self.clear_colourway_display()
        if len(self.stored_cways) != 0:
            return
        self.stored_cways = colways
        num_of_cways = len(self.stored_cways)
        cway_numbs = []
        col_numbs = []
        for i in range(num_of_cways):
            cway_numbs.append(str(i+1)+". "+self.stored_cways[i].name)
            cols = self.stored_cways[i].get_colours()
            for j in range(len(cols)):
                col_numbs.append(str(j+1)+". "+cols[j].name)
        colourway_selector = ttk.Combobox(self,textvariable=self.selected_cway,values=cway_numbs)
        colourway_selector.grid(row=0,column=0)
        if self.selected_cway.get() == "":
            self.selected_cway.set(cway_numbs[0])
        colourway_selector.bind("<<ComboboxSelected>>", self.cway_selected)
        print("selected_cway", self.selected_cway.get())
        self.select_cway(self.selected_cway.get())
    
    def display_diffs(self,diffs):
        rows = 1
        self.diff_multi_add_button.config(state='normal')
        self.diff_apply_button.config(state='normal')
        if len(self.diffs) > 0:
            for diff in self.diffs:
                for component in diff:
                    component.destroy()
            self.diffs = []
        for i in range(0,len(diffs),2):
            sample = diffs[i]
            master = diffs[i+1]
            difference = (master.values['lab'][0] - sample.values['lab'][0],master.values['lab'][1] - sample.values['lab'][1],master.values['lab'][2] - sample.values['lab'][2])
            d_l = ttk.Label(self,text=round(difference[0],2))
            d_l.grid(row=rows,column=5)
            d_a = ttk.Label(self,text=round(difference[1],2))
            d_a.grid(row=rows,column=6)
            d_b = ttk.Label(self,text=round(difference[2],2))
            d_b.grid(row=rows,column=7)
            self.diffs.append((d_l,d_a,d_b))
            rows += 1
    
    def select_cway(self, cway_number):
        print("cway_number", cway_number)
        if len(self.boxes) > 0:
            for row in self.boxes:
                for each in row:
                    each.destroy()
        index = cway_number.split('.')
        crow = 1
        for colour in self.stored_cways[int(index[0])-1].get_colours():
            cname = ttk.Label(self,text=colour.name)
            cname.grid(row=crow,column=0)
            lab = colour.values['lab']
            c_l = ttk.Label(self,text=round(lab[0],2))
            c_l.grid(row=crow,column=1,padx=2)
            c_a = ttk.Label(self,text=round(lab[1],2))
            c_a.grid(row=crow,column=2,padx=2)
            c_b = ttk.Label(self,text=round(lab[2],2))
            c_b.grid(row=crow,column=3,padx=2)
            for each in [c_l,c_a,c_b]:
                each.config(width=10,background=BACKGROUND)
            c_display = tk.Label(self,bg=BACKGROUND)
            c_display.config(bg=(lab_to_hex_rgb((lab[0],lab[1],lab[2]))),width=10)
            c_display.grid(row=crow,column=4)
            self.boxes.append((cname,c_l,c_a,c_b,c_display))
            crow += 1

        
"""
    def update_col_display(event=None):
        col_display.config(bg=(lab_to_hex_rgb((float(l_entry.get()),float(a_entry.get()),float(b_entry.get())))))
        col_display = Label(root,width=20,bg="white",height=4)
        col_display.grid(row=4,column=0)


newcol = AVAColour(name="labcolour", lab=(82.45980892, 5.14516228,30.83633068))
newcol3 = AVAColour(name="morergb", rgb=(60399, 51427, 37945))

newcway3 = AVAColourway((newcol,newcol3),name="Third Colourway", locked="false")
colways = AVAXML.extract_colourways_from_xml("colourway_file.cway")
colways.append(newcway3)
colways.append(newcway3)
"""

Application()
