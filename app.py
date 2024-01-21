import customtkinter
from tkinter import messagebox
from tkintermapview import TkinterMapView
import os
import xarray as xr
from pandas import DataFrame
import numpy as np
from dateutil.parser import parse
import re

customtkinter.set_default_color_theme("blue")


class App(customtkinter.CTk):

    APP_NAME = "NetCDF Viewer"
    WIDTH = 1600
    HEIGHT = 1000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Command-q>", self.on_closing)
        self.bind("<Command-w>", self.on_closing)
        self.createcommand('tk::mac::Quit', self.on_closing)

        self.marker_list = []
        self.df_dict = {}

        self.source_file = ''
        self.dataset = None

        self.cwd = os.getcwd()

        # ============ create two CTkFrames ============

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame_left = customtkinter.CTkFrame(master=self, width=150, corner_radius=0, fg_color=None)
        self.frame_left.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        self.frame_middle = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.frame_middle.grid(row=0, column=1, rowspan=1, pady=0, padx=0, sticky="nsew")

        # ============ frame_left ============

        self.frame_left.grid_rowconfigure(11, weight=1)

        self.button_1 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Set Marker",
                                                command=self.set_marker_event)
        self.button_1.grid(pady=(20, 0), padx=(20, 20), row=0, column=0)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Clear Markers",
                                                command=self.clear_marker_event)
        self.button_2.grid(pady=(20, 0), padx=(20, 20), row=1, column=0)

        self.button_3 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Choose File",
                                                command=self.get_file)
        self.button_3.grid(pady=(80, 0), padx=(20, 20), row=2, column=0)

        self.var_label = customtkinter.CTkLabel(self.frame_left, text="Choose variables:", anchor="w")
        self.var_label.grid(row=3, column=0, padx=(20, 20), pady=(80, 0))
        self.var_checkbox_1 = customtkinter.CTkCheckBox(self.frame_left, text="", 
                                                        state=customtkinter.DISABLED, border_width=0)
        self.var_checkbox_1.grid(row=4, column=0, padx=(20, 20), pady=(10, 0))
        self.var_checkbox_2 = customtkinter.CTkCheckBox(self.frame_left, text="", 
                                                        state=customtkinter.DISABLED, border_width=0)
        self.var_checkbox_2.grid(row=5, column=0, padx=(20, 20), pady=(10, 0))
        self.var_checkbox_3 = customtkinter.CTkCheckBox(self.frame_left, text="",
                                                        state=customtkinter.DISABLED, border_width=0)
        self.var_checkbox_3.grid(row=6, column=0, padx=(20, 20), pady=(10, 0))
        self.var_checkboxes = [self.var_checkbox_1,self.var_checkbox_2,self.var_checkbox_3]

        vcmd = (self.register(self.validate_date), '%P')
        
        self.start_date_label = customtkinter.CTkLabel(self.frame_left, text="Start date:", anchor="w")
        self.start_date_label.grid(row=7, column=0, padx=(20,20), pady=(20,0))
        self.start_date_entry = customtkinter.CTkEntry(master=self.frame_left,placeholder_text="yyyy-mm-dd", 
                                                        validate='focusout', validatecommand=vcmd)
        self.start_date_entry.grid(row=8, column=0, padx=(10,0), pady=12)

        self.end_date_label = customtkinter.CTkLabel(self.frame_left, text="End date:", anchor="w")
        self.end_date_label.grid(row=9, column=0, padx=(20,20), pady=(10,0))
        self.end_date_entry = customtkinter.CTkEntry(master=self.frame_left,placeholder_text="yyyy-mm-dd", 
                                                    validate='focusout', validatecommand=vcmd)
        self.end_date_entry.grid(row=10, column=0, padx=(10,0), pady=12)

        self.button_4 = customtkinter.CTkButton(self.frame_left, text="Enter", command=self.process_csv)
        self.button_4.grid(row=11, column=0, pady=(50, 0), padx=(20, 20))

        self.map_label = customtkinter.CTkLabel(self.frame_left, text="Tile Server:", anchor="w")
        self.map_label.grid(row=12, column=0, padx=(20, 20), pady=(20, 0))
        self.map_option_menu = customtkinter.CTkOptionMenu(self.frame_left, values=["OpenStreetMap", "Google normal", "Google satellite"],
                                                                       command=self.change_map)
        self.map_option_menu.grid(row=13, column=0, padx=(20, 20), pady=(10, 0))

        self.appearance_mode_label = customtkinter.CTkLabel(self.frame_left, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=14, column=0, padx=(20, 20), pady=(20, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.frame_left, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=15, column=0, padx=(20, 20), pady=(10, 20))

        # ============ frame_middle ============

        self.frame_middle.grid_rowconfigure(1, weight=1)
        self.frame_middle.grid_rowconfigure(0, weight=0)
        self.frame_middle.grid_columnconfigure(0, weight=1)
        self.frame_middle.grid_columnconfigure(1, weight=0)
        self.frame_middle.grid_columnconfigure(2, weight=1)

        self.map_widget = TkinterMapView(self.frame_middle, corner_radius=0)
        self.map_widget.grid(row=1, rowspan=1, column=0, columnspan=3, sticky="nswe", padx=(0, 0), pady=(0, 0))

        self.entry = customtkinter.CTkEntry(master=self.frame_middle,
                                            placeholder_text="type latitide,longitude")
        self.entry.grid(row=0, column=0, sticky="we", padx=(12, 0), pady=12)
        self.entry.bind("<Return>", self.search_event)

        self.button_5 = customtkinter.CTkButton(master=self.frame_middle,
                                                text="Search",
                                                width=90,
                                                command=self.search_event)
        self.button_5.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=12)

        self.map_widget.add_right_click_menu_command(label="Add Marker",
                                        command=self.add_marker_event,
                                        pass_coords=True)

        # Set default values
        self.map_widget.set_address("Kathmandu") 
        self.map_option_menu.set("Google normal")
        self.appearance_mode_optionemenu.set("Dark")

    def search_event(self, event=None):
        self.map_widget.set_address(self.entry.get())

    def set_marker_event(self):
        current_position = self.map_widget.get_position()
        self.marker_list.append(self.map_widget.set_marker(current_position[0], current_position[1]))

    def add_marker_event(self, coords):
        new_marker = self.map_widget.set_marker(coords[0], coords[1])
        self.marker_list.append(new_marker)

    def clear_marker_event(self):
        for marker in self.marker_list:
            marker.delete()

    def change_appearance_mode(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_map(self, new_map: str):
        if new_map == "OpenStreetMap":
            self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        elif new_map == "Google normal":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
        elif new_map == "Google satellite":
            self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

    def get_file(self):
        self.source_file = customtkinter.filedialog.askopenfilename(parent=self, initialdir=self.cwd, title='Please select a netcdf file')
        if os.path.isfile(self.source_file) and not self.source_file.endswith('.nc'):
            messagebox.showerror(title="File format not recognized", message="Please select a netcdf file")
            self.source_file=''
            self.get_file()
        if self.source_file.endswith('.nc'):
            self.read_file()
        variables = self.get_variables()
        for i in range(3):
            if i < len(variables):
                self.var_checkboxes[i].configure(text=variables[i],state=customtkinter.NORMAL, border_width=3)

    def read_file(self):
        with xr.open_dataset(self.source_file, decode_coords = 'all') as file:
                self.dataset = file
        min_lon, max_lon, min_lat, max_lat = self.get_bounds()
        top_left = (max_lat,min_lon)
        bottom_right = (min_lat,max_lon)
        self.fit_box(top_left, bottom_right)
        top_right = (max_lat,max_lon)
        bottom_left = (min_lat,min_lon)
        self.set_polygon([top_left,top_right,bottom_right,bottom_left])

    def get_bounds(self):
        min_lon, max_lon = (float(self.dataset['lon'][0]), float(self.dataset['lon'][-1]))
        max_lat, min_lat = (float(self.dataset['lat'][0]), float(self.dataset['lat'][-1]))
        lon_res, lat_res = self.get_resolution()
        return (min_lon-lon_res,max_lon+lon_res,min_lat-lat_res,max_lat+lat_res)

    def get_resolution(self):
        lat_res = float(self.dataset['lat'][0] - self.dataset['lat'][1])
        lon_res = float(self.dataset['lon'][1] - self.dataset['lon'][0])
        return (lon_res,lat_res)

    def get_variables(self):
        return [i for i in self.dataset.data_vars]

    def set_polygon(self, points):
        self.map_widget.set_polygon(points, outline_color='red', border_width=8)

    def fit_box(self, top_left, bottom_right):
        self.map_widget.fit_bounding_box(top_left, bottom_right)

    def get_checked_vars(self):
        self.checked_vars=[]
        for i, checkbox in enumerate(self.var_checkboxes):
            if checkbox.get():
                self.checked_vars.append(self.get_variables()[i])

    def get_nearest_point(self,point):
        lat, lon = point.position
        lat_idx = (np.abs(self.dataset['lat'] - lat)).argmin()
        lon_idx = (np.abs(self.dataset['lon'] - lon)).argmin()
        return (self.dataset['lat'][lat_idx], self.dataset['lon'][lon_idx])

    def validate_date(self, value):
        pattern = r'^(((\d{4}-((0[13578]-|1[02]-)(0[1-9]|[12]\d|3[01])|(0[13456789]-|1[012]-)(0[1-9]|[12]\d|30)|02-(0[1-9]|1\d|2[0-8])))|((([02468][048]|[13579][26])00|\d{2}([13579][26]|0[48]|[2468][048])))-02-29)){0,10}$'
        if re.fullmatch(pattern, value) is None:
            self.on_invalid()
            return False
        return True
    
    def on_invalid(self):
        messagebox.showerror(title="Date format invalid", message="Please enter a valid date in yyyy-mm-dd format")

    def process_csv(self):
        self.get_checked_vars()
        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()
        if not self.marker_list:
            messagebox.showerror(title="Marker not set", message="Please set a marker")
        elif not self.checked_vars:
            messagebox.showerror(title="Variable not selected", message="Please choose a variable")
        elif (not start_date) or (not end_date):
            messagebox.showerror(title="Date not entered", message = "Please enter both start and end dates")
        elif parse(start_date) >= parse(end_date):
            messagebox.showerror(title="Date order incorrect", message="End date cannot be smaller than start date")
        else:
            self.button_4.configure(text="Processing", state=customtkinter.DISABLED)
            time_subset = self.dataset['time'].sel(time = slice(start_date,end_date)).to_numpy()
            for var in self.checked_vars:
                subset_df = DataFrame(time_subset, columns=['time'])
                for point in self.marker_list:
                    nearest_lat, nearest_lon = self.get_nearest_point(point)
                    subset_xr = self.dataset[var].sel(
                        time = slice(start_date, end_date),
                        lon = nearest_lon,
                        lat = nearest_lat
                    )
                    arr = subset_xr.to_numpy()
                    subset_df[str(tuple(round(coord,5) for coord in point.position))] = arr
                self.df_dict[var] = subset_df
            self.button_4.configure(text = "Export csv", state = customtkinter.NORMAL, command=self.export_csv)

    def export_csv(self):
        self.export_dir = customtkinter.filedialog.askdirectory(parent=self, initialdir=self.cwd, title="Please select download directory")
        for var, df in self.df_dict.items():
            df.to_csv(os.path.join(self.export_dir, f'{var}.csv'), index = False)
        self.button_4.configure(text = "Enter", command = self.process_csv)

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
