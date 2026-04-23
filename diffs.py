import os
import tkinter as tk
from tkinter import ttk
import threading
import shutil
import subprocess
import datetime
import math
from skimage import color
import time
import statistics
import random
import string

G_colourway_dir = ""
G_diff_dir = ""
G_output_dir = ""
G_background = ""
G_entry_background = ""
G_text_colour = ""
G_active_btn_col = ""
G_inactive_btn_col = ""

G_loaded_UUID = ""
G_space_needed = [400,45]
G_num_of_colourways_loaded = 0

def read_settings():
    global G_colourway_dir,G_diff_dir,G_output_dir,G_background,G_text_colour, G_active_btn_col, G_inactive_btn_col, G_entry_background
    with open("settings.txt","r") as file:
        raw_file = file.read()
        lines = raw_file.split("\n")
        G_colourway_dir = lines[0].split("=")[0]
        G_diff_dir = lines[1].split("=")[0]
        G_output_dir = lines[2].split("=")[0]
        G_background = lines[3].split("=")[0]
        G_text_colour= lines[4].split("=")[0]
        G_active_btn_col = lines[5].split("=")[0]
        G_inactive_btn_col = lines[6].split("=")[0]
        G_entry_background = lines[7].split("=")[0]

class AVAColourway:
    def __init__(self, *colours, name="", locked="false", modified=False):
        self.name = name
        self.locked = locked
        self.has_been_modified = modified
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
    def __init__(self, name="", rgb=None, xyz="", ref="", lab=None, uuid="",diff=False):
        self.name = name
        self.uuid = uuid
        self.values = {}
        self.ref_found = 0
        self.xyz_found = 0
        self.lab_found = 0
        self.rgb_found = 0
        ## RGB Format (integers 0-65535, 0-65535, 0-65535)
        ## XYZ Format (floats 0-100, 0-100, 0-100)
        
        if rgb:
            self.rgb_found = 1
            self.values['rgb']=rgb
            print("RGB Found: " + str(self.values['rgb']))
        if ref:
            self.ref_found = 1
            self.values['ref']=ref
            print("REF Found: " + str(len(self.values['ref']))+" values")
        if xyz:
            self.xyz_found = 1
            self.values['xyz']=xyz
            print("XYZ Found: " + str(self.values['xyz']))
        if lab:
            self.lab_found = 1
            self.values['lab']=lab
            print("LAB Found: " + str(self.values['lab']))
        
        if self.ref_found == 0 and diff==False:
            self.values['ref'] = ""
            print("No Ref Found: Setting to Blank")
        
        if self.lab_found == 0 and diff==False:
            print("No Lab found")
            if self.xyz_found:
                temp = color.xyz2lab((float(xyz[0])/100,float(xyz[1])/100,float(xyz[2])/100))
                self.values['lab'] = temp
                print(str(xyz)+ ": XYZ to LAB:" + str(temp))
        
        if self.xyz_found == 0 and diff==False:
            print("no XYZ found")
            if self.lab_found:
                self.values['xyz'] = labtoxyz(lab)
                
        if self.rgb_found == 0 and diff==False:
            print("no RGB found")
            self.values['rgb'] = labtorgb(lab)
            
    def print(self):
        print("Colour Name:", self.name, "LAB:",self.values['lab'],"RGB:", self.values['rgb'])
        
    def changelab(self,newlab):
        print("Setting colour", self.name + "lab to" + str(newlab))
        self.values['lab'] = newlab
        self.values['rgb'] = labtorgb(newlab)
        self.values['xyz'] = labtoxyz(newlab)
        print("Changed Colour:" + self.name + "LAB: " + str(newlab) + "RGB:" + str(self.values['rgb']) + "XYZ" + str(self.values['xyz']))

    def setname(self,newname):
        self.name = newname

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

    def remove_cmyk(line):
        if "cmyk:" in line:
            before = line.split("cmyk:")[0]
            after = line.split("cfu:1")[1]
            print("BEFORE",before,"AFTER", after)
            return before + "cfu:1" + after
        else:
            return line
        
    
    def extract_colourways_from_xml(filename):
        global G_loaded_UUID, G_num_of_colourways_loaded
        colourways = []
        with open(filename, 'r') as file:
            header = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>AVA_Colourway_Info</key><string>2.0</string><key>colourways</key><array>'
            raw_file = file.read().replace("\n", "").replace("\t","") # removed spaces and linebreaks
            footer = raw_file[-126:]
            G_loaded_UUID = AVAXML.extract_value(footer,"doc-UUID")
            removed_header = raw_file.replace(header,"").replace(footer,"") #file with removed header + footer
            stripped_colourways = removed_header.split("<dict><key>layers</key><array>")
            G_num_of_colourways_loaded = 0
            for colway in stripped_colourways:
                if colway:
                    cway_name = AVAXML.extract_value(colway,"name","<string>","</string>")
                    cway_locked = AVAXML.extract_value(colway,"locked","<","/>")
                    colours = []
                    test = colway.split("<dict><key>colour</key><string>")
                    for each in test:
                        if each:
                            removed_cmyk = AVAXML.remove_cmyk(each)
                            coldata = AVAXML.get_colourdata_from_line(removed_cmyk)
                            cname = coldata[0]
                            cuuid = AVAXML.extract_value(removed_cmyk,"uuid","<string>","</string>")
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
                    G_num_of_colourways_loaded += 1
                    colourways.append(new)
            return colourways

    def create_AVA_colourway_file(*colourways, name):
        global G_output_dir, G_loaded_UUID, G_num_of_colourways_loaded
        header = '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>AVA_Colourway_Info</key><string>2.0</string><key>colourways</key><array>'
        footer = '</array><key>docInfo</key><dict><key>doc-UUID</key><string>'+G_loaded_UUID+'</string></dict></dict></plist>'
        current_text = header
        cways = colourways[0]
        count = 1
        for each in cways:
            if count > G_num_of_colourways_loaded or each.has_been_modified == True:
                current_text += AVAXML.format_xml_colourway_string(each)        ## Output CWAY file only contains added colourways
            count += 1
        current_text += footer
        G_loaded_UUID = ""
        with open(G_output_dir+"/"+name, "w") as text_file:
            text_file.write(current_text)

    def generate_colour_uuid():
        random_string = ""
        for num in (8,4,4,4,12):
            random_string += ''.join(random.choices(string.ascii_uppercase + string.digits, k=num))
            if num != 12:
                random_string += '-'
        print("Generated Col-UUID", str(random_string))
        return random_string # 8 - 4 - 4 - 4 - 12

    def format_xml_colourway_string(colway):
        format = "<dict><key>layers</key><array>\n"
        for each in colway.get_colours():
            if each.values['ref'] == "":
                ref = ""
            else:
                ref = ""
                for nums in each.values['ref']:
                    ref += nums + ','
            if each.uuid == "":
                each.uuid = AVAXML.generate_colour_uuid()
            new = "<dict><key>colour</key><string>" + each.name +  \
            "\trgb:" + str(each.values['rgb'][0]) + "," + str(each.values['rgb'][1]) + "," + str(each.values['rgb'][2]) + \
            "\txyz:" + str(each.values['xyz'][0]) + "," + str(each.values['xyz'][1]) + "," + str(each.values['xyz'][2]) + \
            "\tref:" + ref + \
            "\tcfu:1</string><key>uuid</key><string>" + \
            each.uuid + "</string></dict>\n"
            format += new
        #if colway.name == "":
        #    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        #    colway.name = random_string
        format += "</array><key>locked</key><" + colway.locked + "/><key>name</key><string>" + colway.name + "</string></dict>\n"
        return format

class AVADiffs:
    def load_diffs(filename):  # Returns a tuple containing master and sample colours (Sample1, Master1, S2, M2 ....)
        global G_diff_dir
        cols = []
        with open(G_diff_dir+"/"+filename, 'r') as file:
            raw_read = file.read().replace("\t",",")
            lines = raw_read.split("\n")
            remove_header = lines[2:]
            remove_footer = remove_header[:-5]
            delta_e_list = []
            for line in remove_footer:
                cells = line.split(",")
                new_sample = AVAColour(name=cells[0],lab=(float(cells[1]),float(cells[2]),float(cells[3])),diff=True)
                new_master = AVAColour(name=cells[4],lab=(float(cells[5]),float(cells[6]),float(cells[7])),diff=True)
                delta_e_list.append(get_delta_e(new_master.values['lab'],new_sample.values['lab']))
                cols.append(new_sample)
                cols.append(new_master)
            print(delta_e_list)
        return (cols,delta_e_list)

def labtorgb(lab):
    temp = color.lab2rgb(lab)
    print(str(lab) +": LAB 2 RGB:", int(temp[0]*65536),int(temp[1]*65536), int(temp[2]*65536))
    return [int(temp[0]*65536),int(temp[1]*65536), int(temp[2]*65536)]

def labtoxyz(lab):
    temp = color.lab2xyz(lab)
    multiplied = [float(temp[0])*100,float(temp[1])*100,float(temp[2])*100]
    clamped = []
    for i in range(3):
        if multiplied[i] >= 0.0 and multiplied[i] <= 100.0:
            clamped.append(multiplied[i])
        elif multiplied[i] < 0:
            clamped.append(0.0)
        elif multiplied[i] > 100.0:
            clamped.append(100.0)
    print(str(lab) + ": LAB to XYZ:" + str(clamped))
    return clamped

def rgb16tosrgb(rgb16):
    return (float(rgb16[0])/65536,float(rgb16[1])/65536,float(rgb16[2])/65536)

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
        threading.Thread(target=self.dimension_watcher,daemon=True).start()
        read_settings()
        container = tk.Frame(self,bg=G_background)
        self.attributes("-fullscreen", False)
        #self.wm_attributes('-type', 'splash')
        self.geometry(None)
        container.pack(side="top",fill="both",expand=True)
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)    
        self.frames = {}
        self.colourways = []

        for each in (MainScreen, ColourScreen):
            frame = each(container, self)
            self.frames[each] = frame
            frame.grid(row=0,column=0,sticky="nsew")
        
        self.bind("<Escape>", exit)
        self.show_frame(MainScreen)
        self.mainloop()
    
    def dimension_watcher(self):
        global G_space_needed
        space_set = G_space_needed
        self.geometry("400x45")
        while True:
            time.sleep(0.5)
            if G_space_needed != space_set:
                self.geometry(str(G_space_needed[0])+"x"+str(G_space_needed[1]))
                space_set = G_space_needed
                print("Changed Dimensions to " + str(space_set[0]) + "x" + str(space_set[1]))
    
    def show_frame(self,cont):
        frame = self.frames[cont]
        frame.on_raise()
        frame.tkraise()
    
    def load_colourway_pressed(self):
        string = self.frames[MainScreen].load_entry.get()
        if string == "":
            return
        else:
            self.colourways = AVAXML.extract_colourways_from_xml(G_colourway_dir+"/"+string)
        self.show_frame(ColourScreen)
        self.frames[ColourScreen].display_colourways(self.colourways)
    
    def save_colourway_pressed(self):
        global G_diff_dir, G_colourway_dir
        current_diff_file = self.frames[ColourScreen].diff_entry.get()
        if os.path.exists(G_diff_dir+"/"+current_diff_file) and current_diff_file != "":
            print("Attemping to remove", G_diff_dir+"/"+current_diff_file)
            os.remove(G_diff_dir+"/"+current_diff_file)
        AVAXML.create_AVA_colourway_file(self.colourways,name=self.frames[MainScreen].load_entry.get())
        current_cway_file = self.frames[MainScreen].load_entry.get()
        if os.path.exists(G_colourway_dir+"/"+current_cway_file):
            os.remove(G_colourway_dir+"/"+current_cway_file)
        ColourScreen.clear_diffs(self.frames[ColourScreen])
        self.show_frame(MainScreen)

    def load_diffs_pressed(self):
        global G_text_colour, G_background
        string = self.frames[ColourScreen].diff_entry.get()
        if string == "":
            return
        else:
            loaded_diffs = AVADiffs.load_diffs(string)
            self.frames[ColourScreen].deltaE.set(round(statistics.mean(loaded_diffs[1]),2))
            self.frames[ColourScreen].deltaE_label.config(fg=G_text_colour,bg=G_background)
            ColourScreen.display_diffs(self.frames[ColourScreen],loaded_diffs[0])

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
            self.colourways[index-1].get_colours()[i].changelab(newcol)
            self.colourways[index-1].has_been_modified = True
            self.frames[ColourScreen].display_colourways(self.colourways,retain=True)

class MainScreen(tk.Frame):
    def __init__(self,parent,controller):
        global G_entry_background,G_text_colour
        tk.Frame.__init__(self,parent)
        self.config(bg=G_background)
        load_button = tk.Button(self,text="Load Colourway",command=lambda param=self:Application.load_colourway_pressed(controller),bg=G_active_btn_col,fg=G_text_colour)
        self.load_entry = tk.Entry(self,bg=G_entry_background,fg=G_text_colour)
        self.load_entry.grid(row=0,column=0)
        load_button.grid(row=0,column=1)
        self.cont = controller

    def on_raise(self):
        global G_space_needed
        G_space_needed = [400,45]
        threading.Thread(target=self.colourway_watcher,daemon=True).start()

    def colourway_watcher(self):
        global G_colourway_dir
        print("Colourway Watcher Started")
        while True:
            time.sleep(0.5)
            files = os.listdir(G_colourway_dir)
            files = [f for f in files if os.path.isfile(G_colourway_dir+'/'+f)]
            for each in files:
                if ".cway" in each:
                    self.load_entry.delete(0,tk.END)
                    self.load_entry.insert(0,each)
                    print("File Found: " + each)
                    Application.load_colourway_pressed(self.cont)
                    return
            self.load_entry.delete(0,tk.END)

class ColourScreen(tk.Frame):
    def __init__(self,parent,controller):
        tk.Frame.__init__(self,parent)
        self.config(bg=G_background)
        self.stored_cways = []
        self.selected_cway = tk.StringVar()
        self.boxes = []
        self.diffs = []
        self.deltaE = tk.StringVar()
        self.cont = controller

        self.diff_entry = tk.Entry(self,bg=G_entry_background,fg=G_text_colour)
        self.diff_entry.grid(row=0,column=2)
        self.diff_entry.config(width=10)
        self.diff_load_button = tk.Button(self,text="Load Diffs",command=lambda param=self:Application.load_diffs_pressed(controller),bg=G_active_btn_col, fg=G_text_colour)
        self.diff_load_button.grid(row=0,column=1)
        self.diff_load_button.config(state='disabled',bg=G_inactive_btn_col)
        self.diff_multi_add_button = tk.Button(self,text="Add multiple",command=lambda param=self:Application.add_multiple_diffs_pressed(controller),bg=G_active_btn_col,fg=G_text_colour)
        self.diff_multi_add_button.grid(row=0,column=4)
        self.diff_multi_add_button.config(state='disabled',bg=G_inactive_btn_col)
        self.diff_apply_button = tk.Button(self,text="Apply Diffs",command=lambda param=self:Application.apply_diffs_to_layer_pressed(controller),bg=G_active_btn_col,fg=G_text_colour)
        self.diff_apply_button.grid(row=0,column=3)
        self.diff_apply_button.config(state='disabled',bg=G_inactive_btn_col)
        self.diff_num_added_entry = tk.Entry(self,bg=G_entry_background,fg=G_text_colour)
        self.diff_num_added_entry.grid(row=0,column=5)
        self.diff_num_added_entry.config(width=5)
        self.diff_num_added_entry.insert(0,"4")
        self.deltaE_label = tk.Label(self, text="ΔE",bg=G_background,fg=G_background)
        self.deltaE_label.grid(row=0,column=7)
        self.deltaE_display = tk.Label(self,textvariable=self.deltaE,bg=G_background,fg=G_text_colour)
        self.deltaE_display.grid(row=0,column=8)
        save_button = tk.Button(self,text="Save", command=lambda param=self:Application.save_colourway_pressed(controller),bg=G_active_btn_col,fg=G_text_colour)
        save_button.grid(row=0,column=6)

    def on_raise(self):
        threading.Thread(target=self.diff_watcher,daemon=True).start()

    def diff_watcher(self):
        global G_diff_dir
        print("Diff Watcher Started")
        self.diff_load_button.config(state='disabled',background=G_inactive_btn_col)
        self.diff_multi_add_button.config(state='disabled',background=G_inactive_btn_col)
        self.diff_apply_button.config(state='disabled',background=G_inactive_btn_col)
        while True:
            time.sleep(0.5)
            files = os.listdir(G_diff_dir)
            files = [f for f in files if os.path.isfile(G_diff_dir+"/"+f)]
            for each in files:
                self.diff_entry.delete(0,tk.END)
                self.diff_entry.insert(0,each)
                self.diff_load_button.config(state='normal',bg=G_active_btn_col)
                Application.load_diffs_pressed(self.cont)
                return
            self.diff_entry.delete(0,tk.END)

    def cway_selected(self,event):
        self.select_cway(self.selected_cway.get())

    def clear_colourway_display(self):
        if len(self.stored_cways) > 0:
            self.stored_cways = []

    def display_colourways(self,colways,retain=False):
        global G_space_needed
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
        G_space_needed = [820,30+(24*len(self.stored_cways[0].get_colours()))]
        colourway_selector = ttk.Combobox(self,textvariable=self.selected_cway,values=cway_numbs,background=G_entry_background,foreground=G_text_colour)
        colourway_selector.grid(row=0,column=0)
        #if self.selected_cway.get() == "":
        if retain == False:
            self.selected_cway.set(cway_numbs[-1])
        colourway_selector.bind("<<ComboboxSelected>>", self.cway_selected)
        print("selected_cway", self.selected_cway.get())
        self.select_cway(self.selected_cway.get())
    
    def clear_diffs(self):
        if len(self.diffs) > 0:
            for diff in self.diffs:
                for component in diff:
                    component.destroy()
            self.diffs = []
        self.deltaE.set("")
        self.deltaE_label.config(fg=G_background)
    
    def display_diffs(self,diffs):
        rows = 1
        self.diff_multi_add_button.config(state='normal',bg=G_active_btn_col)
        self.diff_apply_button.config(state='normal',bg=G_active_btn_col)
        if len(self.diffs) > 0:
            for diff in self.diffs:
                for component in diff:
                    component.destroy()
            self.diffs = []
        for i in range(0,len(diffs),2):
            sample = diffs[i]
            master = diffs[i+1]
            difference = (master.values['lab'][0] - sample.values['lab'][0],master.values['lab'][1] - sample.values['lab'][1],master.values['lab'][2] - sample.values['lab'][2])
            d_l = ttk.Label(self,text=round(difference[0],2),background=G_background,foreground=G_text_colour)
            d_l.grid(row=rows,column=5)
            d_a = ttk.Label(self,text=round(difference[1],2),background=G_background,foreground=G_text_colour)
            d_a.grid(row=rows,column=6)
            d_b = ttk.Label(self,text=round(difference[2],2),background=G_background,foreground=G_text_colour)
            d_b.grid(row=rows,column=7)
            self.diffs.append((d_l,d_a,d_b))
            rows += 1
    
    def select_cway(self, cway_number):
        global G_background
        print("cway_number", cway_number)
        if len(self.boxes) > 0:
            for row in self.boxes:
                for each in row:
                    each.destroy()
        index = cway_number.split('.')
        crow = 1
        for colour in self.stored_cways[int(index[0])-1].get_colours():
            cname = ttk.Label(self,text=colour.name,background=G_background,foreground=G_text_colour)
            cname.grid(row=crow,column=0)
            lab = colour.values['lab']
            c_l = ttk.Label(self,text=round(lab[0],2),foreground=G_text_colour,background=G_background)
            c_l.grid(row=crow,column=1,padx=2)
            c_a = ttk.Label(self,text=round(lab[1],2),foreground=G_text_colour,background=G_background)
            c_a.grid(row=crow,column=2,padx=2)
            c_b = ttk.Label(self,text=round(lab[2],2),foreground=G_text_colour,background=G_background)
            c_b.grid(row=crow,column=3,padx=2)
            for each in [c_l,c_a,c_b]:
                each.config(width=10,background=G_background)
            c_display = tk.Label(self,bg=G_background)
            c_display.config(bg=(lab_to_hex_rgb((lab[0],lab[1],lab[2]))),width=10)
            c_display.grid(row=crow,column=4)
            self.boxes.append((cname,c_l,c_a,c_b,c_display))
            crow += 1

Application()
