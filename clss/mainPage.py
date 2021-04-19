from kivy.uix.screenmanager import Screen
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty, ListProperty
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from tkinter import Tk
from tkinter import filedialog
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.slider import Slider
import time
import xxhash
from collections import defaultdict
from kivy.graphics import Color, Rectangle
import shutil
import threading
from kivy.clock import Clock
import ctypes
from kivy.uix.progressbar import ProgressBar
from PIL import Image as Img
from PIL import ImageStat

libbytiff = ctypes.CDLL("libtiff-5.dll")
libbytiff.TIFFSetWarningHandler.argtypes = [ctypes.c_void_p]
libbytiff.TIFFSetWarningHandler.restype = ctypes.c_void_p
libbytiff.TIFFSetWarningHandler(None)


class ImageButton(ButtonBehavior, Image):
    pass

class MainPage(Screen):

    def __init__(self, **kwargs):
        super(MainPage, self).__init__(**kwargs)
        self.types = ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'nef']
        self.abc = 0
        self.no = 0
        self.dupli = []
        self.dupli_name = []
        self.dirname = ''
        self.moved_dirname=''
        self.filesizes = defaultdict(list)
        self.filenames = defaultdict(list)
        self.filehash = defaultdict(list)
        self.files = []
        self.matches = []
        self.all_duplicates = []
        self.all_names_duplicates = []
        self.h = []
        self.rem = 0
        self.temp_files = 0
        self.val = 120
        self.searched = []
        self.rv = ObjectProperty()
        self.textColor = (0.2, 0.2, 0.2, 1)
        self.colors = defaultdict(list)
        self.colorlist = []
        self.remainingText = ''

    def start_th(self, instance):
        """Threading"""
        a = threading.Thread(target=self.insertfunc)
        a.daemon = True
        a.start()
        a.join()

    def insertfunc(self):
        """schedule_once"""
        Clock.schedule_once(lambda x: self.add_item(self.rem))

    def sliderValue(self, val):
        """Change row height from slider"""
        self.ids.rbl.default_size = (None, val)

    def add_item(self, idx, *args):
        """Add 'x' items to the list"""
        try:
            self.rem -= idx
            self.no += idx
            self.ids.progressBar.value = self.no
            prc = (self.no*100)/self.abc
            self.ids.percent.text = "{:.2f} %".format(prc)
            self.ids.remaining.text = self.remainingText + str(self.rem)
            for i in range(idx):
                a = next(self.dupli)

                if len(a) == 1:
                    end = a[0].split('.')[-1]
                    try:
                        sz = os.path.getsize(a[0])/1024
                    except:
                        sz = 0
                        pass
                    sz = "{:.2f} KB".format(sz)
                    if end.lower() in self.types:
                        try:
                            im = Img.open(a[0])
                            width, height = im.size
                            good=a[0]
                        except:
                            width=''
                            height=''
                            good=''
                            # continue
                        self.ids.rv.data.insert(0, {'image': str(good), 'sz': str(
                            sz), 'txt': str(a[0]), 'clr': self.textColor, 'rez': str(width)+'x'+str(height)})
                    else:
                        self.ids.rv.data.insert(0, {'image': 'default.png', 'sz': str(
                            sz), 'txt': str(a[0]), 'clr': (0.35, 0.35, 0.35, 1), 'rez': ''})
                if len(a) > 1:
                    for j in a:
                        # print('more than 1: ',j)
                        end = j.split('.')[-1]
                        try:
                            sz = os.path.getsize(j)/1024
                        except:
                            sz = 0
                        sz = "{:.2f} KB".format(sz)
                        if end.lower() in self.types:
                            try:
                                im = Img.open(j)
                                width, height = im.size
                                self.ids.rv.data.insert(0, {'image': str(j), 'sz': str(
                                    sz), 'txt': str(j), 'clr': self.textColor, 'rez': str(width)+'x'+str(height)})
                            except:
                                print('Could not open file: ',j)
                                pass
                        else:
                            self.ids.rv.data.insert(0, {'image': 'default.png', 'sz': str(
                                sz), 'txt': str(j), 'clr': self.textColor, 'rez': ''})
                    self.textColor = (0.2, 0.2, 0.2, 1) if self.textColor == (
                        0.35, 0.35, 0.35, 1) else (0.35, 0.35, 0.35, 1)
            self.ids.remainingItems.text = ' Items in the list: ' + str(len(self.ids.rv.data)) + ' '
            self.addButtonsDisabledEnabled(self.rem)
        except StopIteration:
            self.ids.remaining.text = 'Remaining duplicates: 0'
            self.disable5buttons()
            self.ids.progressBar.value = self.abc
            self.ids.percent.text = "100.00 %"
            pass

    def chooseDir(self):
        """Choose source folder"""
        Tk().withdraw()
        dial = filedialog.askdirectory()
        if dial == '' or dial == self.dirname:
            return
        else:
            self.empty_lists()
            self.disable5buttons()
            self.dirname = ''
            self.dirname = dial
            self.ids.lbl.text = dial
            self.ids.lbl.color = (1, 1, 1, 1)
            self.opn(self.dirname, self.moved_dirname)

    def chooseMovedDirname(self):
        """Choose destination folder"""
        Tk().withdraw()
        dial = filedialog.askdirectory()
        if dial == '' or dial == self.moved_dirname:
            return
        else:
            self.ids.lbl1.text = dial
            self.ids.lbl1.color = (1, 1, 1, 1)
            self.moved_dirname = dial
            self.opn(self.dirname, self.moved_dirname)

    def opn(self, pth1, pth2):
        """Check if source and destination directories are True and not the same"""
        if pth1==pth2:
            self.sameFolderPopup()
            return

        if pth1 and pth2:
            self.buttonsEnabled()
            th6 = threading.Thread(target=self.walk, args=[self.dirname, ])
            th6.daemon = True
            th6.start()
        else:
            return

    def walk(self, dirname):
        """Walk to entire directory and add files to the list files"""
        self.files = []
        a = ("{}\{}".format(i, x)
             for i, j, k in os.walk(self.dirname) for x in k)
        b = 1
        try:
            for i in a:
                self.files.append(i)
                self.ids.loading.text = str(b)+' : '+i
                b += 1
        except:
            pass
        self.ids.loading.text = str(len(self.files))+' files scanned.'
        return self.files

    def find_matches(self, files):
        """Return a list of files matching the extension given
        files: list of filepaths
        matches: only the matched files in the directory"""
        self.matches = []
        if self.ids.extension.text == '':
            self.matches = [x for x in files]
        elif self.ids.extension.text != '':
            self.matches = [x for x in files if x.lower().endswith(
                self.ids.extension.text.lower())]
        return self.matches

    def comp_filesizes(self, matches):
        # matches = self.matches
        """Compute filesizes and return a dictionary where the keys are
        the filesizes and the values are a list of files with that filesize

        matches: list of filepaths
        filesizes: dictionary of filesizes"""

        # Create a default dictionary where the default value is an empty list
        self.filesizes = defaultdict(list)

        # Compute the filesize of each of the files in the directory
        a = len(matches)
        b = 0
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = a
        self.ids.progressBar.value = 0
        try:
            for file in matches:
                self.filesizes[os.path.getsize(file)].append(file)
                self.ids.loading.text = str(a)+" : "+file
                self.ids.progressBar.value = b
                b += 1
                prc = (b*100)/len(self.matches)
                self.ids.percent.text = "{:.2f} %".format(prc)
                a -= 1
        except:
            a -= 1
            pass
        self.size_duplicates(self.filesizes)
        self.rem = len(self.all_duplicates)
        self.abc = len(self.all_duplicates)

        self.ids.itm.text = 'Duplicates found: '+str(self.abc)
        self.dupli = ()
        self.dupli = iter(self.all_duplicates)
        self.ids.loading.text = str(len(matches))+' files searched.'
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = len(self.all_duplicates)
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"
        self.addButtonsDisabledEnabled(len(self.all_duplicates))
        self.buttonsEnabled()
        self.remainingText = 'Remaining duplicates: '
        self.ids.remaining.text = self.remainingText + str(self.abc)
        return self.filesizes

    def comp_filenames(self, matches):
        # matches = self.matches
        """Compute filesizes and return a dictionary where the keys are
        the names and the values are a list of files with that name

        files: list of filepaths
        filenames: dictionary of names"""

        # Create a default dictionary where the default value is an empty list
        self.filenames = defaultdict(list)

        # Compute the filesize of each of the files in the directory
        sz = len(self.matches)
        b = 0
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = sz
        self.ids.progressBar.value = 0
        for file in matches:
            a = file.split('\\')[-1]
            self.filenames[a].append(file)
            self.ids.loading.text = str(sz)+" : " + file
            self.ids.progressBar.value = b
            b += 1
            prc = (b*100)/len(self.matches)
            self.ids.percent.text = "{:.2f} %".format(prc)
            sz -= 1

        self.name_duplicates(self.filenames)  # -> self.all_names_duplicates
        self.rem = len(self.all_names_duplicates)
        self.abc = len(self.all_names_duplicates)

        self.ids.itm.text = 'Duplicates found: '+str(self.abc)
        self.dupli = ()
        self.dupli = iter(self.all_names_duplicates)
        self.ids.loading.text = str(len(matches))+' files searched.'
        self.addButtonsDisabledEnabled(len(self.all_names_duplicates))

        self.ids.progressBar.min = 0
        self.ids.progressBar.max = self.rem
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"

        self.buttonsEnabled()
        self.remainingText = 'Remaining duplicates: '
        return self.filenames

    def size_duplicates(self, filesizes):
        """Find files with the same filesize

        filesizes: dictionary of filesizes
        all_duplicates: list of duplicate files"""

        # Create an empty list of all duplicate files
        self.all_duplicates = []
        for size in filesizes:
            duplicates = filesizes[size]

            # If there is more than one file, add the files to the list
            # all_duplicates
            if len(duplicates) > 1:
                self.all_duplicates.append(duplicates)
        self.ids.remaining.text = 'Remaining duplicates: ' + str(len(self.all_duplicates))
        # self.ids.allImages.disabled = False
        # self.ids.searchBtn.disabled = False
        return self.all_duplicates

    def name_duplicates(self, filenames):
        """Find files with the same filesize

        filenames: dictionary of filesizes
        all_names_duplicates: list of duplicate files"""

        # Create an empty list of all duplicate files
        self.all_names_duplicates = []
        for name in filenames:
            duplicates = filenames[name]

            # If there is more than one file, add the files to the list
            # all_duplicates
            if len(duplicates) > 1:
                self.all_names_duplicates.append(duplicates)
        self.ids.remaining.text = 'Remaining duplicates: ' + \
            str(len(self.all_names_duplicates))
        # self.ids.allImages.disabled = False
        # self.ids.searchBtn.disabled = False
        return self.all_names_duplicates

    def calc_hash(self, matches):
        # matches = hash_duplicates
        """Calculate hash for a single list of duplicate files

        filehash: dictionary with hashes as keys and list of files with that hash
        matches: a list of files that are the same size
        hash as values"""

        # Create a default dictionary where the default value is an empty list
        self.filehash = defaultdict(list)
        a = len(self.matches)
        b = 0
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = a
        self.ids.progressBar.value = 0

        for file in matches:
            # Open a file that doesnt contain text, but rawbytes
            try:
                with open(file, 'rb') as f:

                    # Read the contents of the file and compute hash
                    h = xxhash.xxh64(f.read()).hexdigest()

                    # Add the hash and the file to the directory
                    self.filehash[str(h)].append(file)
                    self.ids.loading.text = str(a)+' : '+file
                    self.ids.progressBar.value = b
                    b += 1
                    prc = (b*100)/self.abc
                    self.ids.percent.text = "{:.2f} %".format(prc)
                    a -= 1

            except:
                a -= 1
                continue

        self.ids.loading.text = str(len(matches))+' files searched.'

        self.ids.progressBar.min = 0
        self.ids.progressBar.max = 1
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"
        self.load_files()
        return self.filehash

    def hash_loop(self, filehash):
        """Loop through list of all size duplicates and compute hashes for them

        filehash: list of duplicate files
        h: list of dictionaries containing files with the same hash value"""

        # Create an empty list for hashes
        self.h = []

        # For each list of duplicate files, calculate hashes
        for name in filehash:

            duplicates = filehash[name]
            if len(duplicates) > 1:
                self.h.append(duplicates)
        return self.h

    def src(self):
        """ Button 'Size' """
        if self.dirname == '' or self.moved_dirname == '':
            self.errorPopup()
            return
        else:
            self.buttonsDisabled()
            self.disable5buttons()
            self.empty_lists()
            self.ids.remainingItems.text = ' Items in the list: 0 '
            self.walk(self.dirname)  # REMOVE ON PRODUCTION
            self.find_matches(self.files)  # self.matches
            th3 = threading.Thread(target=self.comp_filesizes, args=[self.matches, ])
            th3.daemon = True
            th3.start()

    def src_name(self):
        """ Button 'Name' """
        if self.dirname == '' or self.moved_dirname == '':
            self.errorPopup()
            return
        else:
            self.buttonsDisabled()
            self.disable5buttons()
            self.empty_lists()
            self.ids.remainingItems.text = ' Items in the list: 0 '
            self.walk(self.dirname)  # REMOVE ON PRODUCTION
            self.find_matches(self.files)  # -> self.matches
            th5 = threading.Thread(
                target=self.comp_filenames, args=[self.matches, ])
            th5.daemon = True
            th5.start()

    def src_hash(self):
        """ Button 'Hash' """
        if self.dirname == '' or self.moved_dirname == '':
            self.errorPopup()
            return
        else:
            self.buttonsDisabled()
            self.disable5buttons()
            self.empty_lists()
            self.ids.remainingItems.text = ' Items in the list: 0 '
            self.walk(self.dirname)  # REMOVE ON PRODUCTION
            self.find_matches(self.files)  # -> self.matches
            self.abc = len(self.matches)
            th3 = threading.Thread(target=self.calc_hash,
                                   args=[self.matches, ])
            th3.daemon = True
            th3.start()

    def src_color(self):
        """ Button 'Color' """
        if self.dirname == '' or self.moved_dirname == '':
            self.errorPopup()
            return
        else:
            self.buttonsDisabled()
            self.disable5buttons()
            self.empty_lists()
            self.walk(self.dirname)  # REMOVE ON PRODUCTION
            self.find_matches(self.files)  # -> self.matches
            self.abc = len(self.matches)
            self.ids.remainingItems.text = ' Items in the list: 0 '
            th3 = threading.Thread(target = self.calc_color, args=[self.matches, ])
            th3.daemon = True
            th3.start()

    def calc_color(self, matches):
        a = len(self.matches)
        b = 1
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = a
        self.ids.progressBar.value = 0
        self.colors = defaultdict(list)
        try:
            for match in matches:
                img = Img.open(match)
                meanImg = ImageStat.Stat(img).mean
                self.colors[str(meanImg)].append(match)
                self.ids.loading.text = str(a)+' : '+match
                self.ids.progressBar.value = b
                b += 1
                prc = (b*100)/self.abc
                self.ids.percent.text = "{:.2f} %".format(prc)
                a -= 1
        except:
            pass

        self.ids.loading.text = str(len(matches))+' files searched.'
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = 1
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"
        self.loadColors()

    def loadColors(self):
        self.meanColor(self.colors)  # -> self.colorList
        self.abc = len(self.colorList)
        self.rem = len(self.colorList)
        self.ids.itm.text = 'Duplicates found: '+str(self.abc)
        self.ids.remaining.text = self.remainingText + str(self.abc)
        self.dupli = ()
        self.dupli = iter(self.colorList)
        self.addButtonsDisabledEnabled(self.abc)
        self.buttonsEnabled()
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = self.rem
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"

    def meanColor(self, lst):
        self.colorList = []

        # For each list of duplicate files, calculate hashes
        for color in lst:
            duplicates = lst[color]
            if len(duplicates) > 1:
                self.colorList.append(duplicates)
                
        return self.colorList

    def load_files(self):
        """Loads after calc_hash"""
        self.hash_loop(self.filehash)  # -> self.h
        self.abc = len(self.h)
        self.rem = len(self.h)
        self.ids.itm.text = 'Duplicates found: '+str(self.abc)
        self.ids.remaining.text = self.remainingText + str(self.abc)
        self.dupli = ()
        self.dupli = iter(self.h)
        self.addButtonsDisabledEnabled(self.abc)
        self.buttonsEnabled()
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = self.rem
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"

    def allImages(self):
        """ Show all images (button)"""
        if self.dirname == '' or self.moved_dirname == '':
            self.errorPopup()
            return
        else:
            self.ids.rv.data = []
            self.walk(self.dirname)
            self.dupli_name = []
            for i in self.files:
                end = i.split('.')[-1].lower()
                if end in self.types:
                    self.dupli_name.append([i])
            self.rem = len(self.dupli_name)
            self.abc = len(self.dupli_name)
            self.addButtonsDisabledEnabled(self.abc)
            self.dupli = iter(self.dupli_name)
            self.no = 0
            self.ids.progressBar.min = 0
            self.ids.progressBar.max = len(self.dupli_name)
            self.ids.progressBar.value = 0
            self.ids.percent.text = "0.00 %"
            self.ids.loading.text = str(len(self.dupli_name))+" images found."
            self.remainingText = 'Remaining images: '
            self.ids.remainingItems.text = ' Items in the list: 0 '
            self.ids.remaining.text = self.remainingText + str(len(self.dupli_name))

    def move_file(self, instance, pth):
        """Move item and close row"""
        indx = None
        a = pth.split('\\')[-1]  # only the file
        b = pth.split('\\')[-1].split('.')
        c = '.'.join(b[:-1])  # file without extension
        try:
            if os.path.exists(self.moved_dirname+'\\'+a) == True:
                d = c+'_0'+str(self.temp_files)+'.'+b[-1]
                shutil.move(pth, self.moved_dirname+'\\'+d)
                for i in range(len(self.ids.rv.data)):
                    if pth == self.ids.rv.data[i]['txt']:
                        indx = i
                self.ids.rv.data.pop(indx)
                self.temp_files += 1
            else:
                for i in range(len(self.ids.rv.data)):
                    if pth == self.ids.rv.data[i]['txt']:
                        indx = i
                self.ids.rv.data.pop(indx)
                shutil.move(pth, self.moved_dirname+'\\'+a)
            self.ids.remainingItems.text = 'Items in the list: ' + str(len(self.ids.rv.data)) +' '
        except:
            popup = Popup(title='Error', content=Label(
                text='CAN`T MOVE FILE.Check properties!'), size_hint=(None, None), size=(400, 200))
            popup.open()
            return

    def closeRow(self, instance, pth):
        """Close row without moving items"""
        indx = None
        for i in range(len(self.ids.rv.data)):
            if pth == self.ids.rv.data[i]['txt']:
                indx = i
        self.ids.rv.data.pop(indx)
        self.ids.remainingItems.text = 'Items in the list: ' + str(len(self.ids.rv.data)) +' '

    def open_dir(self, instance, dr):
        """ 'Open Folder' from the row, opens directory where the file is"""
        try:
            os.startfile(dr)
        except:
            pass

    def search(self, val):
        """Search button"""
        if self.dirname == '' or self.moved_dirname == '':
            self.errorPopup()
            return
        self.clearWidgets()
        self.rem = 0
        self.walk(self.dirname)
        self.searched = []
        for i in self.files:
            a = i.split('\\')[-1]
            if val.lower() in a.lower():
                self.searched.append([i])

        self.abc = len(self.searched)
        self.rem = len(self.searched)
        self.no = 0
        self.dupli = iter(self.searched)
        self.ids.progressBar.min = 0
        self.ids.progressBar.max = self.abc
        self.ids.progressBar.value = 0
        self.ids.percent.text = "0.00 %"
        self.ids.loading.text = str(len(self.searched)) +" files found."
        self.ids.itm.text = ''
        self.remainingText = 'Files remaining: '
        self.ids.remaining.text = self.remainingText + str(len(self.searched))
        self.addButtonsDisabledEnabled(self.rem)

    def errorPopup(self):
        """Popup in case a folder is not open or valid"""
        self.errorPop = Popup(title='Check folders', content=Label(
            text='Select SOURCE and DESTINATION folders'), size_hint=(None, None), size=(400, 200))
        self.errorPop.open()

    def sameFolderPopup(self):
        """Popup in case source and destination folders are the same"""
        self.sameFolderPop = Popup(title='Check folders', content=Label(
            text='SOURCE and DESTINATION cannot be the same.'), size_hint=(None, None), size=(400, 200))
        self.sameFolderPop.open()

    def clearWidgets(self):
        """Clear the screen (recycleview)"""
        self.ids.rv.data = []
        self.ids.remainingItems.text=' Items in the list: 0 '

    def empty_lists(self):
        """Clear the lists and dicts"""
        # self.files=[]
        self.abc = 0
        self.rem = 0
        self.no = 0
        self.ids.remainingItems.text = ''
        self.ids.itm.text = ''
        self.ids.remaining.text = ''
        self.ids.rv.data = []
        self.matches = []
        self.filesizes = []
        self.filenames = []
        self.all_duplicates = []
        self.all_names_duplicates = []
        self.filehash = []
        self.h = []

    def disable5buttons(self):
        """Disable buttons from 1 to 100 and All"""
        self.ids.addBtn1.disabled = True
        self.ids.addBtn2.disabled = True
        self.ids.addBtn5.disabled = True
        self.ids.addBtn10.disabled = True
        self.ids.addBtn50.disabled = True
        self.ids.addBtn100.disabled = True
        self.ids.addAll.disabled = True

    def buttonsEnabled(self):
        """Enable basic buttons"""
        self.ids.find_duplicates.disabled = False
        self.ids.find_duplicates1.disabled = False
        self.ids.find_duplicates2.disabled = False
        self.ids.find_duplicates3.disabled = False
        self.ids.allImages.disabled = False
        self.ids.searchBtn.disabled = False
        self.ids.allImages.disabled = False
        self.ids.searchBtn.disabled = False
        self.ids.clr_widgets.disabled = False
        self.ids.sourceBtn.disabled = False
        self.ids.destinationBtn.disabled = False

    def buttonsDisabled(self):
        """Disable basic buttons"""
        self.ids.find_duplicates.disabled = True
        self.ids.find_duplicates1.disabled = True
        self.ids.find_duplicates2.disabled = True
        self.ids.find_duplicates3.disabled = True
        self.ids.allImages.disabled = True
        self.ids.searchBtn.disabled = True
        self.ids.allImages.disabled = True
        self.ids.searchBtn.disabled = True
        self.ids.clr_widgets.disabled = True
        self.ids.sourceBtn.disabled = True
        self.ids.destinationBtn.disabled = True

    def addButtonsDisabledEnabled(self, lst):
        """Activate buttons 1-100 depending of the length of the list of elements"""
        if lst <= 0:
            self.ids.addBtn1.disabled = True
            self.ids.addBtn2.disabled = True
            self.ids.addBtn5.disabled = True
            self.ids.addBtn10.disabled = True
            self.ids.addBtn50.disabled = True
            self.ids.addBtn100.disabled = True
            self.ids.addAll.disabled = True
        elif lst <= 2:
            self.ids.addBtn1.disabled = False
            self.ids.addBtn2.disabled = True
            self.ids.addBtn5.disabled = True
            self.ids.addBtn10.disabled = True
            self.ids.addBtn50.disabled = True
            self.ids.addBtn100.disabled = True
            self.ids.addAll.disabled = False
        elif lst <= 5:
            self.ids.addBtn1.disabled = False
            self.ids.addBtn2.disabled = False
            self.ids.addBtn5.disabled = True
            self.ids.addBtn10.disabled = True
            self.ids.addBtn50.disabled = True
            self.ids.addBtn100.disabled = True
            self.ids.addAll.disabled = False
        elif lst <= 10:
            self.ids.addBtn1.disabled = False
            self.ids.addBtn2.disabled = False
            self.ids.addBtn5.disabled = False
            self.ids.addBtn10.disabled = True
            self.ids.addBtn50.disabled = True
            self.ids.addBtn100.disabled = True
            self.ids.addAll.disabled = False
        elif lst <= 50:
            self.ids.addBtn1.disabled = False
            self.ids.addBtn2.disabled = False
            self.ids.addBtn5.disabled = False
            self.ids.addBtn10.disabled = False
            self.ids.addBtn50.disabled = True
            self.ids.addBtn100.disabled = True
            self.ids.addAll.disabled = False
        elif lst <= 100:
            self.ids.addBtn1.disabled = False
            self.ids.addBtn2.disabled = False
            self.ids.addBtn5.disabled = False
            self.ids.addBtn10.disabled = False
            self.ids.addBtn50.disabled = False
            self.ids.addBtn100.disabled = True
            self.ids.addAll.disabled = False
        elif lst > 100:
            self.ids.addBtn1.disabled = False
            self.ids.addBtn2.disabled = False
            self.ids.addBtn5.disabled = False
            self.ids.addBtn10.disabled = False
            self.ids.addBtn50.disabled = False
            self.ids.addBtn100.disabled = False
            self.ids.addAll.disabled = False

